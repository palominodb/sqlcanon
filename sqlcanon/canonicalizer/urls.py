from django.conf.urls import patterns, url

urlpatterns = patterns('canonicalizer.views',
    url(r'^sparkline/(?P<data>.+)/$',
        'sparkline',
        name='canonicalizer_sparkline'),
)
