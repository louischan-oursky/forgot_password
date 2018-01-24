# Copyright 2016 Oursky Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os

import boto3
import pyzmail

logger = logging.getLogger(__name__)


class Mailer:
    def __init__(self, **smtp_params):
        self.smtp_params = smtp_params
        if os.getenv('FORGOT_PASSWORD_AWSSES_REGION') is not None:
            region = os.environ['FORGOT_PASSWORD_AWSSES_REGION']
            access_key = os.getenv('FORGOT_PASSWORD_AWSSES_ACCESS_KEY')
            secret_key = os.getenv('FORGOT_PASSWORD_AWSSES_SECRET_KEY')
            self.awsses_client = boto3.client(
                'ses',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
        else:
            self.awsses_client = None

    def send_mail(self, sender, to, subject, text, html=None, reply_to=None):
        if self.awsses_client is None:
            return self._smtp(
                sender=sender,
                to=to,
                subject=subject,
                text=text,
                html=html,
                reply_to=reply_to,
            )
        return self._awsses(
            sender=sender,
            to=to,
            subject=subject,
            text=text,
            html=html,
            reply_to=reply_to,
        )

    def _smtp(self, sender, to, subject, text, html=None, reply_to=None):
        """
        Send email to user.
        """
        encoding = 'utf-8'
        text_args = (text, encoding)
        html_args = (html, encoding) if html else None
        headers = []

        if reply_to:
            headers.append(('Reply-To', reply_to))

        payload, mail_from, rcpt_to, msg_id = pyzmail.compose_mail(
            sender, [to], subject, encoding, text_args,
            html=html_args, headers=headers)

        try:
            pyzmail.send_mail2(payload,
                               mail_from,
                               rcpt_to,
                               **self.smtp_params)
        except Exception as e:
            logger.exception('Unable to send email to the receipient.')
            raise Exception('Unable to send email to the receipient.')

    def _awsses(self, sender, to, subject, text, html=None, reply_to=None):
        CHARSET = 'UTF-8'
        request = {
            'Source': sender,
            'Destination': {
                'ToAddresses': [to],
            },
            'Message': {
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': text,
                    },
                },
            },
        }
        if html is not None:
            request['Message']['Body']['Html'] = {
                'Charset': CHARSET,
                'Data': html,
            }
        if reply_to is not None:
            request['ReplyToAddresses'] = [reply_to]
        try:
            self.awsses_client.send_email(**request)
        except Exception as e:
            logger.exception('Unable to send email to the receipient.')
            raise Exception('Unable to send email to the receipient.')
