import datetime
import decimal
import logging
import pprint
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Max, Count, Sum, Avg
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils import timezone, simplejson
from django.views.decorators.csrf import csrf_exempt

import canonicalizer.forms as app_forms
import canonicalizer.funcs as app_funcs
import canonicalizer.models as app_models
import canonicalizer.utils as app_utils
import canonicalizer.spark as spark
from canonicalizer.businesslogic import core as core_logic

log = logging.getLogger(__name__)


def explain_results(request, id, template='canonicalizer/explain_results.html'):
    """Shows explain results page."""
    id = int(id)
    expstmt = app_models.ExplainedStatement.objects.get(pk=id)
    result = expstmt.explainresult_set.all()
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def explained_statements(
        request,
        template='canonicalizer/explained_statements.html'):
    """Shows explained statements page."""

    stmts = app_models.ExplainedStatement.objects.all()
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@csrf_exempt
def save_explained_statement(request):
    """Saves explain data."""

    def post_vars(post):
        data = simplejson.loads(post.get('data'))

        statement_data_id = int(data.get('statement_data_id'))
        explain_rows = simplejson.loads(data.get('explain_rows'))
        db = data.get('db')
        server_id = int(data.get('server_id'))

        return dict(
            statement_data_id=statement_data_id,
            explain_rows=explain_rows,
            db=db,
            server_id=server_id)

    rv = {}
    try:
        if request.method == 'POST':
            log.debug(u'\nrequest.POST:\n%s' % (pprint.pformat(request.POST)))
            post_vars_packed = post_vars(request.POST)
            #log.debug('post_vars_packed = {0}'.format(post_vars_packed))
            explained_statement = app_funcs.save_explained_statement(
                **post_vars_packed)

        ret = simplejson.dumps(rv)
    except Exception, e:
        log.exception(u'{0}'.format(e))
        ret = simplejson.dumps(dict(error=u'{0}'.format(e)))
    return HttpResponse(ret, mimetype='application/json')


@csrf_exempt
def save_statement_data(request):
    """Saves statement data."""

    def get_post_vars(post):
        """Returns variables from request post."""

        post_data = post.get('data')
        try:
            data = simplejson.loads(post_data)
        except:
            log.error(u'Could not successfully convert the following data to JSON object: {0}'.format(post_data))
            return None

        v = {}
        v['statement'] = data.get('statement')
        v['hostname'] = data.get('hostname')
        v['canonicalized_statement'] = data.get('canonicalized_statement')

        if 'canonicalized_statement_hash' in data and data['canonicalized_statement_hash']:
            v['canonicalized_statement_hash'] = int(data['canonicalized_statement_hash'])

        if 'canonicalized_statement_hostname_hash' in data and data['canonicalized_statement_hostname_hash']:
            v['canonicalized_statement_hostname_hash'] = int(data['canonicalized_statement_hostname_hash'])

        if 'query_time' in data and data['query_time']:
            v['query_time'] = float(data.get('query_time'))

        if 'lock_time' in data and data['lock_time']:
            v['lock_time'] = float(data.get('lock_time'))

        if 'rows_sent' in data and data['rows_sent']:
            v['rows_sent'] = int(data.get('rows_sent'))

        if 'rows_examined' in data and data['rows_examined']:
            v['rows_examined'] = int(data.get('rows_examined'))

        if 'rows_affected' in data and data['rows_affected']:
            v['rows_affected'] = int(data.get('rows_affected'))

        if 'rows_read' in data and data['rows_read']:
            v['rows_read'] = int(data.get('rows_read'))

        if 'bytes_sent' in data and data['bytes_sent']:
            v['bytes_sent'] = int(data.get('bytes_sent'))

        if 'tmp_tables' in data and data['tmp_tables']:
            v['tmp_tables'] = int(data.get('tmp_tables'))

        if 'tmp_disk_tables' in data and data['tmp_disk_tables']:
            v['tmp_disk_tables'] = int(data.get('tmp_disk_tables'))

        if 'tmp_table_sizes' in data and data['tmp_table_sizes']:
            v['tmp_table_sizes'] = int(data.get('tmp_table_sizes'))

        if 'server_id' in data:
            v['server_id'] = int(data.get('server_id'))

        if 'schema' in data and data['schema'] and data['schema'].strip():
            v['schema'] = data['schema'].strip()

        if 'hostname' in data and data['hostname'] and data['hostname'].strip():
            v['hostname'] = data['hostname'].strip()

        return v

    # store here the statements that needs to be EXPLAINed
    explain = []
    try:
        if request.method == 'POST':
            log.debug(u'\nrequest.POST:\n%s' % (pprint.pformat(request.POST)))

            post_vars = get_post_vars(request.POST)

            log.debug(u'\npost_vars:\n%s' % (pprint.pformat(post_vars)))

            if post_vars:
                post_vars['dt'] = timezone.now()

                #log.debug(u'post_vars={0}'.format(post_vars))

                statement = post_vars.get('statement')
                canonicalized_statement = post_vars.get('canonicalized_statement')
                canonicalized_statement_hostname_hash = post_vars.get('canonicalized_statement_hostname_hash')

                #log.debug((
                #    u'\n'
                #    u'statement:\n'
                #    u'%s\n'
                #    u'canonicalized_statement:\n'
                #    u'%s\n'
                #    u'canonicalized_statement_hostname_hash: %s') % (
                #        statement, canonicalized_statement, canonicalized_statement_hostname_hash)

                if canonicalized_statement:
                    is_select_statement = canonicalized_statement.startswith('SELECT ')
                else:
                    is_select_statement = False

                first_seen = False
                if is_select_statement:
                    count = (app_models.StatementData.objects.filter(
                        canonicalized_statement_hostname_hash=canonicalized_statement_hostname_hash)
                        .count())

                    # first_seen is set to True, if this is the first time
                    # we saw this statement
                    first_seen = not count

                    log.debug(u'\nis_select_statement=%s\nfirst_seen=%s' % (
                        is_select_statement, first_seen))

                statement_data = app_funcs.save_statement_data(**post_vars)

                if first_seen:
                    explain_data = dict(
                        statement=statement,
                        statement_data_id=statement_data.id)
                    if 'schema' in post_vars and post_vars['schema'] and post_vars['schema'].strip():
                        explain_data['schema'] = post_vars['schema'].strip()
                    explain.append(explain_data)

        ret = simplejson.dumps(dict(explain=explain))
    except Exception, e:
        log.exception(u'{0}'.format(e))
        ret = simplejson.dumps(dict(error=u'{0}'.format(e)))
    return HttpResponse(ret, mimetype='application/json')


