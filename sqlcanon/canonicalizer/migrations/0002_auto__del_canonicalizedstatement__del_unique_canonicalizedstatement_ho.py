# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'CanonicalizedStatement', fields ['hostname', 'statement']
        db.delete_unique('canonicalizer_canonicalizedstatement', ['hostname', 'statement'])

        # Deleting model 'CanonicalizedStatement'
        db.delete_table('canonicalizer_canonicalizedstatement')


    def backwards(self, orm):
        # Adding model 'CanonicalizedStatement'
        db.create_table('canonicalizer_canonicalizedstatement', (
            ('hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('instances', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('statement_hostname_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('canonicalizer', ['CanonicalizedStatement'])

        # Adding unique constraint on 'CanonicalizedStatement', fields ['hostname', 'statement']
        db.create_unique('canonicalizer_canonicalizedstatement', ['hostname', 'statement'])


    models = {
        'canonicalizer.statementdata': {
            'Meta': {'object_name': 'StatementData'},
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'canonicalized_statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'lock_time': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'query_time': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'rows_examined': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'rows_sent': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'sequence_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''"})
        }
    }

    complete_apps = ['canonicalizer']