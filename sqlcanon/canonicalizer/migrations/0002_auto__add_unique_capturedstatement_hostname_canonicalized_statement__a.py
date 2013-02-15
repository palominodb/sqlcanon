# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'CapturedStatement', fields ['hostname', 'canonicalized_statement']
        db.create_unique('canonicalizer_capturedstatement', ['hostname', 'canonicalized_statement'])

        # Adding unique constraint on 'CanonicalizedStatement', fields ['hostname', 'statement']
        db.create_unique('canonicalizer_canonicalizedstatement', ['hostname', 'statement'])


    def backwards(self, orm):
        # Removing unique constraint on 'CanonicalizedStatement', fields ['hostname', 'statement']
        db.delete_unique('canonicalizer_canonicalizedstatement', ['hostname', 'statement'])

        # Removing unique constraint on 'CapturedStatement', fields ['hostname', 'canonicalized_statement']
        db.delete_unique('canonicalizer_capturedstatement', ['hostname', 'canonicalized_statement'])


    models = {
        'canonicalizer.canonicalizedstatement': {
            'Meta': {'unique_together': "(('hostname', 'statement'),)", 'object_name': 'CanonicalizedStatement'},
            'hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instances': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'canonicalizer.capturedstatement': {
            'Meta': {'unique_together': "(('hostname', 'canonicalized_statement'),)", 'object_name': 'CapturedStatement'},
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