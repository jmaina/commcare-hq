class ReportDataSource(object):
    slug = ''

    def __init__(self, config=None):
        """
        :param config: dictionary containing configuration for this data source.
         e.g.
         {
            'startdate': date(2013, 1, 1),
            'enddate': date(2013, 1, 31),
            'user_id': 'abc'
         }
        """
        self.configure(config, check_conflicts=True)

    def configure(self, config, check_conflicts=False):
        """
        :param config: dictionary containing configuration for this data source.
         Overrides any config supplied to the constructor.
        """
        self.config = config or {}
        if hasattr(self, 'filters'):
            for name, filter in self.filters:
                if check_conflicts and hasattr(self, name):
                    raise Exception("Conflicting property name: {}".format(name))

                setattr(self, name, self.config.get(name, None))

        return config

    def slugs(self):
        """
        Intention: Override

        :return: A list of available slugs.
        """
        return []

    def get_data(self, slugs=None):
        """
        Intention: Override

        :param slugs: List of slugs to return for each row. Return all values if slugs = None or [].
        :return: A list of dictionaries mapping slugs to values.

        e.g.
        [{'village': 'Mazu', 'births': 30, 'deaths': 28},{...}]
        """

        return {}

    def get_total_records(self):
        return 0