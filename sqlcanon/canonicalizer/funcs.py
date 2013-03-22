"""This file contains app business rules."""
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import canonicalizer.models as app_models


LOGGER = logging.getLogger(__name__)


def save_explained_statement(**kwargs):
    """Saves explain results."""

    statement_data_id = kwargs.get('statement_data_id')
    explain_rows = kwargs.get('explain_rows')
    db = kwargs.get('db', '')
    server_id = kwargs.get('server_id')

    statement_data = app_models.StatementData.objects.get(pk=statement_data_id)
    explained_statement = app_models.ExplainedStatement.objects.create(
        dt=statement_data.dt,
        statement=statement_data.statement,
        server_id=statement_data.server_id,
        canonicalized_statement=statement_data.canonicalized_statement,
        canonicalized_statement_hash=statement_data.canonicalized_statement_hash,
        canonicalized_statement_hostname_hash=statement_data.canonicalized_statement_hostname_hash,
        db=db)

    for explain_row in explain_rows:
        # fix null texts
        for k in ['select_type', 'table', 'type', 'possible_keys', 'key', 'ref', 'extra']:
            if k in explain_row:
                if not explain_row[k]:
                    explain_row[k] = ''
        app_models.ExplainResult.objects.create(explained_statement=explained_statement, **explain_row)

    return explained_statement


def save_statement_data(**kwargs):
    """Saves statement data.

    Statement data are stored as RRD.
    """

    qs = app_models.StatementData.objects.order_by('-updated_at', '-sequence_id')[:1]
    statement_data = None
    if qs:
        statement_data = qs[0]
    if statement_data:
        sequence_id = ((statement_data.sequence_id + 1) %
                       settings.CAPTURED_STATEMENT_ROW_LIMIT)
    else:
        sequence_id = 1

    try:
        statement_data = app_models.StatementData.objects.get(
            sequence_id=sequence_id)
        statement_data.dt = kwargs.get('dt')
        statement_data.statement = kwargs.get('statement')
        statement_data.server_id = kwargs.get('server_id')
        statement_data.canonicalized_statement = kwargs.get('canonicalized_statement')
        statement_data.canonicalized_statement_hash = kwargs.get('canonicalized_statement_hash')
        statement_data.canonicalized_statement_hostname_hash = kwargs.get('canonicalized_statement_hostname_hash')
        statement_data.query_time = kwargs.get('query_time')
        statement_data.lock_time = kwargs.get('lock_time')
        statement_data.rows_sent = kwargs.get('rows_sent')
        statement_data.rows_examined = kwargs.get('rows_examined')
        statement_data.rows_affected = kwargs.get('rows_affected')
        statement_data.rows_read = kwargs.get('rows_read')
        statement_data.bytes_sent = kwargs.get('bytes_sent')
        statement_data.tmp_tables = kwargs.get('tmp_tables')
        statement_data.tmp_disk_tables = kwargs.get('tmp_disk_tables')
        statement_data.tmp_table_sizes = kwargs.get('tmp_table_sizes')
        statement_data.hostname = kwargs.get('hostname')
        statement_data.schema = kwargs.get('schema')
        statement_data.save()

    except ObjectDoesNotExist:
        statement_data = app_models.StatementData.objects.create(
            dt=kwargs.get('dt'),
            statement=kwargs.get('statement'),
            server_id=kwargs.get('server_id'),
            canonicalized_statement=kwargs.get('canonicalized_statement'),
            canonicalized_statement_hash=kwargs.get('canonicalized_statement_hash'),
            canonicalized_statement_hostname_hash=kwargs.get('canonicalized_statement_hostname_hash'),
            query_time=kwargs.get('query_time'),
            lock_time=kwargs.get('lock_time'),
            rows_sent=kwargs.get('rows_sent'),
            rows_examined=kwargs.get('rows_examined'),
            rows_affected=kwargs.get('rows_affected'),
            rows_read=kwargs.get('rows_read'),
            bytes_sent=kwargs.get('bytes_sent'),
            tmp_tables=kwargs.get('tmp_tables'),
            tmp_disk_tables=kwargs.get('tmp_disk_tables'),
            tmp_table_sizes=kwargs.get('tmp_table_sizes'),
            hostname=kwargs.get('hostname'),
            schema=kwargs.get('schema'),
            sequence_id=sequence_id,
        )
    return statement_data
