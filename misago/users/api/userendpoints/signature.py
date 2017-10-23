from rest_framework.response import Response

from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from misago.conf import settings
from misago.core.utils import format_plaintext_for_html
from misago.users.serializers import EditSignatureSerializer
from misago.users.signatures import is_user_signature_valid, set_user_signature


def signature_endpoint(request):
    user = request.user

    if not user.acl_cache['can_have_signature']:
        raise PermissionDenied(_("You don't have permission to change signature."))

    if user.is_signature_locked:
        if user.signature_lock_user_message:
            extra = format_plaintext_for_html(user.signature_lock_user_message)
        else:
            extra = None

        return Response(
            {
                'detail': _("Your signature is locked. You can't change it."),
                'extra': extra
            },
            status=403,
        )

    if request.method == 'POST':
        return edit_signature(request, user)

    return get_signature_options(user)


def get_signature_options(user):
    options = {
        'signature': None,
        'limit': settings.signature_length_max,
    }

    if user.signature:
        options['signature'] = {
            'plain': user.signature,
            'html': user.signature_parsed,
        }

        if not is_user_signature_valid(user):
            options['signature']['html'] = None

    return Response(options)


def edit_signature(request, user):
    serializer = EditSignatureSerializer(user, data=request.data)
    if serializer.is_valid():
        set_user_signature(request, user, serializer.validated_data['signature'])
        user.save(update_fields=['signature', 'signature_parsed', 'signature_checksum'])
        return get_signature_options(user)
    else:
        return Response(
            {
                'detail': serializer.errors
            },
            status=400,
        )
