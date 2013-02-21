from django.contrib import admin
from canonicalizer.models import CanonicalizedStatement

import canonicalizer.models as app_models


class CanonicalizedStatementAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'hostname', 'hash_as_hex_str',
                    'statement_hostname_hash_as_hex_str', 'instances')


class StatementDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'dt', 'statement', 'hostname',
        'canonicalized_statement', 'canonicalized_statement_hash_hex_str',
        'canonicalized_statement_hostname_hash_hex_str',
        'query_time', 'lock_time', 'rows_sent', 'rows_examined',
        'sequence_id', 'last_updated')


admin.site.register(CanonicalizedStatement, CanonicalizedStatementAdmin)
admin.site.register(app_models.StatementData, StatementDataAdmin)