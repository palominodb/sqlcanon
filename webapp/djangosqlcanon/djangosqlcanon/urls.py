from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from tastypie.api import Api

from sqlcanon.api import resources

v1_api = Api(api_name='v1')
v1_api.register(resources.StatementDataResource())
v1_api.register(resources.ExplainedStatementResource())
v1_api.register(resources.ExplainResultResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'djangosqlcanon.views.home', name='home'),
    # url(r'^djangosqlcanon/', include('djangosqlcanon.foo.urls')),

    url(r'^$', 'sqlcanon.views.home', name='home'),

    url(r'^sqlcanon/', include('sqlcanon.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/', include(v1_api.urls)),
)
