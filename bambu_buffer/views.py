from bambu_buffer import settings, log
from bambu_buffer.models import BufferToken, BufferProfile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.http import urlencode
import requests

@login_required
def auth(request):
    next = request.GET.get('next', settings.AUTH_REDIRECT)
    request.session['bambu_buffer.next'] = next

    return HttpResponseRedirect(
        '%s?%s' % (
            settings.AUTHORISE_URL,
            urlencode(
                {
                    'client_id': settings.CLIENT_ID,
                    'redirect_uri': 'http%s://%s%s' % (
                        request.is_secure() and 's' or '',
                        get_current_site().domain,
                        reverse('buffer_callback')
                    ),
                    'response_type': settings.RESPONSE_TYPE
                }
            )
        )
    )

@login_required
def callback(request):
    response = requests.post(
        settings.TOKEN_URL,
        data = {
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'redirect_uri': 'http%s://%s%s' % (
                request.is_secure() and 's' or '',
                get_current_site().domain,
                reverse('buffer_callback')
            ),
            'code': request.GET.get('code'),
            'grant_type': settings.AUTHORISATION_CODE
        },
        timeout = settings.TIMEOUT
    )

    next = request.session.get('bambu_buffer.next',
        settings.AUTH_REDIRECT
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')

        with transaction.atomic():
            try:
                request.user.buffer_token.delete()
            except BufferToken.DoesNotExist:
                pass

            BufferToken.objects.create(
                user = user,
                token = token
            )

        log.success(data, request)
        return HttpResponseRedirect(
            reverse('buffer_profiles')
        )
    else:
        log.error(response.json(), request)

    return HttpResponseRedirect(next)

@login_required
def profiles(request):
    try:
        token = request.user.buffer_token
    except BufferToken.DoesNotExist:
        return HttpResponseRedirect(
            reverse('buffer_auth')
        )

    if request.method == 'POST':
        selected = request.POST.getlist('profiles')
        for pk in selected:
            BufferProfile.objects.filter(
                service__token = token,
                pk = pk
            ).update(
                selected = True
            )

        BufferProfile.objects.filter(
            service__token = token
        ).exclude(
            pk__in = selected
        ).update(
            selected = False
        )

        if settings.UPDATED_MESSAGE:
            messages.success(request, settings.UPDATED_MESSAGE)

        return HttpResponseRedirect(
            reverse('buffer_profiles')
        )

    return TemplateResponse(
        request,
        'buffer/profiles.html',
        {
            'profiles': BufferProfile.objects.filter(
                service__token = token
            ).select_related()
        }
    )

@login_required
def refresh(request):
    try:
        token = request.user.buffer_token
    except BufferToken.DoesNotExist:
        return HttpResponseRedirect(
            reverse('buffer_auth')
        )

    token.refresh_services()
    if settings.REFRESHED_MESSAGES:
        messages.success(request, settings.REFRESHED_MESSAGES)

    return HttpResponseRedirect(
        reverse('buffer_profiles')
    )
