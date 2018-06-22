#!/usr/bin/env python
"""
email.py - various functions to work with emails in the pdata application
"""
from __future__ import unicode_literals, division, absolute_import
import argparse
import logging.config
from smtplib import SMTPException
import sys

import django
django.setup()
from django.core.mail import EmailMessage
from django.template.defaultfilters import pluralize

from pdata_app.models import EmailQueue

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_LOG_FORMAT = '%(levelname)s: %(message)s'

logger = logging.getLogger(__name__)


EMAIL_HOST = 'exchsmtp.stfc.ac.uk'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

FROM_ADDRESS = 'no-reply@prima-dm.ceda.ac.uk'
REPLY_TO_ADDRESS = 'jon.seddon@metoffice.gov.uk'


def parse_args():
    """
    Parse command-line arguments
    """
    parser = argparse.ArgumentParser(description='Send any unsent emails that '
                                                 'are in the queue.')
    parser.add_argument('-l', '--log-level', help='set logging level to one of '
        'debug, info, warn (the default), or error')
    args = parser.parse_args()

    return args


def main():
    """
    Send any queued emails

    :return:
    """
    num_sent = 0

    for email in EmailQueue.objects.filter(sent=False):
        if not email.recipient.email:
            msg = 'No email address is available for user {}'.format(
                email.recipient.username)
            logger.warning(msg)
        else:
            email_msg = EmailMessage(
                subject=email.subject,
                body=email.message,
                from_email=FROM_ADDRESS,
                reply_to=(REPLY_TO_ADDRESS,),
                to=(email.recipient.email,)
            )

            try:
                email_msg.send()
            except SMTPException as exc:
                msg = 'Unable to send email to {} with subject {}.\n{}'.format(
                    email.recipient.email, email.subject, exc.message)
                logger.warning(msg)
            else:
                email.sent = True
                email.save()
                num_sent += 1

    logger.debug('{} email{} sent'.format(num_sent, pluralize(num_sent)))


if __name__ == '__main__':
    cmd_args = parse_args()

    # determine the log level
    if cmd_args.log_level:
        try:
            log_level = getattr(logging, cmd_args.log_level.upper())
        except AttributeError:
            logger.setLevel(logging.WARNING)
            logger.error('log-level must be one of: debug, info, warn or error')
            sys.exit(1)
    else:
        log_level = DEFAULT_LOG_LEVEL

    # configure the logger
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': DEFAULT_LOG_FORMAT,
            },
        },
        'handlers': {
            'default': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': True
            }
        }
    })

    # run the code
    main()
