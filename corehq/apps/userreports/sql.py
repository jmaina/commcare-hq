import hashlib
import sqlalchemy
from django.conf import settings
from sqlalchemy.exc import IntegrityError
from dimagi.utils.decorators.memoized import memoized
from fluff.util import get_column_type

metadata = sqlalchemy.MetaData()


class IndicatorSqlAdapter(object):

    def __init__(self, engine, config):
        self.engine = engine
        self.config = config

    @memoized
    def get_table(self):
        return get_indicator_table(self.config)

    def rebuild_table(self):
        rebuild_table(self.engine, self.get_table())

    def drop_table(self):
        with self.engine.begin() as connection:
            self.get_table().drop(connection, checkfirst=True)

    def save(self, doc):
        indicator_rows = self.config.get_all_values(doc)
        if indicator_rows:
            table = self.get_table()
            for indicator_row in indicator_rows:
                with self.engine.begin() as connection:
                    # delete all existing rows for this doc to ensure we aren't left with stale data
                    delete = table.delete(table.c.doc_id == doc['_id'])
                    connection.execute(delete)
                    all_values = {i.column.id: i.value for i in indicator_row}
                    insert = table.insert().values(**all_values)
                    try:
                        connection.execute(insert)
                    except IntegrityError:
                        # Someone beat us to it. Concurrent inserts can happen
                        # when a doc is processed by the celery rebuild task
                        # at the same time as the pillow.
                        pass

    def delete(self, doc):
        table = self.get_table()
        with self.engine.begin() as connection:
            delete = table.delete(table.c.doc_id == doc['_id'])
            connection.execute(delete)


def get_indicator_table(indicator_config, custom_metadata=None):
    sql_columns = [column_to_sql(col) for col in indicator_config.get_columns()]
    table_name = get_table_name(indicator_config.domain, indicator_config.table_id)
    # todo: needed to add extend_existing=True to support multiple calls to this function for the same table.
    # is that valid?
    return sqlalchemy.Table(
        table_name,
        custom_metadata or metadata,
        extend_existing=True,
        *sql_columns
    )


def column_to_sql(column):
    return sqlalchemy.Column(
        column.id,
        get_column_type(column.datatype),
        nullable=column.is_nullable,
        primary_key=column.is_primary_key,
    )


def get_engine():
    return sqlalchemy.create_engine(settings.SQL_REPORTING_DATABASE_URL)


def rebuild_table(engine, table):
    with engine.begin() as connection:
        table.drop(connection, checkfirst=True)
        table.create(connection)
    engine.dispose()


def get_table_name(domain, table_id):
    def _hash(domain, table_id):
        return hashlib.sha1('{}_{}'.format(hashlib.sha1(domain).hexdigest(), table_id)).hexdigest()[:8]

    return 'config_report_{0}_{1}_{2}'.format(domain, table_id, _hash(domain, table_id))
