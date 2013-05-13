"""Sqlcanon views."""

from __future__ import unicode_literals

import datetime
import decimal
import json
import logging
import pprint
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Avg, Count, Max, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from sqlcanon import forms
from sqlcanon import models
from sqlcanon import utils
from sqlcanon import spark
from sqlcanon.logic import core


log = logging.getLogger(__name__)


def explain_results(
        request, id, template='sqlcanon/explain_results.html'):
    """Shows explain results page."""

    id = int(id)
    explained_statement = models.ExplainedStatement.objects.get(pk=id)
    result = explained_statement.explain_results.all()
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def explained_statements(
        request, template='sqlcanon/explained_statements.html'):
    """Shows explained statements page."""

    stmts = models.ExplainedStatement.objects.all()
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@csrf_exempt
def save_explained_statement(request):
    """Saves explain data."""

    def post_vars(post):
        data = json.loads(post['data'])
        statement_data_id = int(data['statement_data_id'])
        explain_rows = json.loads(data['explain_rows'])
        db = data.get('db')
        server_id = data.get('server_id')
        if server_id:
            server_id = int(server_id)
        return dict(
            statement_data_id=statement_data_id,
            explain_rows=explain_rows,
            db=db,
            server_id=server_id)

    rv = {}
    try:
        if request.method == 'POST':
            log.debug(
                'request.POST:\n%s' % (pprint.pformat(request.POST),))
            post_vars_packed = post_vars(request.POST)
            explained_statement = core.save_explained_statement(
                **post_vars_packed)
        ret = json.dumps(rv)
    except Exception, e:
        log.exception('%s' % (e,))
        ret = json.dumps(dict(error='%s' % (e,)))
    return HttpResponse(ret, mimetype='application/json')


@csrf_exempt
def save_statement_data(request):
    """Saves statement data."""

    def get_post_vars(post):
        post_data = post['data']
        try:
            data = json.loads(post_data)
        except:
            log.error(
                ('Could not successfully convert the following data '
                'to JSON object: %s') % (post_data,))
            return None

        v = {}
        v['statement'] = data['statement']
        v['hostname'] = data['hostname']
        v['canonicalized_statement'] = data['canonicalized_statement']

        if 'canonicalized_statement_hash' in data and data[
                'canonicalized_statement_hash']:
            v['canonicalized_statement_hash'] = int(
                data['canonicalized_statement_hash'])

        if 'canonicalized_statement_hostname_hash' in data and data[
                'canonicalized_statement_hostname_hash']:
            v['canonicalized_statement_hostname_hash'] = int(
                data['canonicalized_statement_hostname_hash'])

        if 'query_time' in data and data['query_time']:
            v['query_time'] = float(data['query_time'])

        if 'lock_time' in data and data['lock_time']:
            v['lock_time'] = float(data['lock_time'])

        if 'rows_sent' in data and data['rows_sent']:
            v['rows_sent'] = int(data['rows_sent'])

        if 'rows_examined' in data and data['rows_examined']:
            v['rows_examined'] = int(data['rows_examined'])

        if 'rows_affected' in data and data['rows_affected']:
            v['rows_affected'] = int(data['rows_affected'])

        if 'rows_read' in data and data['rows_read']:
            v['rows_read'] = int(data['rows_read'])

        if 'bytes_sent' in data and data['bytes_sent']:
            v['bytes_sent'] = int(data['bytes_sent'])

        if 'tmp_tables' in data and data['tmp_tables']:
            v['tmp_tables'] = int(data['tmp_tables'])

        if 'tmp_disk_tables' in data and data['tmp_disk_tables']:
            v['tmp_disk_tables'] = int(data['tmp_disk_tables'])

        if 'tmp_table_sizes' in data and data['tmp_table_sizes']:
            v['tmp_table_sizes'] = int(data['tmp_table_sizes'])

        if 'server_id' in data:
            v['server_id'] = int(data['server_id'])

        if 'schema' in data and data['schema'] and data[
                'schema'].strip():
            v['schema'] = data['schema'].strip()

        if 'hostname' in data and data['hostname'] and data[
                'hostname'].strip():
            v['hostname'] = data['hostname'].strip()

        return v

    # store here the statements that needs to be EXPLAINed
    explain = []
    try:
        if request.method == 'POST':
            log.debug(
                'request.POST:\n%s' % (pprint.pformat(request.POST),))
            post_vars = get_post_vars(request.POST)
            if post_vars:
                post_vars['dt'] = timezone.now()

                statement = post_vars['statement']
                canonicalized_statement = post_vars[
                    'canonicalized_statement']
                canonicalized_statement_hostname_hash = post_vars.get(
                    'canonicalized_statement_hostname_hash')

                if canonicalized_statement:
                    is_select_statement = canonicalized_statement.startswith(
                        'SELECT ')
                else:
                    is_select_statement = False

                first_seen = False
                if is_select_statement:
                    count = (models.StatementData.objects.filter(
                        canonicalized_statement_hostname_hash=canonicalized_statement_hostname_hash)
                        .count())

                    # first_seen is set to True, if this is the first
                    # time we saw this statement
                    first_seen = not count

                    log.debug(
                        'is_select_statement=%s\nfirst_seen=%s' % (
                            is_select_statement, first_seen))

                statement_data = core.save_statement_data(
                    **post_vars)

                if first_seen:
                    explain_data = dict(
                        statement=statement,
                        statement_data_id=statement_data.id)
                    if 'schema' in post_vars and post_vars[
                            'schema'] and post_vars[
                            'schema'].strip():
                        explain_data['schema'] = post_vars['schema'].strip()
                    explain.append(explain_data)

        ret = json.dumps(dict(explain=explain))
    except Exception, e:
        log.exception('%s' % (e,))
        ret = json.dumps(dict(error='%s' % (e,)))
    return HttpResponse(ret, mimetype='application/json')


