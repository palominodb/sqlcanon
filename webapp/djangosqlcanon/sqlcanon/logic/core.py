"""Sqlcanon core logic."""

import datetime
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum, Avg, Max
from django.utils import timezone

from sqlcanon import models
from sqlcanon import utils

log = logging.getLogger(__name__)


def get_top_queries(n, column, filter_dict):
    """Returns top 'n' queries based on 'column'.

    Args:

        n: Top number of rows to return.

        column: The column to be used in ordering

            choices:

                count

                total_query_time

                total_lock_time

                total_rows_read

                avg_query_time

                avg_lock_time

                avg_rows_read

        filter_dict: should be a dict with the following keys:

            hostname (optional): Filter result by hostname.
                Use "__none__" to filter results whose hostname is None.

            schema (optional): Filter result by schema.
                Use "__none__" to filter results whose schema is None.

    Returns:

        A StatementData queryset containing the following fields:

            hostname, if used in filtering

            schema, if used in filtering

            canonicalized_statement

            canonicalized_statement_hash

        The queryset also contains the following annotations:

            count: Group row count.

            total_query_time: Sum of query_time.

            total_lock_time: Sum of lock_time.

            total_rows_read: Sum of rows_read.

            avg_query_time: Avg of query_time.

            avg_lock_time: Avg of lock_time.

            avg_rows_read: Avg of rows_read.
    """

    hostname = filter_dict.get('hostname', None)
    schema = filter_dict.get('schema', None)

    flds = []
    if hostname:
        flds.append('hostname')
    if schema:
        flds.append('schema')
    flds.extend(
        ['canonicalized_statement', 'canonicalized_statement_hash'])
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
    """Returns statements found in last 'last_minutes' minutes.

    Args:

        last_minutes: period length starting from current time going
            backwards.

    Returns:

        A list of dictionaries in the following format:

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


def save_explained_statement(**kwargs):
    """Saves explain results."""

    statement_data_id = kwargs.get('statement_data_id')
    explain_rows = kwargs.get('explain_rows')
    db = kwargs.get('db', '')
    server_id = kwargs.get('server_id')

    statement_data = models.StatementData.objects.get(
        pk=statement_data_id)
    explained_statement = models.ExplainedStatement.objects.create(
        dt=statement_data.dt,
        statement=statement_data.statement,
        server_id=statement_data.server_id,
        canonicalized_statement=statement_data.canonicalized_statement,
        canonicalized_statement_hash=statement_data.canonicalized_statement_hash,
        canonicalized_statement_hostname_hash=statement_data.canonicalized_statement_hostname_hash,
        db=db)

    for explain_row in explain_rows:
        # fix null texts
        flds = [
            'select_type', 'table', 'type', 'possible_keys', 'key',
            'ref', 'extra']
        for k in flds:
            if k in explain_row:
                if not explain_row[k]:
                    explain_row[k] = ''
        models.ExplainResult.objects.create(
            explained_statement=explained_statement, **explain_row)

    return explained_statement


def save_statement_data(**kwargs):
    """Saves statement data.

    Statement data are stored in round-robin fashion.
    """

    qs = models.StatementData.objects.order_by(
        '-updated_at', '-sequence_id')[:1]
    statement_data = None
    if qs:
        statement_data = qs[0]
    if statement_data:
        sequence_id = ((statement_data.sequence_id + 1) %
            settings.CAPTURED_STATEMENT_ROW_LIMIT)
    else:
        sequence_id = 1

    #
    # update if row exist, otherwise, create it
    #
    field_value_map = dict([(k, v) for k, v in kwargs.iteritems() if v])
    try:
        statement_data = models.StatementData.objects.get(
            sequence_id=sequence_id)
        for k, v in field_value_map.iteritems():
            setattr(statement_data, k, v)
        statement_data.save()
    except ObjectDoesNotExist:
        field_value_map.update(sequence_id=sequence_id)
        statement_data = models.StatementData.objects.create(
            **field_value_map)

    return statement_data
