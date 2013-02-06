from datetime import datetime

class QueryLister:
    def __init__(self):
        """
        Initialization.
        """

        # list item will be a list in the following format:
        #     [dt, query, canonicalized_query, count]
        #
        #     dt:
        #         query date/time
        #     query:
        #         query
        #     canonicalized_query:
        #         canonicalized query,
        #     count:
        #         for a given window, number of instances of queries, that are similar to this query, found
        self.query_list = []


    def append_query(self, query, canonicalized_query, dt=None):
        """
        Appends query to list.
        """

        if dt is None:
            dt = datetime.now()

        # order of items on list is expected to be ordered by datetime in ascending order
        # do not allow violation of this rule
        if self.query_list:
            assert self.query_list[len(self.query_list) - 1][0] <= dt

        self.query_list.append([dt, query, canonicalized_query, 0])

    def get_list(self, dt_start, dt_end, remove_older_items=True):
        """
        Returns part of the list (filtered by datetime start and end) with updated count field.

        dt_start
            filter: datetime start
        dt_end
            filter: datetime end
        remove_older_items:
            exclude items whose datetime is < dt_start
        """

        assert dt_start <= dt_end

        # Store counts here.
        # This will look like:
        #     counts = {
        #         'select * from foo': {
        #             'count': 3,
        #             'indeces': [0, 1, 4]   # indeces of list items who have the same canonicalized_query
        #         },
        #         'insert into people(name, email) values (n)': {
        #             'count': 2,
        #             'indeces': [2, 3]
        #         }
        #     }
        counts = {}

        # store the indeces of the items that will be included in
        # the final result
        list_indeces = []

        # calculate counts
        for index, query_list_item in enumerate(self.query_list):
            dt, query, canonicalized_query, count = query_list_item
            if(dt_start <= dt <= dt_end):
                list_indeces.append(index)
                if counts.has_key(canonicalized_query):
                    counts[canonicalized_query]['count'] += 1
                else:
                    counts[canonicalized_query] = dict(count=1, indeces=[])

                # remember indeces of queries that have the same canonicalized query
                counts[canonicalized_query]['indeces'].append(index)

        # reflect counts in result (query_list subset)
        for canonicalized_query, info in counts.iteritems():
            count = info['count']
            indeces = info['indeces']
            for index in indeces:
                self.query_list[index][3] = count

        if list_indeces:
            result = self.query_list[min(list_indeces):max(list_indeces) + 1]
        else:
            result = []

        if remove_older_items:
            if list_indeces and min(list_indeces) < len(self.query_list):
                self.query_list = self.query_list[min(list_indeces):]
            else:
                self.query_list = []

        return result