def last_statements(
        request, window_length,
        template='sqlcanon/last_statements.html'):

    try:
        window_length = int(window_length)
        dt = timezone.now()
        dt_start = dt - datetime.timedelta(minutes=window_length)
        statement_data_qs = (
            models.StatementData.objects
            .filter(dt__gte=dt_start, dt__lte=dt)
            .values(
                'canonicalized_statement',
                'server_id',
                'canonicalized_statement_hostname_hash',
                'canonicalized_statement_hash',
                'statement')
            .annotate(Max('dt'), Count('dt')).order_by('dt__max'))

        # calculate counts
        counts = {}
        for statement_data in statement_data_qs:
            canonicalized_statement_hostname_hash = statement_data[
                'canonicalized_statement_hostname_hash']
            if canonicalized_statement_hostname_hash in counts:
                counts[canonicalized_statement_hostname_hash] += (
                    statement_data['dt__count'])
            else:
                counts[canonicalized_statement_hostname_hash] = (
                    statement_data['dt__count'])

        statements = []
        for statement_data in statement_data_qs:
            canonicalized_statement_hostname_hash = statement_data[
                'canonicalized_statement_hostname_hash']
            count = counts.get(canonicalized_statement_hostname_hash, 1)
            sparkline_data_session_key = 'sparkline_data.%s' % (
                utils.int_to_hex_str(
                    canonicalized_statement_hostname_hash),)
            sparkline_data = request.session.get(
                sparkline_data_session_key, [])
            if sparkline_data:
                if sparkline_data[-1] != count:
                    # add new data only if it is different from the
                    # last data added
                    sparkline_data.append(count)
            else:
                sparkline_data.append(count)
            if len(sparkline_data) > settings.SPARKLINE_DATA_COUNT_LIMIT:
                # limit number of items in sparkline data
                sparkline_data = sparkline_data[
                    -settings.SPARKLINE_DATA_COUNT_LIMIT:len(
                        sparkline_data)]
            statements.append([
                statement_data,
                count,
                utils.int_to_hex_str(
                    canonicalized_statement_hostname_hash),
                ','.join([str(i) for i in sparkline_data])
            ])
            request.session[sparkline_data_session_key] = sparkline_data

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        log.exception('%s' % (e,))


