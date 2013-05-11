from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from tastypie.api import Api

from canonicalizer.api import resources

v1_api = Api(api_name='v1')
v1_api.register(resources.StatementDataResource())
v1_api.register(resources.ExplainedStatementResource())
v1_api.register(resources.ExplainResultResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sqlcanon.views.home', name='home'),
    # url(r'^sqlcanon/', include('sqlcanon.foo.urls')),

    url(r'^$', 'canonicalizer.views.home', name='home'),

    url(
        r'^save-statement-data/',
        'canonicalizer.views.save_statement_data',
        name='save_statement_data'),

    url(
        r'^save-explained-statement/',
        'canonicalizer.views.save_explained_statement',
        name='save_explained_statement'),

    url(r'^last-statements/(?P<window_length>\d+)/',
        'canonicalizer.views.last_statements',
        name='last_statements'),

    url(r'^top-queries/(?P<n>\d+)/',
        'canonicalizer.views.top_queries',
        name='top_queries'),

    url(r'^explained-statements/',
        'canonicalizer.views.explained_statements',
        name='explained_statements'),

    url(r'^explain-results/(?P<id>\d+)/',
        'canonicalizer.views.explain_results',
        name='explain_results'),

    url(r'^canonicalizer/', include('canonicalizer.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/', include(v1_api.urls)),
)
