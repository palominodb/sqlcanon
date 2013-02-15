from django.db import models
from canonicalizer.lib.utils import int_to_hex_str

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

class CapturedStatement(models.Model):
    dt = models.DateTimeField(db_index=True)
    statement = models.TextField(default='')
    hostname = models.CharField(max_length=1024, default='')
    canonicalized_statement = models.TextField(default='')
    canonicalized_statement_hash = models.IntegerField(default=0, db_index=True)
    statement_hostname_hash = models.IntegerField(default=0, db_index=True)
    sequence_id = models.IntegerField(unique=True)
    last_updated = models.DateTimeField(db_index=True, auto_now_add=True, auto_now=True)

    def __unicode__(self):
        return u'<CapturedStatement id={0}, dt={1}, statement={2}, hostname={3}>'.format(
            self.id, self.dt, self.statement, self.hostname
        )

    def canonicalized_statement_hash_as_hex_str(self):
        return int_to_hex_str(self.canonicalized_statement_hash)

    def statement_hostname_hash_as_hex_str(self):
        return int_to_hex_str(self.statement_hostname_hash)