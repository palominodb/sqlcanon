from django.contrib import admin
from canonicalizer.models import CapturedStatement, CanonicalizedStatement

class CanonicalizedStatementAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'hash', 'instances')

class CapturedStatementAdmin(admin.ModelAdmin):
    list_display = ('id', 'dt', 'statement', 'canonicalized_statement',
                    'canonicalized_statement_hash', 'sequence_id', 'last_updated')

admin.site.register(CanonicalizedStatement, CanonicalizedStatementAdmin)
admin.site.register(CapturedStatement, CapturedStatementAdmin)