from django.db import models

import canonicalizer.utils as app_utils


class StatementData(models.Model):
    dt = models.DateTimeField(null=True, blank=True)
    statement = models.TextField(blank=True)

    server_id = models.IntegerField(null=True, blank=True)

    canonicalized_statement = models.TextField(blank=True)
    canonicalized_statement_hash = models.IntegerField(null=True, blank=True)
    canonicalized_statement_hostname_hash = models.IntegerField(null=True, blank=True)
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

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now_add=True, auto_now=True)

    # 2013-03-22 Elmer: added the following fields
    hostname = models.CharField(max_length=256, blank=True, null=True)
    schema = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = u'statements'

    def __unicode__(self):
        return (
            u'<StatementData '
            u'id={0}, '
            u'dt={1}, '
            u'statement={2}, '
            u'server_id={3}, '
            u'canonicalized_statement={4}, '
            u'canonicalized_statement_hash={5}, '
            u'canonicalized_statement_hostname_hash={6}, '
            u'query_time={7}, '
            u'lock_time={8}, '
            u'rows_sent={9}, '
            u'rows_examined={10}, '
            u'rows_affected={11}, '
            u'rows_read={12}, '
            u'bytes_sent={13}, '
            u'tmp_tables={14}, '
            u'tmp_disk_tables={15}, '
            u'tmp_table_sizes={16}, '
            u'hostname={17}, '
            u'schema={18}, '
            u'sequence_id={19}, '
            u'created_at={20}, '
            u'updated_at={21}'
            u'>').format(
                self.id,
                self.dt,
                self.statement,
                self.server_id,
                self.canonicalized_statement,
                self.canonicalized_statement_hash,
                self.canonicalized_statement_hostname_hash,
                self.query_time,
                self.lock_time,
                self.rows_sent,
                self.rows_examined,
                self.rows_affected,
                self.rows_read,
                self.bytes_sent,
                self.tmp_tables,
                self.tmp_disk_tables,
                self.tmp_table_sizes,
                self.sequence_id,
                self.hostname,
                self.schema,
                self.created_at,
                self.updated_at)

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
    dt = models.DateTimeField(null=True, blank=True)
    statement = models.TextField(blank=True)

    # was hostname
    server_id = models.IntegerField(null=True, blank=True)

    canonicalized_statement = models.TextField(blank=True)
    canonicalized_statement_hash = models.IntegerField(null=True, blank=True)
    canonicalized_statement_hostname_hash = models.IntegerField(
        null=True, blank=True)
    db = models.TextField(blank=True)

    # new
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    # new
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = u'explained_statements'

    def __unicode__(self):
        return (
            u'<ExplainedStatement '
            u'id={0}, '
            u'dt={1}, '
            u'statement={2}, '
            u'server_id={3}, '
            u'canonicalized_statement={4}, '
            u'canonicalized_statement_hash={5}, '
            u'canonicalized_statement_hostname_hash={6}, '
            u'db={7}, '
            u'created_at={8}, '
            u'udated_at={9}'
            u'>').format(
                self.id,
                self.dt,
                self.statement,
                self.server_id,
                self.canonicalized_statement,
                self.canonicalized_statement_hash,
                self.canonicalized_statement_hostname_hash,
                self.db,
                self.created_at,
                self.updated_at)

    def canonicalized_statement_hash_hex_str(self):
        return app_utils.int_to_hex_str(self.canonicalized_statement_hash)

    def canonicalized_statement_hostname_hash_hex_str(self):
        return app_utils.int_to_hex_str(
            self.canonicalized_statement_hostname_hash)


class ExplainResult(models.Model):
    #explained_statement_id = models.IntegerField(null=True, blank=True)
    explained_statement = models.ForeignKey(
        ExplainedStatement, db_column='explained_statement_id',
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

    # new
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    # new
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = u'explain_results'

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
            u'extra={11}, '
            u'created_at={12}, '
            u'updated_at={13}'
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
                self.extra,
                self.created_at,
                self.updated_at)




