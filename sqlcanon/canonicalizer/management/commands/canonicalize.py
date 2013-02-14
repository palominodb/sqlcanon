from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from canonicalizer.lib.canonicalizers import process_log_file, \
    process_query_log_from_stdin, query_log_listen, print_db_counts

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--print-db-counts',
            action='store_true',
            default=False,
            dest='print_db_counts',
            help='Print counts stored in DB at the end of execution.'),

        make_option('--log-file',
            dest='log_file',
            help='Mysql query log file to process.'),

        make_option('--listen',
            action='store_true',
            dest='listen',
            help='Opens up log file and waits for newly written data.'),

        make_option('--listen-window-length',
            type='int',
            default=5,
            dest='listen_window_length',
            help='Length of period of query list filter in number of minutes. (default: 5)'),
    )

    def handle(self, *args, **options):
        try:
            log_file = options.get('log_file')
            listen = options.get('listen')
            listen_window_length = options.get('listen_window_length')
            if log_file and listen:
                print 'Listening for new data in {0} (window_length={1})...'.format(
                    log_file, listen_window_length
                )
                query_log_listen(log_file=log_file, listen_frequency=1,
                    listen_window_length=listen_window_length)
            elif log_file:
                print 'Processing contents from log file {0}...'.format(log_file)
                process_log_file(log_file)
            else:
                # read from pipe
                print 'Processing data from stdin...'
                process_query_log_from_stdin()
            if options.get('print_db_counts'):
                print_db_counts()
        except Exception, e:
            raise CommandError('An error has occurred: {0}'.format(e))