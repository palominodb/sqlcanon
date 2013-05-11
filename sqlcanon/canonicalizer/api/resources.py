import json
import logging
from django.conf.urls import url
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

from canonicalizer import models
from canonicalizer.businesslogic import core as core_logic

log = logging.getLogger(__name__)


class ExplainedStatementResource(ModelResource):
    class Meta:
        queryset = models.ExplainedStatement.objects.all()
        resource_name = 'explained_statement'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {
            'id': ALL,
        }


class ExplainResultResource(ModelResource):
    explained_statement = fields.ForeignKey(
        ExplainedStatementResource, 'explained_statement')

    class Meta:
        queryset = models.ExplainResult.objects.all()
        resource_name = 'explain_result'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {
            'explained_statement': ALL_WITH_RELATIONS,
        }


class StatementDataResource(ModelResource):
    class Meta:
        queryset = models.StatementData.objects.all()
        resource_name = 'statement_data'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

    def prepend_urls(self):
        return [
            # get top queries
            url(
                r'^(?P<resource_name>%s)/get_top_queries/$' % (
                    self._meta.resource_name,),
                self.wrap_view('get_top_queries'),
                name='api_get_top_queries'),

            # get last statements
            url(
                r'^(?P<resource_name>%s)/get_last_statements/$' % (
                    self._meta.resource_name,),
                self.wrap_view('get_last_statements'),
                name='api_get_last_statements'),
        ]

    def get_last_statements(self, request, **kwargs):
        """
        Returns last statements found in last 'n' minutes.

        request.raw_post_data should be a JSON object in the form:
        {
            "n": 1,     # minutes
        }
        """

        # allow post only
        self.method_check(request, allowed=['post'])

        self.is_authenticated(request)

        data = {}
        try:
            post = json.loads(request.raw_post_data)
            n = int(post['n'])
            data['objects'] = core_logic.get_last_statements(n)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(data=data, request=request)
        return self.create_response(request, bundle)

    def get_top_queries(self, request, **kwargs):
        """
        Returns top 'n' queries.

        request.raw_post_data should be a JSON object in the form:
        {
            "n": 1,             # top limit
            "column": "",       # column to be used in ordering
            "hostname": ""      # hostname to be used in filtering
            "schema": ""        # schema to be used in filtering
        }
        """

        # allow posts only
        self.method_check(request, allowed=['post'])

        self.is_authenticated(request)

        data = {}
        try:
            post = json.loads(request.raw_post_data)
            n = int(post['n'])
            column = post['column']
            hostname = post.get('hostname', None)
            schema = post.get('schema', None)
            filter_dict = {}
            if hostname:
                filter_dict['hostname'] = hostname
            if schema:
                filter_dict['schema'] = schema
            qs = core_logic.get_top_queries(n, column, filter_dict)
            objects = []
            for obj in qs:
                objects.append(obj)
            data['objects'] = objects
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(data=data, request=request)
        return self.create_response(request, bundle)