def home(request, template='site/home.html'):
    try:
        # top queries form
        tqf = None

        # last statements form
        lsf = None

        count=Count('id'),
        total_query_time=Sum('query_time'),
        total_lock_time=Sum('lock_time'),
        total_rows_read=Sum('rows_read'),
        avg_query_time=Avg('query_time'),
        avg_lock_time=Avg('lock_time'),
        avg_rows_read=Avg('rows_read')
        column_choices = [
            ('count', 'Number of times seen'),
            ('total_query_time', 'Total query time'),
            ('total_lock_time', 'Total lock time'),
            ('total_rows_read', 'Total rows read'),
            ('avg_query_time', 'Avg query time'),
            ('avg_lock_time', 'Avg lock time'),
            ('avg_rows_read', 'Avg rows read')
        ]

        hostname_choices = [('__all__', '<All hostnames>')]
        qs = models.StatementData.objects.values('hostname').distinct()
        for r in qs:
            k = r['hostname']
            v = r['hostname']
            if not v:
                k = '__none__'
                v = '<No hostname>'
            hostname_choices.append((k, v))
        schema_choices = [('__all__', '<All schemas>')]
        qs = models.StatementData.objects.values('schema').distinct()
        for r in qs:
            k = r['schema']
            v = r['schema']
            if not v:
                k = '__none__'
                v = '<No schema>'
            schema_choices.append((k, v))

        if request.method == 'POST':
            if 'view_top_queries' in request.POST:
                tqf = forms.TopQueriesForm(request.POST)
                tqf.fields['column'].choices = column_choices
                tqf.fields['hostname'].choices = hostname_choices
                tqf.fields['schema'].choices = schema_choices
                if tqf.is_valid():
                    url = reverse(
                        'sqlcanon_top_queries',
                        args=[tqf.cleaned_data['limit']])
                    params = dict(
                        column=tqf.cleaned_data['column'],
                        hostname=tqf.cleaned_data['hostname'],
                        schema=tqf.cleaned_data['schema'])
                    url += '?' + urllib.urlencode(params)
                    return redirect(url)
            if 'view_last_statements' in request.POST:
                lsf = forms.LastStatementsForm(request.POST)
                if lsf.is_valid():
                    return redirect(
                        'sqlcanon_last_statements',
                        lsf.cleaned_data['minutes'])

        if not tqf:
            tqf = forms.TopQueriesForm()
            tqf.fields['column'].choices = column_choices
            tqf.fields['hostname'].choices = hostname_choices
            tqf.fields['schema'].choices = schema_choices

        if not lsf:
            lsf = forms.LastStatementsForm()

        log.debug('Rendering home view.')
        return render_to_response(template, locals(),
            context_instance=RequestContext(request))

    except Exception, e:
        log.exception('%s' % (e,))


def sparkline(request, data):
    try:
        data = [int(x) for x in data.split(',')]
        image = spark.sparkline_smooth(data)
        response = HttpResponse(mimetype="image/png")
        image.save(response, 'PNG')
        return response
    except Exception, e:
        log.exception('%s' % (e,))


def top_queries(request, n, template='sqlcanon/top_queries.html'):
    try:
        n = int(n)

        column = request.GET.get('column', 'count')
        hostname = request.GET.get('hostname', None)
        schema = request.GET.get('schema', None)

        filter_dict = {}
        if hostname:
            filter_dict['hostname'] = hostname
        if schema:
            filter_dict['schema'] = schema

        qs = core.get_top_queries(n, column, filter_dict)

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        log.exception('%s' % (e,))
