import datetime
import logging
from django.db.models import Count, Sum, Avg, Max
from django.utils import timezone

from canonicalizer import models, utils

log = logging.getLogger(__name__)


def get_top_queries(n, column, filter_dict):
    """
    Returns top 'n' queries based on 'column'.

    n
        - top number of rows to return

    column
        - the column to be used in ordering
            choices:
                count
                total_query_time
                total_lock_time
                total_rows_read
                avg_query_time
                avg_lock_time
                avg_rows_read

    filter_dict
        - should be a dict with the following keys:

            hostname (optional)
                - filter result by hostname
                - use "__none__" to filter results whose hostname is None
            schema (optional)
                - filter result by schema
                - use "__none__" to filter results whose schema is None
    """

    hostname = filter_dict.get('hostname', None)
    schema = filter_dict.get('schema', None)

    flds = []
    if hostname:
        flds.append('hostname')
    if schema:
        flds.append('schema')
    flds.extend(['canonicalized_statement', 'canonicalized_statement_hash'])
    qs = models.StatementData.objects.values(*flds)

    #
    # apply filters if present
    #
    if hostname and hostname == '__none__':
        qs = qs.filter(hostname=None)
    elif hostname and hostname != '__all__':
        qs = qs.filter(hostname=hostname)
    if schema and schema == '__none__':
        qs = qs.filter(schema=None)
    elif schema and schema != '__all__':
        qs = qs.filter(schema=schema)

    qs = qs.annotate(
        count=Count('id'),
        total_query_time=Sum('query_time'),
        total_lock_time=Sum('lock_time'),
        total_rows_read=Sum('rows_read'),
        avg_query_time=Avg('query_time'),
        avg_lock_time=Avg('lock_time'),
        avg_rows_read=Avg('rows_read')
    ).order_by('-%s' % (column,))[:n]

    return qs


def get_last_statements(last_minutes):
    """
    Returns statements found in last 'last_minutes' minutes.

    Return format:
    [
        {
            "statement_data": obj,      # StatementData instance
            "count": 0                  # number of instances
        },
        ...
    ]
    """

    dt = timezone.now()
    dt_start = dt - datetime.timedelta(minutes=last_minutes)
    statement_data_qs = (
        models.StatementData.objects
        .filter(dt__gte=dt_start, dt__lte=dt)
        .values(
            'canonicalized_statement',
            'server_id',
            'canonicalized_statement_hostname_hash',
            'canonicalized_statement_hash',
            'statement')
        .annotate(Max('dt'), Count('dt')).order_by('dt__max'))

    # calculate counts
    counts = {}
    for statement_data in statement_data_qs:
        canonicalized_statement_hostname_hash = (
            statement_data['canonicalized_statement_hostname_hash'])
        if canonicalized_statement_hostname_hash in counts:
            counts[canonicalized_statement_hostname_hash] += (
                statement_data['dt__count'])
        else:
            counts[canonicalized_statement_hostname_hash] = (
                statement_data['dt__count'])

    objects = []
    for statement_data in statement_data_qs:
        canonicalized_statement_hostname_hash = (
            statement_data['canonicalized_statement_hostname_hash'])
        count = counts.get(canonicalized_statement_hostname_hash, 1)

        objects.append(
            dict(
                statement_data=statement_data,
                count=count
            )
        )
    return objects