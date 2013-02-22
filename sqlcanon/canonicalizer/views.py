import datetime
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
def save_statement_data(request):
    """Saves statement data."""

    def post_vars(POST):
        """Returns variables from request POST."""

        statement = POST.get('statement')

        hostname = POST.get('hostname')

        canonicalized_statement = POST.get(
            'canonicalized_statement')

        canonicalized_statement_hash = POST.get(
            'canonicalized_statement_hash')
        if canonicalized_statement_hash:
            canonicalized_statement_hash = int(
                canonicalized_statement_hash)

        canonicalized_statement_hostname_hash = POST.get(
            'canonicalized_statement_hostname_hash')
        if canonicalized_statement_hostname_hash:
            canonicalized_statement_hostname_hash = int(
                canonicalized_statement_hostname_hash)

        query_time = POST.get('query_time')
        if query_time:
            query_time = float(query_time)

        lock_time = POST.get('lock_time')
        if lock_time:
            lock_time = float(lock_time)

        rows_sent = POST.get('rows_sent')
        if rows_sent:
            rows_sent = float(rows_sent)

        rows_examined = POST.get('rows_examined')
        if rows_examined:
            rows_examined = float(rows_examined)

        return (
            statement,
            hostname,
            canonicalized_statement,
            canonicalized_statement_hash,
            canonicalized_statement_hostname_hash,
            query_time,
            lock_time,
            rows_sent,
            rows_examined
        )

    # store here the statements that needs to be EXPLAINed
    explain = []
    try:
        if request.method == 'POST':
            post_vars_packed = post_vars(request.POST)
            (
                statement,
                hostname,
                canonicalized_statement,
                canonicalized_statement_hash,
                canonicalized_statement_hostname_hash,
                query_time,
                lock_time,
                rows_sent,
                rows_examined
            ) = post_vars_packed

            dt = timezone.now()
            
            LOGGER.debug('dt: {0}, post_vars_packed={1}'.format(dt,
                post_vars_packed))

            is_select_statement = canonicalized_statement.startswith('SELECT ')
            if is_select_statement:
                count = (app_models.StatementData.objects.filter(
                    canonicalized_statement_hostname_hash=
                        canonicalized_statement_hostname_hash)
                    .count())

                # first_seen is set to True, if this is the first time we saw
                # this statement
                first_seen = not count

                if first_seen:
                    explain.append(statement)

            app_funcs.save_statement_data(dt, *post_vars_packed)

        ret = simplejson.dumps(dict(explain=explain))
    except Exception, e:
        LOGGER.exception('{0}'.format(e))
        ret = simplejson.dumps(dict(error='{0}'.format(e)))
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
                'hostname',
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
        LOGGER.exception('{0}'.format(e))


def home(request, template='home.html'):
    try:
        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        LOGGER.exception('{0}'.format(e))


def sparkline(request, data):
    try:
        data = [int(x) for x in data.split(',')]
        image = spark.sparkline_smooth(data)
        response = HttpResponse(mimetype="image/png")
        image.save(response, 'PNG')
        return response
    except Exception, e:
        LOGGER.exception('{0}'.format(e))


def top_queries(request, n, template='canonicalizer/top_queries.html'):
    try:
        n = int(n)

        statement_data_qs = (
            app_models.StatementData.objects
            .values(
                'canonicalized_statement',
                'hostname',
                'canonicalized_statement_hostname_hash')
            .annotate(Count('id')).order_by('-id__count')[:n])

        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        LOGGER.exception('{0}'.format(e))