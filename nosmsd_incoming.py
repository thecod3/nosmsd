#!/usr/bin/env python
# encoding=utf-8
# maintainer: rgaudin

import sys
import locale
import time
import logging
from datetime import datetime, timedelta

from nosmsd.settings import settings as nosettings
from nosmsd.utils import import_path
from nosmsd.database import Inbox

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)

if nosettings.NOSMSD_GETTEXT:
    locale.setlocale(locale.LC_ALL, nosettings.NOSMSD_GETTEXT_LOCALE)


def handle(*args, **options):

    # Message ID in DB is provided as first argument
    if len(args) != 1:
        logger.warning(u"No message ID provided")
        return False
    try:
        sql_id = int(args[0])
    except:
        sql_id = None

    if not isinstance(sql_id, int):
        logger.error(u"Provided ID (%s) is not an int." % sql_id)
        return False

    # open up smsd DB
    try:
        message = Inbox.select().get(ID=sql_id, Processed=Inbox.PROC_FALSE)
    except Inbox.DoesNotExist:
        logger.warning(u"No unprocessed row in DB for ID %d" % sql_id)
        return False

    # process handler
    try:
        handler_func = import_path(nosettings.NOSMSD_HANDLER)
    except AttributeError:
        message.status = Inbox.STATUS_ERROR
        message.save()
        logger.error(u"NO SMS_HANDLER defined while receiving SMS")
    except Exception as e:
        message.status = Inbox.STATUS_ERROR
        message.save()
        logger.error(u"Unbale to call SMS_HANDLER with %r" % e)
    else:
        try:
            #thread.start_new_thread(handler_func, (message,))
            handler_func(message)
        except Exception as e:
            message.status = Inbox.STATUS_ERROR
            message.save()
            logger.error(u"SMS handler failed on %s with %r" \
                          % (message, e))

    message.status = Inbox.STATUS_PROCESSED
    message.Processed = Inbox.PROC_TRUE
    message.save()

if __name__ == '__main__':
    handle(*sys.argv[1:])
