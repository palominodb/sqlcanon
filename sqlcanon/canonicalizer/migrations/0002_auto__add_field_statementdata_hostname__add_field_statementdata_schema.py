# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'StatementData.hostname'
        db.add_column(u'statements', 'hostname',
                      self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True),
                      keep_default=False)

        # Adding field 'StatementData.schema'
        db.add_column(u'statements', 'schema',
                      self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'StatementData.hostname'
        db.delete_column(u'statements', 'hostname')

        # Deleting field 'StatementData.schema'
        db.delete_column(u'statements', 'schema')


    models = {
        'canonicalizer.explainedstatement': {
            'Meta': {'object_name': 'ExplainedStatement', 'db_table': "u'explained_statements'"},
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'canonicalized_statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'db': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'server_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        'canonicalizer.explainresult': {
            'Meta': {'object_name': 'ExplainResult', 'db_table': "u'explain_results'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'explained_statement': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['canonicalizer.ExplainedStatement']", 'null': 'True', 'db_column': "'explained_statement_id'", 'blank': 'True'}),
            'extra': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'key_len': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'possible_keys': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ref': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'rows': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'select_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'select_type': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'table': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        'canonicalizer.statementdata': {
            'Meta': {'object_name': 'StatementData', 'db_table': "u'statements'"},
            'bytes_sent': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'canonicalized_statement': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'canonicalized_statement_hash': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'canonicalized_statement_hostname_hash': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_time': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'query_time': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'rows_affected': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rows_examined': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rows_read': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rows_sent': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'schema': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'sequence_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'server_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'statement': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tmp_disk_tables': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tmp_table_sizes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tmp_tables': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['canonicalizer']