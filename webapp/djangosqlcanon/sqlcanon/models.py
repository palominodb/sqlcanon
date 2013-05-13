"""Sqlcanon models."""

from __future__ import unicode_literals

from django.db import models

import sqlcanon.utils as utils


class StatementData(models.Model):
    """Contains information about a SQL statement.

    Attributes:

        dt: Date and Time of this model, usually comes from the input
            log files

        statement: The actual statement.

        server_id: Server ID.

        hostname: Hostname.

        schema: Schema name.

        canonicalized_statement: Canonical form of the statement.

        canonicalized_statement_hash: Hash of the canonical form of
            the statement.

        query_time: Recorded query time.

        lock_time: Recorded lock time.

        rows_sent: Recorded rows_sent.

        rows_examined: Recorded rows examined.

        rows_affected: Recorded rows affected.

        rows_read: Recorded rows read.

        bytes_sent: Recorded bytes sent.

        sequence_id: In round-robin storage logic, this is used to
            determine the next row to be used for storage.

        created_at: Date and time this object was created.

        updated_at: Date and time this object was last updated.
    """

    dt = models.DateTimeField(null=True, blank=True)
    statement = models.TextField(blank=True)
    server_id = models.IntegerField(null=True, blank=True)
    hostname = models.CharField(max_length=256, blank=True, null=True)
    schema = models.CharField(max_length=256, blank=True, null=True)
    canonicalized_statement = models.TextField(blank=True)
    canonicalized_statement_hash = models.IntegerField(
        null=True, blank=True)
    canonicalized_statement_hostname_hash = models.IntegerField(
        null=True, blank=True)

    query_time = models.FloatField(null=True, blank=True)
    lock_time = models.FloatField(null=True, blank=True)
    rows_sent = models.IntegerField(null=True, blank=True)
    rows_examined = models.IntegerField(null=True, blank=True)
    rows_affected = models.IntegerField(null=True, blank=True)
    rows_read = models.IntegerField(null=True, blank=True)
    bytes_sent = models.IntegerField(null=True, blank=True)
    tmp_tables = models.IntegerField(null=True, blank=True)
    tmp_disk_tables = models.IntegerField(null=True, blank=True)
    tmp_table_sizes = models.IntegerField(null=True, blank=True)

    sequence_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = u'statements'

    def __unicode__(self):
        return u'<StatementData %s>' % (
            utils.generate_model_instance_unicode_string(self),)

    def canonicalized_statement_hash_hex_str(self):
        """Returns canonicalized statement hash as hex string."""

        return utils.int_to_hex_str(self.canonicalized_statement_hash)

    def canonicalized_statement_hostname_hash_hex_str(self):
        """Returns canonicalized statement-hostname hash as hex string."""

        return utils.int_to_hex_str(
            self.canonicalized_statement_hostname_hash)


class ExplainedStatement(models.Model):
    """Info about statement where EXPLAIN operation has been performed.

    Note:
        Most fields in here are copied from StatementData.
        StatementData is currently stored in a round robin fashion so
        we can't just FK to it.

    Attributes:
        dt: Statement date and time.

        statement: The EXPLAINed statement.

        server_id: Server ID.

        Hostname: Hostname.

        canonicalized_statement: Canonical form of the statement.

        canonicalized_statement_hash = Hash of the canonical form of
            the statement.

        canonicalized_statement_hash = Hash of
            canonicalized statement-hostname.

        db: Schema name.

        created_at: The date and time the object was created.

        updated_at: The date and time the object was last updated.
    """
    dt = models.DateTimeField(null=True, blank=True)
    statement = models.TextField(blank=True)
    server_id = models.IntegerField(null=True, blank=True)
    hostname = models.CharField(max_length=256, blank=True, null=True)
    canonicalized_statement = models.TextField(blank=True)
    canonicalized_statement_hash = models.IntegerField(
        null=True, blank=True)
    canonicalized_statement_hostname_hash = models.IntegerField(
        null=True, blank=True)
    db = models.TextField(blank=True)

    created_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = u'explained_statements'

    def __unicode__(self):
        return u'<ExplainedStatement %s>' % (
            utils.generate_model_instance_unicode_string(self),)

    def canonicalized_statement_hash_hex_str(self):
        """Returns the hex string version of canonicalized_statement_hash."""
        return utils.int_to_hex_str(self.canonicalized_statement_hash)

    def canonicalized_statement_hostname_hash_hex_str(self):
        """Returns the hex string version of canonicalized_statement-hostname hash."""
        return utils.int_to_hex_str(
            self.canonicalized_statement_hostname_hash)


class ExplainResult(models.Model):
    """Represents a single row of EXPLAIN results.

    Attributes:

        explained_statement: Instance of ExplainedStatement where this
            object is associated with.

        select_id: EXPLAIN select_id column.

        select_type: EXPLAIN select_type column.

        table: EXPLAIN table column.

        type: EXPLAIN type column.

        possible_keys: EXPLAIN possible_keys column.

        key: EXPLAIN key column.

        key_len: EXPLAIN key_len column.

        ref: EXPLAIN ref column.

        rows: EXPLAIN rows column.

        extra: EXPLAIN extra column.

        created_at: The date and time the object was created.

        updated_at: The date and time the object was last updated.
    """

    explained_statement = models.ForeignKey(
        ExplainedStatement, db_column='explained_statement_id',
        related_name='explain_results',
        null=True, blank=True)

    select_id = models.IntegerField(null=True, blank=True)
    select_type = models.TextField(blank=True)
    table = models.TextField(blank=True)
    type = models.TextField(blank=True)
    possible_keys = models.TextField(blank=True)
    key = models.TextField(blank=True)
    key_len = models.IntegerField(null=True, blank=True)
    ref = models.TextField(blank=True)
    rows = models.IntegerField(null=True, blank=True)
    extra = models.TextField(blank=True)

    created_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = u'explain_results'

    def __unicode__(self):
        return u'<ExplainResult %s>' % (
            utils.generate_model_instance_unicode_string(self),)



