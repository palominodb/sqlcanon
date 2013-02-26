# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StatementData'
        db.create_table('canonicalizer_statementdata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('canonicalized_statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('canonicalized_statement_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('canonicalized_statement_hostname_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('query_time', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('lock_time', self.gf('django.db.models.fields.FloatField')(default=None, null=True, blank=True)),
            ('rows_sent', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('rows_examined', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('rows_affected', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('rows_read', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('bytes_sent', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('tmp_tables', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('tmp_disk_tables', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('tmp_table_sizes', self.gf('django.db.models.fields.DecimalField')(default=None, null=True, max_digits=24, decimal_places=0, blank=True)),
            ('sequence_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('canonicalizer', ['StatementData'])

        # Adding model 'ExplainedStatement'
        db.create_table('canonicalizer_explainedstatement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('canonicalized_statement', self.gf('django.db.models.fields.TextField')(default='')),
            ('canonicalized_statement_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('canonicalized_statement_hostname_hash', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('db', self.gf('django.db.models.fields.CharField')(default=None, max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal('canonicalizer', ['ExplainedStatement'])

        # Adding model 'ExplainResult'
        db.create_table('canonicalizer_explainresult', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('explained_statement', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['canonicalizer.ExplainedStatement'])),
            ('select_id', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('select_type', self.gf('django.db.models.fields.CharField')(default=None, max_length=128, null=True, blank=True)),
            ('table', self.gf('django.db.models.fields.CharField')(default=None, max_length=128, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default=None, max_length=128, null=True, blank=True)),
            ('possible_keys', self.gf('django.db.models.fields.CharField')(default=None, max_length=1024, null=True, blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(default=None, max_length=1024, null=True, blank=True)),
            ('key_len', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('ref', self.gf('django.db.models.fields.CharField')(default=None, max_length=1024, null=True, blank=True)),
            ('rows', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('extra', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('canonicalizer', ['ExplainResult'])


    def backwards(self, orm):
        # Deleting model 'StatementData'
        db.delete_table('canonicalizer_statementdata')

        # Deleting model 'ExplainedStatement'
        db.delete_table('canonicalizer_explainedstatement')

        # Deleting model 'ExplainResult'
        db.delete_table('canonicalizer_explainresult')


    models = {
        'canonicalizer.explainedstatement': {
            'Meta': {'object_name': 'ExplainedStatement'},
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'canonicalized_statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'db': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''"})
        },
        'canonicalizer.explainresult': {
            'Meta': {'object_name': 'ExplainResult'},
            'explained_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['canonicalizer.ExplainedStatement']"}),
            'extra': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'key_len': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'possible_keys': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'ref': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'rows': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'select_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'select_type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'table': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        'canonicalizer.statementdata': {
            'Meta': {'object_name': 'StatementData'},
            'bytes_sent': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'canonicalized_statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'lock_time': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'query_time': ('django.db.models.fields.FloatField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'rows_affected': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'rows_examined': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'rows_read': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'rows_sent': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'sequence_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'tmp_disk_tables': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'tmp_table_sizes': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'}),
            'tmp_tables': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '24', 'decimal_places': '0', 'blank': 'True'})
        }
    }

    complete_apps = ['canonicalizer']