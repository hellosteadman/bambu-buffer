from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Model
from bambu_buffer.exceptions import *
from bambu_buffer.settings import ENABLED, POST_URL, TIMEOUT, AUTOPOST_MODELS
from datetime import datetime, date
from threading import Thread
import requests

__version__ = '3.3.1'
default_app_config = 'bambu_buffer.apps.BufferConfig'

class BufferThread(Thread):
    def __init__(self, token, data, *args, **kwargs):
        self.data = data
        self.token = token
        super(BufferThread, self).__init__(*args, **kwargs)

    def run(self):
        from bambu_buffer import log

        response = requests.post(
            '%s?access_token=%s' % (POST_URL, self.token),
            self.data,
            timeout = TIMEOUT
        )

        if response.status_code != 200:
            log.error(response.json())

def post(item, author, **kwargs):
    if not ENABLED:
        return

    from bambu_buffer.models import BufferToken, BufferProfile, BufferedItem

    try:
        token = author.buffer_token
    except BufferToken.DoesNotExist:
        return

    if 'url' in kwargs:
        url = kwargs.get('url')
    elif isinstance(item, Model):
        url = u'http://%s%s' % (
            get_current_site().domain, item.get_absolute_url()
        )

        content_type = ContentType.objects.get_for_model(item)
        if BufferedItem.objects.filter(
            object_id = item.pk,
            content_type = content_type
        ).exists():
            return

        BufferedItem.objects.create(
            content_type = content_type,
            object_id = item.pk
        )
    else:
        url = None

    data = {
        'text': u'%s%s' % (
            unicode(kwargs.get('text') or item),
            url and (u' %s' % url) or u''
        ),
        'profile_ids[]': kwargs.get('profile_ids') or BufferProfile.objects.filter(
            service__token = token,
            selected = True
        ).values_list('remote_id', flat = True),
        'media[description]': kwargs.get('description')
    }

    if 'picture' in kwargs:
        data['media[picture]'] = kwargs['picture']
        if not 'thumbnail' in kwargs:
            raise TypeError(
                'For image-based updates, the thumbnail parameter is required.'
            )

    if 'thumbnail' in kwargs:
        data['media[thumbnail]'] = kwargs['thumbnail']

    if 'shorten' in kwargs:
        data['shorten'] = kwargs['shorten'] and 'true' or 'false'

    if 'now' in kwargs:
        data['now'] = kwargs['now'] and 'true' or 'false'

    if 'top' in kwargs:
        data['top'] = kwargs['top'] and 'true' or 'false'

    if 'scheduled_at' in kwargs:
        if isinstance(kwargs['scheduled_at'], (datetime, date)):
            data['scheduled_at'] = kwargs['scheduled_at'].isoformat()
        else:
            try:
                data['scheduled_at'] = int(kwargs['scheduled_at'])
            except:
                raise TypeError(
                    'scheduled_at must be an integer or DateTime'
                )

    BufferThread(token.token, data).start()
