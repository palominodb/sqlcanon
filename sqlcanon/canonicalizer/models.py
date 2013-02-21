from django.db import models
# FIXME:
from canonicalizer.lib.utils import int_to_hex_str

import canonicalizer.utils as app_utils


class CanonicalizedStatement(models.Model):
    statement = models.TextField(default='')
    hostname = models.CharField(max_length=1024, default='')
    hash = models.IntegerField(default=0, db_index=True)
    statement_hostname_hash = models.IntegerField(default=0, db_index=True)
    instances = models.IntegerField(default=0, db_index=True)

    class Meta:
        unique_together = (('hostname', 'statement'),)

    def __unicode__(self):
        return u'<CanonicalizedStatement id={0}, statement={1}, hostname={2}, hash={3}, counts={4}>'.format(
            self.id, self.statement, self.hostname, self.statement_hostname_hash, self.instances
        )

    def hash_as_hex_str(self):
        return int_to_hex_str(self.hash)

    def statement_hostname_hash_as_hex_str(self):
        return int_to_hex_str(self.statement_hostname_hash)


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