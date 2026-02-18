# core/middleware.py
from django.http import Http404, HttpResponseNotAllowed
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from core.errors import _error_response
import threading
import logging

logger = logging.getLogger(__name__)

class CustomErrorMiddleware(MiddlewareMixin):
    """
    همه خطاها رو می‌گیره و به صفحه خطای زیبا می‌فرسته
    حتی وقتی DEBUG=True
    """

    def process_exception(self, request, exception):
        # فقط خطاهای HTTP رو مدیریت کن
        if isinstance(exception, Http404):
            logger.warning(f"404 Not Found: {request.path}")
            return _error_response(request, 404, "! صفحه یافت نشد", "صفحه مورد نظر پیدا نشد.")
        
        elif isinstance(exception, PermissionDenied):
            return _error_response(request, 403, "دسترسی ممنوع", "شما اجازه دسترسی ندارید.")
        
        elif isinstance(exception, HttpResponseNotAllowed):
            return _error_response(request, 405, "متد مجاز نیست", f"متد {request.method} پشتیبانی نمی‌شود.")
        
        # خطاهای غیرمنتظره (مثل Exception)
        else:
            logger.error(f"500 Internal Server Error: {exception}", exc_info=True)
            return _error_response(request, 500, "خطای سرور", "مشکلی رخ داده است.")

    def process_response(self, request, response):
        # اگر پاسخ 404 بود (مثلاً URL ناموجود)
        if response.status_code == 404:
            logger.warning(f"404 from process_response: {request.path}")
            return _error_response(request, 404, "! صفحه یافت نشد", "صفحه مورد نظر پیدا نشد.")
        return response
    

_thread_locals = threading.local()
def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_profile():
    user = get_current_user()
    if user and user.is_authenticated:
        from accounts.models import mdl_Profile
        try:
            return mdl_Profile.objects.get(user=user)
        except mdl_Profile.DoesNotExist:
            return None
    return None


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        _thread_locals.user = request.user if hasattr(request, 'user') else None
        response = self.get_response(request)
        return response