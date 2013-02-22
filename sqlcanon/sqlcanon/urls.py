from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

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

    url(r'^canonicalizer/', include('canonicalizer.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
