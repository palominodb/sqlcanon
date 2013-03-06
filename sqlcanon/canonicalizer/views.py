import datetime
import decimal
import logging

from django.conf import settings
from django.db.models import Max, Count
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone, simplejson
from django.views.decorators.csrf import csrf_exempt

import canonicalizer.funcs as app_funcs
import canonicalizer.models as app_models
import canonicalizer.utils as app_utils
import canonicalizer.spark as spark

LOGGER = logging.getLogger(__name__)


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
            post_vars_packed = post_vars(request.POST)
            #LOGGER.debug('post_vars_packed = {0}'.format(post_vars_packed))
            explained_statement = app_funcs.save_explained_statement(
                **post_vars_packed)

        ret = simplejson.dumps(rv)
    except Exception, e:
        LOGGER.exception(u'{0}'.format(e))
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
            LOGGER.error(u'Could not successfully convert the following data to JSON object: {0}'.format(post_data))
            return None

        v = {}
        v['statement'] = data.get('statement')
        v['hostname'] = data.get('hostname')
        v['canonicalized_statement'] = data.get(
            'canonicalized_statement')
        v['canonicalized_statement_hash'] = int(data.get(
            'canonicalized_statement_hash'))
        v['canonicalized_statement_hostname_hash'] = int(
            data.get('canonicalized_statement_hostname_hash'))
        if 'query_time' in data:
            v['query_time'] = float(data.get('query_time'))
        if 'lock_time' in data:
            v['lock_time'] = float(data.get('lock_time'))
        if 'rows_sent' in data:
            v['rows_sent'] = int(data.get('rows_sent'))
        if 'rows_examined' in data:
            v['rows_examined'] = int(data.get('rows_examined'))
        if 'rows_affected' in data:
            v['rows_affected'] = int(data.get('rows_affected'))
        if 'rows_read' in data:
            v['rows_read'] = int(data.get('rows_read'))
        if 'bytes_sent' in data:
            v['bytes_sent'] = int(data.get('bytes_sent'))
        if 'tmp_tables' in data:
            v['tmp_tables'] = int(data.get('tmp_tables'))
        if 'tmp_disk_tables' in data:
            v['tmp_disk_tables'] = int(data.get('tmp_disk_tables'))
        if 'tmp_table_sizes' in data:
            v['tmp_table_sizes'] = int(data.get('tmp_table_sizes'))
        if 'server_id' in data:
            v['server_id'] = int(data.get('server_id'))

        return v

    # store here the statements that needs to be EXPLAINed
    explain = []
    try:
        if request.method == 'POST':
            #LOGGER.debug(u'request.POST={0}'.format(request.POST))

            post_vars = get_post_vars(request.POST)

            if post_vars:
                post_vars['dt'] = timezone.now()

                #LOGGER.debug(u'post_vars={0}'.format(post_vars))

                statement = post_vars.get('statement')
                canonicalized_statement = post_vars.get('canonicalized_statement')
                canonicalized_statement_hostname_hash = post_vars.get('canonicalized_statement_hostname_hash')

                is_select_statement = canonicalized_statement.startswith('SELECT ')

                first_seen = False
                if is_select_statement:
                    count = (app_models.StatementData.objects.filter(
                        canonicalized_statement_hostname_hash=canonicalized_statement_hostname_hash)
                        .count())

                    # first_seen is set to True, if this is the first time
                    # we saw this statement
                    first_seen = not count

                statement_data = app_funcs.save_statement_data(**post_vars)

                if first_seen:
                    explain.append(dict(
                        statement=statement,
                        statement_data_id=statement_data.id))

        ret = simplejson.dumps(dict(explain=explain))
    except Exception, e:
        LOGGER.exception(u'{0}'.format(e))
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
        LOGGER.exception(u'{0}'.format(e))


def home(request, template='home.html'):
    try:
        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        LOGGER.exception(u'{0}'.format(e))


def sparkline(request, data):
    try:
        data = [int(x) for x in data.split(',')]
        image = spark.sparkline_smooth(data)
        response = HttpResponse(mimetype="image/png")
        image.save(response, 'PNG')
        return response
    except Exception, e:
        LOGGER.exception(u'{0}'.format(e))


def top_queries(request, n, template='canonicalizer/top_queries.html'):
    try:
        n = int(n)

        statement_data_qs = (
            app_models.StatementData.objects
            .values(
                'canonicalized_statement',
                'server_id',
                'canonicalized_statement_hostname_hash')
            .annotate(Count('id')).order_by('-id__count')[:n])

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        LOGGER.exception(u'{0}'.format(e))
