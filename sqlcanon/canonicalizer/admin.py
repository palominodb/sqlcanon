from django.contrib import admin

import canonicalizer.models as app_models


class StatementDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'dt', 'statement', 'hostname',
        'canonicalized_statement', 'canonicalized_statement_hash_hex_str',
        'canonicalized_statement_hostname_hash_hex_str',
        'query_time', 'lock_time', 'rows_sent', 'rows_examined',
        'sequence_id', 'last_updated')


class ExplainResultInline(admin.StackedInline):
    model = app_models.ExplainResult


class ExplainedStatementAdmin(admin.ModelAdmin):
    inlines = [ExplainResultInline,]
    list_display = (
        'id', 'dt', 'statement', 'hostname', 'canonicalized_statement',
        'canonicalized_statement_hash_hex_str',
        'canonicalized_statement_hostname_hash_hex_str',
        'db')


admin.site.register(app_models.StatementData, StatementDataAdmin)
admin.site.register(app_models.ExplainedStatement, ExplainedStatementAdmin)