def last_statements(request, window_length,
                    template='canonicalizer/last_statements.html'):
    try:
        window_length = int(window_length)
        dt = timezone.now()
        dt_start = dt - datetime.timedelta(minutes=window_length)
        statement_data_qs = (
            app_models.StatementData.objects
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
            sparkline_data_session_key = 'sparkline_data.{0}'.format(
                app_utils.int_to_hex_str(
                    canonicalized_statement_hostname_hash))
            sparkline_data = request.session.get(
                sparkline_data_session_key, [])
            if sparkline_data:
                if sparkline_data[-1] != count:
                    # add new data only if it is different from the last data
                    # added
                    sparkline_data.append(count)
            else:
                sparkline_data.append(count)
            if len(sparkline_data) > settings.SPARKLINE_DATA_COUNT_LIMIT:
                # limit number of items in sparkline data
                sparkline_data = sparkline_data[
                    -settings.SPARKLINE_DATA_COUNT_LIMIT:len(sparkline_data)]
            statements.append([
                statement_data,
                count,
                app_utils.int_to_hex_str(canonicalized_statement_hostname_hash),
                ','.join([str(i) for i in sparkline_data])
            ])
            request.session[sparkline_data_session_key] = sparkline_data

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        log.exception(u'{0}'.format(e))


def home(request, template='site/home.html'):
    try:
        tqf = None
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
        qs = app_models.StatementData.objects.values('hostname').distinct()
        for r in qs:
            k = r['hostname']
            v = r['hostname']
            if not v:
                k = '__none__'
                v = '<No hostname>'
            hostname_choices.append((k, v))
        schema_choices = [('__all__', '<All schemas>')]
        qs = app_models.StatementData.objects.values('schema').distinct()
        for r in qs:
            k = r['schema']
            v = r['schema']
            if not v:
                k = '__none__'
                v = '<No schema>'
            schema_choices.append((k, v))

        if request.method == 'POST':
            if 'view_top_queries' in request.POST:
                tqf = app_forms.TopQueriesForm(request.POST)
                tqf.fields['column'].choices = column_choices
                tqf.fields['hostname'].choices = hostname_choices
                tqf.fields['schema'].choices = schema_choices
                if tqf.is_valid():
                    url = reverse('top_queries', args=[tqf.cleaned_data['limit']])
                    params = dict(
                        column=tqf.cleaned_data['column'],
                        hostname=tqf.cleaned_data['hostname'],
                        schema=tqf.cleaned_data['schema'])
                    url += '?' + urllib.urlencode(params)
                    return redirect(url)
            if 'view_last_statements' in request.POST:
                lsf = app_forms.LastStatementsForm(request.POST)
                if lsf.is_valid():
                    return redirect('last_statements', lsf.cleaned_data['minutes'])

        if not tqf:
            tqf = app_forms.TopQueriesForm()
            tqf.fields['column'].choices = column_choices
            tqf.fields['hostname'].choices = hostname_choices
            tqf.fields['schema'].choices = schema_choices

        if not lsf:
            lsf = app_forms.LastStatementsForm()

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        log.exception(u'{0}'.format(e))


def sparkline(request, data):
    try:
        data = [int(x) for x in data.split(',')]
        image = spark.sparkline_smooth(data)
        response = HttpResponse(mimetype="image/png")
        image.save(response, 'PNG')
        return response
    except Exception, e:
        log.exception(u'{0}'.format(e))


def top_queries(request, n, template='canonicalizer/top_queries.html'):
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

        qs = core_logic.get_top_queries(n, column, filter_dict)

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        log.exception(u'{0}'.format(e))
