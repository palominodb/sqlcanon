from datetime import datetime
import pprint

from django.utils import timezone

import mmh3

PP = pprint.PrettyPrinter(indent=4)

class QueryLister:
    def __init__(self):
        """
        Initialization.
        """

        # list item will be a list in the following format:
        #     [dt, statement, canonicalized_query, hash, count]
        #
        #     dt:
        #         statement date/time
        #     statement:
        #         statement
        #     canonicalized_statement:
        #         canonicalized statement
        #     hash:
        #         hash of canonicalized_statement
        #     count:
        #         for a given window, number of instances of statements, that are similar to this statement, found
        self.statement_list = []


    def append_statement(self, statement, canonicalized_statement, dt=None):
        """
        Appends statement to list.
        """

        if not dt:
            dt = timezone.now()

        # order of items on list is expected to be ordered by datetime in ascending order
        # do not allow violation of this rule
        if self.statement_list:
            assert self.statement_list[len(self.statement_list) - 1][0] <= dt

        self.statement_list.append([dt, statement, canonicalized_statement, mmh3.hash(canonicalized_statement), 0])

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
        #             'indices': [0, 1, 4]   # indices of list items who have the same canonicalized statement
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
        for index, statement_list_item in enumerate(self.statement_list):
            dt, query, canonicalized_query, hash, count = statement_list_item

            if(dt_start <= dt <= dt_end):
                list_indices.append(index)
                if counts.has_key(hash):
                    counts[hash]['count'] += 1
                else:
                    counts[hash] = dict(count=1, indices=[])

                # remember indices of queries that have the same canonicalized statement
                counts[hash]['indices'].append(index)

        # reflect counts in result (statement_list subset)
        for hash, info in counts.iteritems():
            count = info['count']
            indices = info['indices']
            for index in indices:
                self.statement_list[index][4] = count

        if list_indices:
            result = self.statement_list[min(list_indices):max(list_indices) + 1]
        else:
            result = []

        if remove_older_items:
            if list_indices and min(list_indices) < len(self.statement_list):
                self.statement_list = self.statement_list[min(list_indices):]
            else:
                self.statement_list = []

        return result
