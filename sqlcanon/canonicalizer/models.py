from django.db import models

import canonicalizer.utils as app_utils


class StatementData(models.Model):
    dt = models.DateTimeField(db_index=True)
    statement = models.TextField(default='')
    hostname = models.CharField(max_length=1024, default='')
    canonicalized_statement = models.TextField(default='')
    canonicalized_statement_hash = models.IntegerField(
        default=0, db_index=True)

    # canonicalized_statement+hostname hash
    canonicalized_statement_hostname_hash = models.IntegerField(
        default=0, db_index=True)

    query_time = models.FloatField(blank=True, null=True, default=None)
    lock_time = models.FloatField(blank=True, null=True, default=None)
    rows_sent = models.FloatField(blank=True, null=True, default=None)
    rows_examined = models.FloatField(blank=True, null=True, default=None)
    sequence_id = models.IntegerField(unique=True)
    last_updated = models.DateTimeField(
        db_index=True, auto_now_add=True, auto_now=True)

    def __unicode__(self):
        return (
            u'<StatementData '
            u'id={0}, '
            u'dt={1}, '
            u'statement={2}, '
            u'hostname={3}, '
            u'canonicalized_statement={4}, '
            u'canonicalized_statement_hash={5}, '
            u'canonicalized_statement_hostname_hash={6}, '
            u'query_time={7}, '
            u'lock_time={8}, '
            u'rows_sent={9}, '
            u'rows_examined={10}, '
            u'sequence_id={11}, '
            u'last_updated={12}'
            u'>').format(
                self.id,
                self.dt,
                self.statement,
                self.hostname,
                self.canonicalized_statement,
                self.canonicalized_statement_hash,
                self.canonicalized_statement_hostname_hash,
                self.query_time,
                self.lock_time,
                self.rows_sent,
                self.rows_examined,
                self.sequence_id,
                self.last_updated)

    def canonicalized_statement_hash_hex_str(self):
        return app_utils.int_to_hex_str(self.canonicalized_statement_hash)

    def canonicalized_statement_hostname_hash_hex_str(self):
        return app_utils.int_to_hex_str(
            self.canonicalized_statement_hostname_hash)


class ExplainedStatement(models.Model):
    """Explained Statement

    Note:
        Most fields in here are copied from StatementData.
        StatementData is currently stored as RRD so we can't just FK to it.
    """

    dt = models.DateTimeField()
    statement = models.TextField(default='')
    hostname = models.CharField(max_length=1024, default='')
    canonicalized_statement = models.TextField(default='')
    canonicalized_statement_hash = models.IntegerField(
        default=0, db_index=True)
    canonicalized_statement_hostname_hash = models.IntegerField(
        default=0, db_index=True)
    db = models.CharField(max_length=128, blank=True, null=True, default=None)

    def __unicode__(self):
        return (
            u'<ExplainedStatement '
            u'id={0}, '
            u'dt={1}, '
            u'statement={2}, '
            u'hostname={3}, '
            u'canonicalized_statement={4}, '
            u'canonicalized_statement_hash={5}, '
            u'canonicalized_statement_hostname_hash={6}, '
            u'db={7}'
            u'>').format(
                self.id,
                self.dt,
                self.statement,
                self.hostname,
                self.canonicalized_statement,
                self.canonicalized_statement_hash,
                self.canonicalized_statement_hostname_hash,
                self.db)

    def canonicalized_statement_hash_hex_str(self):
        return app_utils.int_to_hex_str(self.canonicalized_statement_hash)

    def canonicalized_statement_hostname_hash_hex_str(self):
        return app_utils.int_to_hex_str(
            self.canonicalized_statement_hostname_hash)


class ExplainResult(models.Model):
    explained_statement = models.ForeignKey(ExplainedStatement)
    select_id = models.IntegerField(blank=True, null=True, default=None)
    select_type = models.CharField(
        max_length=128, blank=True, null=True, default=None)
    table = models.CharField(
        max_length=128, blank=True, null=True, default=None)
    type = models.CharField(
        max_length=128, blank=True, null=True, default=None)
    possible_keys = models.CharField(
        max_length=1024, blank=True, null=True, default=None)
    key = models.CharField(
        max_length=1024, blank=True, null=True, default=None)
    key_len = models.IntegerField(blank=True, null=True, default=None)
    ref = models.CharField(
        max_length=1024, blank=True, null=True, default=None)
    rows = models.IntegerField(blank=True, null=True, default=None)
    extra = models.TextField(blank=True, null=True, default=None)

    def __unicode__(self):
        return (
            u'<ExplainResult '
            u'id={0}, '
            u'explained_statement_id={1}, '
            u'select_id={2}, '
            u'select_type={3}, '
            u'table={4}, '
            u'type={5}, '
            u'possible_keys={6}, '
            u'key={7}, '
            u'key_len={8}, '
            u'ref={9}, '
            u'rows={10}, '
            u'extra={11}'
            u'>').format(
                self.id,
                self.explained_statement.id,
                self.select_id,
                self.select_type,
                self.table,
                self.type,
                self.possible_keys,
                self.key,
                self.key_len,
                self.ref,
                self.rows,
                self.extra)

