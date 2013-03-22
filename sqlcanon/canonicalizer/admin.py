from django.contrib import admin

import canonicalizer.models as app_models


class StatementDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'dt', 'statement', 'hostname', 'server_id',
        'canonicalized_statement', 'canonicalized_statement_hash_hex_str',
        'canonicalized_statement_hostname_hash_hex_str',
        'query_time', 'lock_time', 'rows_sent', 'rows_examined',
        'rows_affected', 'rows_read', 'bytes_sent',
        'tmp_tables', 'tmp_disk_tables', 'tmp_table_sizes', 'schema',
        'sequence_id',
        'created_at', 'updated_at')


class ExplainResultInline(admin.TabularInline):
    model = app_models.ExplainResult


class ExplainedStatementAdmin(admin.ModelAdmin):
    inlines = [ExplainResultInline,]
    list_display = (
        'id', 'dt', 'statement', 'server_id', 'canonicalized_statement',
        'canonicalized_statement_hash_hex_str',
        'canonicalized_statement_hostname_hash_hex_str',
        'db',
        'created_at', 'updated_at')


admin.site.register(app_models.StatementData, StatementDataAdmin)
admin.site.register(app_models.ExplainedStatement, ExplainedStatementAdmin)
