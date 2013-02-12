from datetime import datetime, timedelta
import logging
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import mmh3
from canonicalizer.lib.canonicalizers import STATEMENT_UNKNOWN, \
    canonicalize_statement, db_increment_canonicalized_statement_count
from canonicalizer.lib.utils import int_to_hex_str
from canonicalizer.models import CapturedStatement
from canonicalizer.lib import spark

LOGGER = logging.getLogger(__name__)

@csrf_exempt
def process_captured_statement(request):
    try:
        if request.method == 'POST':
            statement = unicode(request.POST['statement'])
            LOGGER.debug(u'Statement: {0}'.format(statement))
            dt = timezone.now()
            canonicalize_statement_results = canonicalize_statement(statement)
            for statement_orig, statement_normalized, statement_canonicalized, values \
                in canonicalize_statement_results:

                db_increment_canonicalized_statement_count(statement_canonicalized)
                if not statement_canonicalized:
                    statement_canonicalized = STATEMENT_UNKNOWN
                hash = mmh3.hash(statement_canonicalized)

                CapturedStatement.objects.create(
                    dt=dt,
                    statement=statement_orig,
                    canonicalized_statement=statement_canonicalized,
                    canonicalized_statement_hash=hash,
                )


        return HttpResponse('')
    except Exception, e:
        LOGGER.exception('{0}'.format(e))

def last_statements(request, window_length, template='canonicalizer/last_statements.html'):
    try:
        window_length = int(window_length)
        dt = timezone.now()
        dt_start = dt - timedelta(minutes=window_length)
        captured_statements = CapturedStatement.objects.filter(
            dt__gte=dt_start, dt__lte=dt).order_by('dt')

        # calculate counts
        counts = {}
        for captured_statement in captured_statements:
            hash = captured_statement.canonicalized_statement_hash
            if counts.has_key(hash):
                counts[hash] += 1
            else:
                counts[hash] = 1

        statements = []
        for captured_statement in captured_statements:
            hash = captured_statement.canonicalized_statement_hash
            count = counts.get(hash, 1)
            sparkline_data_session_key = 'sparkline_data.{0}'.format(int_to_hex_str(hash))
            sparkline_data = request.session.get(sparkline_data_session_key, [])
            if sparkline_data:
                if sparkline_data[-1] != count:
                    # add new data only if it is different from the last data added
                    sparkline_data.append(count)
            else:
                sparkline_data.append(count)
            COUNT_LIMIT = 20
            if len(sparkline_data) > COUNT_LIMIT:
                # limit number of items in sparkline data
                sparkline_data = sparkline_data[-COUNT_LIMIT:len(sparkline_data)]
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