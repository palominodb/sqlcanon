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
            ('statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('statement_hostname_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('instances', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('canonicalizer', ['CanonicalizedStatement'])

        # Adding model 'CapturedStatement'
        db.create_table('canonicalizer_capturedstatement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('canonicalized_statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('canonicalized_statement_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('statement_hostname_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('sequence_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, db_index=True, blank=True)),
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
            'hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instances': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'canonicalizer.capturedstatement': {
            'Meta': {'object_name': 'CapturedStatement'},
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'sequence_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        }
    }

    complete_apps = ['canonicalizer']