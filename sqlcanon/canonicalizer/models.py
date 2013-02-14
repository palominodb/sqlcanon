from django.db import models
from canonicalizer.lib.utils import int_to_hex_str

class CanonicalizedStatement(models.Model):
    statement = models.TextField(unique=True, default='')
    hash = models.IntegerField(unique=True, default=0)
    instances = models.IntegerField(default=0)

    def __unicode__(self):
        return u'<CanonicalizedStatement id={0}, statement={1}, hash={2}, counts={3}>'.format(
            self.id, self.statement, self.hash, self.instances
        )

    def hash_as_hex_str(self):
        return int_to_hex_str(self.hash)

class CapturedStatement(models.Model):
    dt = models.DateTimeField(db_index=True)
    statement = models.TextField()
    canonicalized_statement = models.TextField()
    canonicalized_statement_hash = models.IntegerField()
    sequence_id = models.IntegerField(unique=True)
    last_updated = models.DateTimeField(db_index=True, auto_now_add=True, auto_now=True)

    def __unicode__(self):
        return u'<CapturedStatement id={0}, dt={1}, statement={2}>'.format(
            self.id, self.dt, self.statement
        )