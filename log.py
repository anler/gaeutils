import sys
import logging

from django.conf import settings
from django.utils.log import AdminEmailHandler as DjangoAdminEmailHandler

from google.appengine.api import mail


class AdminEmailHandler(DjangoAdminEmailHandler):
    """An exception log handler that e-mails log entries to site admins.

    If the request is passed as the first argument to the log record,
    request data will be provided in the
    """
    def emit(self, record):
        import traceback
        from django.conf import settings
        from django.views.debug import ExceptionReporter

        try:
            if sys.version_info < (2,5):
                # A nasty workaround required because Python 2.4's logging
                # module doesn't support passing in extra context.
                # For this handler, the only extra data we need is the
                # request, and that's in the top stack frame.
                request = record.exc_info[2].tb_frame.f_locals['request']
            else:
                request = record.request

            subject = '%s (%s IP): %s' % (
                record.levelname,
                (request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'),
                record.msg
            )
            request_repr = repr(request)
        except:
            subject = '%s: %s' % (
                record.levelname,
                record.msg
            )

            request = None
            request_repr = "Request repr() unavailable"

        if record.exc_info:
            exc_info = record.exc_info
            stack_trace = '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            exc_info = (None, record.msg, None)
            stack_trace = 'No stack trace available'

        text_message = "%s\n\n%s" % (stack_trace, request_repr)
        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        html_message = self.include_html and reporter.get_traceback_html() or None

        message = mail.EmailMessage(sender=settings.SERVER_EMAIL)
        message.subject = subject
        message.to = ["%s<%s>" % (n, e) for n, e in settings.ADMINS]
        message.body = text_message
        if html_message:
            message.html = html_message
        message.send()


