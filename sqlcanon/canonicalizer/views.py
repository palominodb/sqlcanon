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
from canonicalizer.models import CapturedStatement, CanonicalizedStatement
from canonicalizer.lib import spark

LOGGER = logging.getLogger(__name__)

@csrf_exempt
def process_captured_statement(request):
    explain = []
    try:
        if request.method == 'POST':
            hostname = unicode(request.POST['hostname'])
            statement = unicode(request.POST['statement'])
            LOGGER.debug(u'Hostname: {0}, Statement: {1}'.format(hostname, statement))

            dt = timezone.now()
            canonicalize_statement_results = canonicalize_statement(statement)
            for statement_orig, statement_normalized, statement_canonicalized, values \
                    in canonicalize_statement_results:

                if not statement_canonicalized:
                    statement_canonicalized = STATEMENT_UNKNOWN

                is_select_statement = statement_canonicalized.strip().startswith('SELECT ')
                #LOGGER.debug('is_select_statement: {0}'.format(is_select_statement))
                hash = mmh3.hash(statement_canonicalized)
                statement_hostname_hash = mmh3.hash('{0}{1}'.format(
                    statement_canonicalized, hostname
                ))

                if is_select_statement:
                    #LOGGER.debug('statement_hostname_hash: {0}'.format(statement_hostname_hash))
                    count = CanonicalizedStatement.objects.filter(
                        statement_hostname_hash=statement_hostname_hash).count()
                    #LOGGER.debug('count: {0}'.format(count))
                    #is_new = not (CapturedStatement.objects.filter(
                    #    statement_hostname_hash=statement_hostname_hash).count())
                    is_new = not count
                    #LOGGER.debug('is_new: {0}'.format(is_new))
                    if is_new:
                        explain.append(statement_orig)
                        LOGGER.debug('Added statement for EXPLAIN execution: {0}'.format(
                            statement_orig
                        ))

                db_increment_canonicalized_statement_count(
                    canonicalized_statement=statement_canonicalized,
                    canonicalized_statement_hash=hash,
                    hostname=hostname,
                    statement_hostname_hash=statement_hostname_hash)

                qs = CapturedStatement.objects.order_by('-last_updated')[:1]
                captured_statement = None
                if qs:
                    captured_statement = qs[0]
                if captured_statement:
                    sequence_id = (captured_statement.sequence_id + 1) % settings.CAPTURED_STATEMENT_ROW_LIMIT
                else:
                    sequence_id = 1
                try:
                    captured_statement = CapturedStatement.objects.get(
                        sequence_id=sequence_id)
                    captured_statement.dt = dt
                    captured_statement.statement = statement_orig
                    captured_statement.hostname = hostname
                    captured_statement.canonicalized_statement = statement_canonicalized
                    captured_statement.canonicalized_statement_hash = hash
                    captured_statement.statement_hostname_hash = statement_hostname_hash
                    captured_statement.save()
                except ObjectDoesNotExist:
                    CapturedStatement.objects.create(
                        dt=dt,
                        statement=statement_orig,
                        hostname=hostname,
                        canonicalized_statement=statement_canonicalized,
                        canonicalized_statement_hash=hash,
                        statement_hostname_hash=statement_hostname_hash,
                        sequence_id=sequence_id,
                    )

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