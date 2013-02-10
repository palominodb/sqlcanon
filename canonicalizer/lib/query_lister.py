from datetime import datetime
import pprint

import mmh3

PP = pprint.PrettyPrinter(indent=4)

class QueryLister:
    def __init__(self):
        """
        Initialization.
        """

        # list item will be a list in the following format:
        #     [dt, query, canonicalized_query, hash, count]
        #
        #     dt:
        #         query date/time
        #     query:
        #         query
        #     canonicalized_query:
        #         canonicalized query
        #     hash:
        #         hash of canonicalized_query
        #     count:
        #         for a given window, number of instances of queries, that are similar to this query, found
        self.query_list = []


    def append_query(self, query, canonicalized_query, dt=None):
        """
        Appends query to list.
        """

        if not dt: 
            dt = datetime.now()

        # order of items on list is expected to be ordered by datetime in ascending order
        # do not allow violation of this rule
        if self.query_list:
            assert self.query_list[len(self.query_list) - 1][0] <= dt

        self.query_list.append([dt, query, canonicalized_query, mmh3.hash(canonicalized_query), 0])

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
        #         1234: {  # hash
        #             'count': 3,
        #             'indices': [0, 1, 4]   # indices of list items who have the same canonicalized_query
        #         },
        #         5678: {
        #             'count': 2,
        #             'indices': [2, 3]
        #         }
        #     }
        counts = {}

        # store the indices of the items that will be included in
        # the final result
        list_indices = []

        # calculate counts
        for index, query_list_item in enumerate(self.query_list):
            dt, query, canonicalized_query, hash, count = query_list_item

            if(dt_start <= dt <= dt_end):
                list_indices.append(index)
                if counts.has_key(hash):
                    counts[hash]['count'] += 1
                else:
                    counts[hash] = dict(count=1, indices=[])

                # remember indices of queries that have the same canonicalized query
                counts[hash]['indices'].append(index)

        # reflect counts in result (query_list subset)
        for hash, info in counts.iteritems():
            count = info['count']
            indices = info['indices']
            for index in indices:
                self.query_list[index][4] = count

        if list_indices:
            result = self.query_list[min(list_indices):max(list_indices) + 1]
        else:
            result = []

        if remove_older_items:
            if list_indices and min(list_indices) < len(self.query_list):
                self.query_list = self.query_list[min(list_indices):]
            else:
                self.query_list = []

        return result