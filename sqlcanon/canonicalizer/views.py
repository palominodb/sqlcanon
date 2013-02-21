from datetime import datetime, timedelta
import logging
from django.conf import settings 
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, Count
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone, simplejson
from django.views.decorators.csrf import csrf_exempt
import mmh3
from canonicalizer.lib.canonicalizers import STATEMENT_UNKNOWN, \
    canonicalize_statement, db_increment_canonicalized_statement_count
from canonicalizer.lib.utils import int_to_hex_str
from canonicalizer.models import CanonicalizedStatement
from canonicalizer.lib import spark

import canonicalizer.funcs as app_funcs
import canonicalizer.models as app_models


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
            LOGGER.debug('request.POST={0}'.format(request.POST))
            LOGGER.debug('post_vars_packed={0}'.format(post_vars_packed))

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
        dt_start = dt - timedelta(minutes=window_length)
        #captured_statements = CapturedStatement.objects.filter(
        #    dt__gte=dt_start, dt__lte=dt).order_by('dt')
        captured_statements = CapturedStatement.objects.filter(
            dt__gte=dt_start, dt__lte=dt).values('statement', 'hostname',
            'canonicalized_statement', 'canonicalized_statement_hash',
            'statement_hostname_hash').annotate(Max('dt'), Count('dt')).order_by('dt__max')

        # calculate counts
        counts = {}
        for captured_statement in captured_statements:
            #hash = captured_statement.statement_hostname_hash
            hash = captured_statement['statement_hostname_hash']
            if hash in counts:
                #counts[hash] += 1
                counts[hash] += captured_statement['dt__count']
            else:
                #counts[hash] = 1
                counts[hash] = captured_statement['dt__count']

        statements = []
        for captured_statement in captured_statements:
            #hash = captured_statement.statement_hostname_hash
            hash = captured_statement['statement_hostname_hash']
            count = counts.get(hash, 1)
            sparkline_data_session_key = 'sparkline_data.{0}'.format(
                int_to_hex_str(hash))
            sparkline_data = request.session.get(
                sparkline_data_session_key, [])
            if sparkline_data:
                if sparkline_data[-1] != count:
                    # add new data only if it is different from the last data added
                    sparkline_data.append(count)
            else:
                sparkline_data.append(count)
            COUNT_LIMIT = 20
            if len(sparkline_data) > COUNT_LIMIT:
                # limit number of items in sparkline data
                sparkline_data = sparkline_data[-COUNT_LIMIT:len(
                    sparkline_data)]
            statements.append([
                captured_statement,
                count,
                int_to_hex_str(hash),
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
        statements = CanonicalizedStatement.objects.order_by('-instances')[:n]
        return render_to_response(template, locals(),
            context_instance=RequestContext(request))
    except Exception, e:
        LOGGER.exception('{0}'.format(e))