from django.shortcuts import render
from django.views import View
from django.contrib import messages
from core.errors import _error_response 
import importlib
from django.http import Http404, HttpResponseNotAllowed
from django.core.exceptions import PermissionDenied
from django.template import Template, Context
import json
import logging
logger = logging.getLogger(__name__)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.safestring import mark_safe

from accounts.models import *
from appointment.models import *

from core.templatetags.jdate import *

from core.generic import (
    apply_search,
    apply_filters,
    apply_pagination,
    render_search_form,
    render_filter_form,
    render_pagination
)

class ManagementView(View):
    ROUTES = {
        'psychologist': 'management.views.ManagementPsychologistActionView',
    }

    def dispatch(self, request, subject, action, pk=None):
        if subject not in self.ROUTES:
            return _error_response(request, 404, "OOPS! صفحه یافت نشد", "موضوع درخواستی پشتیبانی نمی‌شود.")

        try:
            module_path, view_name = self.ROUTES[subject].rsplit('.', 1)
            module = importlib.import_module(module_path)
            view_class = getattr(module, view_name)
        except (ImportError, AttributeError) as e:
            pass
            # logger.error(f"Dynamic view import failed: {e}")
            # return _error_response(request, 500, "خطای سرور", "ویوی مورد نظر یافت نشد.")

        try:
            view = view_class.as_view()
            return view(request, subject=subject, action=action, pk=pk)

        except Http404:
            return _error_response(request, 404, "صفحه یافت نشد", "آیتم مورد نظر وجود ندارد.")
        except PermissionDenied:
            return _error_response(request, 403, "دسترسی ممنوع", "شما اجازه انجام این عمل را ندارید.")
        except Exception as e:
            messages.add_message(
                request,
                messages.ERROR,
                str(e),
                extra_tags=json.dumps({
                    "style": "error",
                    "size": "medium",
                    "duration": 6000,
                    "location": "top-right",
                    "title": "خطا",
                })
            )
            return _error_response(
                request,
                500,
                "خطای داخلی",
                str(e)
            )
        
class BaseManagementView(LoginRequiredMixin, View):
    """کلاس پایه برای همه داشبوردها - شامل سایدبار مشترک"""
    
    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    def get_sidebar_menu(self, request, active_section=None):
        """ساخت سایدبار به صورت متمرکز و قابل گسترش"""
        profile = request.user
        roles = list(profile.roles.values_list('name', flat=True))
        
        sidebar_menu = [
            {
                'title': 'اصلی',
                'items': [
                    {'label': 'خانه', 'url': '/', 'icon': 'fe fe-home', 'is_active': False},
                    {'label': 'داشبورد', 'url': '/dashboard/user', 'icon': 'fe fe-grid', 'is_active': False},
                ]
            }
        ]

        # مدیر کلینیک
        if "manager" in roles:
            sidebar_menu.append({
                'title': 'مدیر کلینیک',
                'items': [
                    {'label': 'پنل مدیریت', 'url': '/dashboard/manager', 
                     'icon': 'ri ri-user-settings-line', 'is_active': False},
                ]
            })

        # متخصص
        if "psychologist" in roles:
            items = [
                {'label': 'پنل متخصص', 'url': '/dashboard/psychologist', 
                 'icon': 'mdi mdi-stethoscope', 'is_active': False},
            ]


            sidebar_menu.append({
                'title': 'متخصص',
                'items': items
            })

        # منشی
        if "secretary" in roles:
            sidebar_menu.append({
                'title': 'منشی',
                'items': [
                    {'label': 'پنل منشی', 'url': '/dashboard/secretary', 
                     'icon': 'ti ti-microphone', 'is_active': False},
                ]
            })

        if "admin" in roles:
            sidebar_menu.append({
                'title': 'ادمین',
                'items': [
                    {'label': 'پنل ادمین', 'url': '/dashboard/admin', 
                     'icon': 'ri ri-admin-line', 'is_active': False},
                ]
            })

        # فعال کردن آیتم فعلی
        if active_section:
            for section in sidebar_menu:
                for item in section.get('items', []):
                    if item['url'] == active_section:
                        item['is_active'] = True
                        break

        return sidebar_menu
  


class ManagementPsychologistActionView(BaseManagementView):
    
    def get(self, request, subject=None, action=None, **kwargs):
        
        if action == 'list':
            psychologists=Psychologist.objects.all()
            queryset = Psychologist.objects.all()
            search_fields = ['user__first_name', 'user__last_name', 'user__username', 'specialty']
            filter_fields = {
                'is_active': {
                    'label': 'وضعیت',
                    'type': 'boolean',
                    'choices': [( '', 'وضعیت'), ('True', 'فعال'), ('False', 'غیرفعال')]
                },
                # 'specialty': {
                #     'label': 'تخصص',
                #     'type': 'select',
                #     'choices': []          
                # },
                
            }
            queryset, query = apply_search(queryset, request, search_fields)
            queryset = apply_filters(queryset, request, filter_fields)

            psychologists, current_page, total_pages, total = apply_pagination(queryset, request, per_page=15)
            

            # ==================== ساخت تمپلیت ====================
            template_string = """
                <div class="main-content with-sidebar">
                    <div class="side-app">
                        <div class="main-container container-fluid">
                            <div class="page-header">
                                <ol class="breadcrumb">
                                    <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                    <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</li>
                                    <li class="breadcrumb-back">
                                        <a href="/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                    </li>
                                </ol>
                            </div>

                            <div class="row">

                                <div class="col-xl-3 col-lg-4">
                                    {{search_form}}
                                    {{filter_form}}
                                </div>


                                <div class="col-xl-9 col-lg-8">
                                    <div class="card">
                                        
                                        <div class="card-body">
                                            <div class="table-responsive">
                                                <table class="table table-bordered border text-nowrap mb-0" id="removecolumns-edit">
                                                    <thead>
                                                        <tr>
                                                            <th>نام</th>
                                                            <th>نوع</th>
                                                            <th>کد عضویت</th>
                                                            <th>کد اشتغال</th>
                                                            <th>تاریخ ثبت</th>
                                                            <th>وضعیت</th>
                                                            <th>حذف</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {% for psychologist in psychologists %}
                                                        <tr>
                                                            <td>{{psychologist.profile.first_name}} {{psychologist.profile.last_name}}</td>
                                                            <td>{{psychologist.PsychologistType}}</td>
                                                            <td>{{psychologist.membership_code}}</td>
                                                            <td>{{psychologist.license_code}}</td>
                                                            <td>{{psychologist.created_at|to_jalali}}</td>
                                                            <td>
                                                                <div class="btn-list">
                                                                    <button id="bEdit" type="button" class="btn btn-sm btn-success">
                                                                        فعال
                                                                    </button>
                                                                </div>
                                                            </td>
                                                            <td>
                                                                <div class="btn-list">
                                                                    <button id="bDel" type="button" class="btn  btn-sm btn-danger">
                                                                        <span class="fe fe-trash-2"> </span>
                                                                    </button>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                        {% endfor %}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            
                        </div>
                    </div>
                </div>
            """

            t = Template(template_string)
            content = t.render(Context({
                'psychologists':psychologists,
                'search_form': mark_safe(render_search_form(query)),
                'filter_form': mark_safe(render_filter_form(filter_fields, request)),
                'pagination': mark_safe(render_pagination(current_page, total_pages, f"&q={query}" if query else "")),
                'total': total,
            }))

            context = {
                'content': mark_safe(content),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/user'),
                'extra_css': [],
                'extra_js': [],
            }
            
            return render(request, 'index1.html', context)

        return super().get(request, subject, action, **kwargs)

