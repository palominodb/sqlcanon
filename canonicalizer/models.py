from django.db import models

class CanonicalizedStatement(models.Model):
    statement = models.TextField(unique=True, default='')
    hash = models.IntegerField(unique=True, default=0)
    instances = models.IntegerField(default=0)

    def __unicode__(self):
        return u'<CanonicalizedStatement id={0}, statement={1}, hash={2}, counts={3}>'.format(
            self.id, self.statement, self.hash, self.instances
        )

class CapturedStatement(models.Model):
    dt = models.DateTimeField()
    statement = models.TextField()
    canonicalized_statement = models.TextField()
    canonicalized_statement_hash = models.IntegerField()

    def __unicode__(self):
        return u'<CapturedStatement id={0}, dt={1}, statement={2}>'.format(
            self.id, self.dt, self.statement
        )