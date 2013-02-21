"""This file contains app business rules."""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import canonicalizer.models as app_models

def save_statement_data(
        dt,
        statement, hostname,
        canonicalized_statement, canonicalized_statement_hash,
        canonicalized_statement_hostname_hash,
        query_time=None,
        lock_time=None,
        rows_sent=None,
        rows_examined=None):
    """Saves statement data.

    Statement data are stored as RRD.
    """

    qs = app_models.StatementData.objects.order_by('-last_updated')[:1]
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
        statement_data.dt = dt
        statement_data.statement = statement
        statement_data.hostname = hostname
        statement_data.canonicalized_statement = canonicalized_statement
        statement_data.canonicalized_statement_hash = (
            canonicalized_statement_hash)
        statement_data.canonicalized_statement_hostname_hash = (
            canonicalized_statement_hostname_hash)
        statement_data.query_time = query_time
        statement_data.lock_time = lock_time
        statement_data.rows_sent = rows_sent
        statement_data.rows_examined = rows_examined
        statement_data.save()
    except ObjectDoesNotExist:
        app_models.StatementData.objects.create(
            dt=dt,
            statement=statement,
            hostname=hostname,
            canonicalized_statement=canonicalized_statement,
            canonicalized_statement_hash=canonicalized_statement_hash,
            canonicalized_statement_hostname_hash=
                canonicalized_statement_hostname_hash,
            query_time=query_time,
            lock_time=lock_time,
            rows_sent=rows_sent,
            rows_examined=rows_examined,
            sequence_id=sequence_id,
        )