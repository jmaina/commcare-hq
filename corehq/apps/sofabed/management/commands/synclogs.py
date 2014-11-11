import datetime
import json
from django.core.management.base import NoArgsCommand
from casexml.apps.phone.models import SyncLog
from corehq.apps.sofabed.models import SyncLog as SyncLogSQL
from sys import stdin

class PaginateViewLogHandler:
    @staticmethod
    def view_starting(db, view_name, kwargs, total_emitted):
        print 'Fetching rows {}-{} from couch'.format(
            total_emitted,
            total_emitted + kwargs['limit'] - 1)
        print 'First doc: ', kwargs.get('startkey_docid')

    @staticmethod
    def view_ending(db, view_name, kwargs, total_emitted, time):
        print 'View call took {}'.format(time)
        print 'Last doc: ', kwargs.get('startkey_docid')


def paginate_view(db, view_name, chunk_size,
                  log_handler=PaginateViewLogHandler(), **kwargs):
    """
    intended as a more performant drop-in replacement for

        iter(db.view(view_name, **kwargs))

    intended specifically to be more performant when dealing with
    large numbers of rows

    Note: If the contents of the couch view do not change over the duration of
    the paginate_view call, this is guaranteed to have the same results
    as a direct view call. If the view is updated, however,
    paginate_views may skip docs that were added/updated during this period
    or may include docs that were removed/updated during this period.
    For this reason, it's best to use this with views that update infrequently
    or that are sorted by date modified and/or add-only,
    or when exactness is not a strict requirement

    chunk_size is how many docs to fetch per request to couchdb

    """
    if kwargs.get('reduce', True):
        raise ValueError('paginate_view must be called with reduce=False')

    if 'limit' in kwargs:
        raise ValueError('paginate_view cannot be called with limit')

    if 'skip' in kwargs:
        raise ValueError('paginate_view cannot be called with skip')

    kwargs['limit'] = chunk_size
    total_emitted = 0
    len_results = -1
    while len_results:
        log_handler.view_starting(db, view_name, kwargs, total_emitted)
        start_time = datetime.datetime.utcnow()
        results = db.view(view_name, **kwargs)
        len_results = len(results)

        for result in results:
            yield result

        if len_results:
            kwargs['startkey'] = result['key']
            kwargs['startkey_docid'] = result['id']
            kwargs['skip'] = 1

        total_emitted += len_results
        log_handler.view_ending(db, view_name, kwargs, total_emitted,
                                datetime.datetime.utcnow() - start_time)


class Command(NoArgsCommand):
    def handle(self, *args, **options):
        db = SyncLog.get_db()

        start = db.get("7a2c965642e3b48a3591b28af0ee6ae2")

        key = [start['_id'], start['date'], start['last_seq']]
        print key
        results = paginate_view(
            db, 'phone/sync_logs_by_user',
            chunk_size=1000,
            reduce=False,
            include_docs=True,
            startkey=key,
            startkey_docid=start['_id']
        )

        for r in results:
            doc = r['doc']
            if doc.get('duration', None):
                sl = SyncLog.wrap(doc)

                print sl
                SyncLogSQL(
                    id=sl._id,
                    date=sl.date,
                    user_id=sl.user_id,
                    previous_log_id=sl.previous_log_id,
                    last_seq=sl.last_seq,
                    duration=sl.duration,
                    cases_on_phone=len(sl.cases_on_phone),
                    dependent_cases_on_phone=len(sl.dependent_cases_on_phone),
                    owner_ids_on_phone=len(sl.owner_ids_on_phone)
                ).save()
