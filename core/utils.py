from django.utils.safestring import mark_safe
from django.urls import reverse
from urllib.parse import urlencode 
from django.template import Template, Context
import math

# ====================== Helper Functions ======================
def get_user_status(psychologist=None, request=None):
    """
    وضعیت کاربر: لاگین، مالکیت و نقش‌ها
    """
    if not request or not hasattr(request, 'user'):
        return {
            'is_authenticated': False,
            'is_owner': False,
            'roles': []
        }

    user = request.user
    if not user.is_authenticated:
        return {
            'is_authenticated': False,
            'is_owner': False,
            'roles': []
        }

    result = {
        'is_authenticated': True,
        'is_owner': False,
        'roles': []
    }

    if hasattr(user, 'roles'):
        result['roles'] = list(user.roles.values_list('name', flat=True))

    if psychologist and hasattr(psychologist, 'profile'):
        if psychologist.profile == user:
            result['is_owner'] = True

    return result
