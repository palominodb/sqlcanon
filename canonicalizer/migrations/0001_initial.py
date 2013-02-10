# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CanonicalizedStatement'
        db.create_table('canonicalizer_canonicalizedstatement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('statement', self.gf('django.db.models.fields.TextField')(default='', unique=True)),
            ('hash', self.gf('django.db.models.fields.IntegerField')(default=0, unique=True)),
            ('instances', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('canonicalizer', ['CanonicalizedStatement'])

        # Adding model 'CapturedStatement'
        db.create_table('canonicalizer_capturedstatement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('statement', self.gf('django.db.models.fields.TextField')()),
            ('canonicalized_statement', self.gf('django.db.models.fields.TextField')()),
            ('canonicalized_statement_hash', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('canonicalizer', ['CapturedStatement'])


    def backwards(self, orm):
        # Deleting model 'CanonicalizedStatement'
        db.delete_table('canonicalizer_canonicalizedstatement')

        # Deleting model 'CapturedStatement'
        db.delete_table('canonicalizer_capturedstatement')


    models = {
        'canonicalizer.canonicalizedstatement': {
            'Meta': {'object_name': 'CanonicalizedStatement'},
            'hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instances': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''", 'unique': 'True'})
        },
        'canonicalizer.capturedstatement': {
            'Meta': {'object_name': 'CapturedStatement'},
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {}),
            'dt': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['canonicalizer']