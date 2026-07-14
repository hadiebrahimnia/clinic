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
    render_pagination,
    render_generic_table
)

class ManagementView(View):
    ROUTES = {
        'role':'management.views.RoleManagementView',
        'country':'management.views.CountryManagementView',
        'province':'management.views.ProvinceManagementView',
        'city':'management.views.CityManagementView',
        'university':'management.views.UniversityManagementView',
        'fieldofstudy':'management.views.FieldOfStudyManagementView',
        'specialization':'management.views.SpecializationManagementView',
        'profile':'management.views.ProfileManagementView',
        'secretary': 'management.views.SecretaryManagementView',
        'psychologisttype': 'management.views.PsychologistTypeManagementView',
        'psychologist': 'management.views.PsychologistManagementView',
        'psychologistdocument': 'management.views.PsychologistDocumentManagementView',
        'psychologistspecialties': 'management.views.PsychologistSpecialtiesManagementView',
        'psychologistdegree': 'management.views.PsychologistDegreeManagementView',
        'sectiontype': 'management.views.SectionTypeManagementView',
        'psychologistsection': 'management.views.PsychologistSectionManagementView',
        'platform': 'management.views.PlatformManagementView',
        'psychologistsocialmedia': 'management.views.PsychologistSocialMediaManagementView',
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
  


class PsychologistManagementView(BaseManagementView):
    
    def get(self, request, subject=None, action=None, pk=None ,**kwargs):
        
        if action == 'list':
            queryset = Psychologist.objects.all().exclude(is_deleted=True).select_related('profile')
            search_fields = [
                'profile__first_name',
                'profile__last_name',
                # اگر می‌خواهید جستجوی ترکیبی هم بهتر کار کند (اختیاری)
                # 'profile__first_name__icontains', 'profile__last_name__icontains'
            ]
            filter_fields = {
                'is_active': {
                    'label': 'وضعیت',
                    'type': 'boolean',
                    'choices': [('', 'همه'), ('True', 'فعال'), ('False', 'غیرفعال')]
                },
            }
            queryset, query = apply_search(queryset, request, search_fields)
            queryset = apply_filters(queryset, request, filter_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل مدیریت</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست متخصصان</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """
            
            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)
            columns = [
                {
                    'field': 'profile__first_name',
                    'title': 'نام و نام خانوادگی',
                    'display': lambda obj: '''
                        <a href="/management/psychologist/detail/{pk}/" 
                        class="btn btn-info btn-pill"
                        target="_blanck"
                        >
                            {full_name}
                        </a>
                    '''.format(
                        pk=getattr(obj, 'pk', getattr(obj, 'id', '')),
                        full_name=f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip() or '—'
                    )
                },
                {'field': 'PsychologistType', 'title': 'عنوان'},
                {
                    'field': 'is_active',
                    'title': 'وضعیت',
                    'display': {
                        'type': 'toggle',
                        'app': 'accounts',
                        'model': 'Psychologist',
                        'title': 'وضعیت',
                        'confirm': 'تغییر وضعیت',
                        'extra_class': ''
                    }
                },
            ]
            actions = [
                {
                    'type': 'edit',
                    'url': '/management/psychologist/edit/{pk}/'
                },
                {
                    'type': 'delete',
                    'app': 'accounts',
                    'model': 'Psychologist',
                    'field': 'is_deleted'
                },
            ]
            table_html = render_generic_table(
                items,
                columns,
                title="لیست متخصصان",
                actions=actions,
                model_name="psychologist",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),      # ← اضافه شد
                filter_form=render_filter_form(filter_fields, request),  # ← اضافه شد
                pagination=render_pagination(current_page, total_pages, f"&q={query}" if query else ""),
                breadcrumb=breadcrumb
            )

            context = {
                'content': mark_safe(table_html),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/manager'),
                'extra_css': [
                    '/static/js/table-data.js',
                    '/static/plugins/switcher/css/switcher.css',
                    '/static/plugins/gallery/css/picture.css',
                ],
                'extra_js': [
                    '/static/plugins/switcher/js/switcher.js',
                    '/static/plugins/gallery/js/picture.js',
                ],
                
            }
            
            return render(request, 'index1.html', context)

        if action == 'detail':
            queryset = Psychologist.objects.all().exclude(is_deleted=True).select_related('profile')
            search_fields = []
            filter_fields = {}
            queryset, query = apply_search(queryset, request, search_fields)
            queryset = apply_filters(queryset, request, filter_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل مدیریت</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست متخصصان</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """
            
            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)
            columns = [
                {
                    'field': 'profile__first_name',
                    'title': 'نام و نام خانوادگی',
                    'display': lambda obj: '''
                        <a href="/management/psychologist/detail/{pk}/" 
                        class="btn btn-info btn-pill"
                        target="_blanck"
                        >
                            {full_name}
                        </a>
                    '''.format(
                        pk=getattr(obj, 'pk', getattr(obj, 'id', '')),
                        full_name=f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip() or '—'
                    )
                },
                {'field': 'PsychologistType', 'title': 'عنوان'},
                {
                    'field': 'is_active',
                    'title': 'وضعیت',
                    'display': {
                        'type': 'toggle',
                        'app': 'accounts',
                        'model': 'Psychologist',
                        'title': 'وضعیت',
                        'confirm': 'تغییر وضعیت',
                        'extra_class': ''
                    }
                },
            ]
            actions = [
                {
                    'type': 'edit',
                    'url': '/management/psychologist/edit/{pk}/'
                },
                {
                    'type': 'delete',
                    'app': 'accounts',
                    'model': 'Psychologist',
                    'field': 'is_deleted'
                },
            ]
            table_html = render_generic_table(
                items,
                columns,
                title="لیست متخصصان",
                actions=actions,
                model_name="psychologist",
                extra_context={'per_page': per_page},
                pagination=render_pagination(current_page, total_pages, f"&q={query}" if query else ""),
                breadcrumb=breadcrumb
            )

            context = {
                'content': mark_safe(table_html),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/manager'),
                'extra_css': [
                    '/static/js/table-data.js',
                    '/static/plugins/switcher/css/switcher.css',
                    '/static/plugins/gallery/css/picture.css',
                ],
                'extra_js': [
                    '/static/plugins/switcher/js/switcher.js',
                    '/static/plugins/gallery/js/picture.js',
                ],
                
            }
            
            return render(request, 'index1.html', context)



        return super().get(request, subject, action, **kwargs)
    



class SecretaryManagementView(BaseManagementView):
    
    def get(self, request, subject=None, action=None, **kwargs):
        
        if action == 'list':
            queryset = Secretary.objects.all().select_related('profile')
            search_fields = [
                'profile__first_name',
                'profile__last_name',
                # اگر می‌خواهید جستجوی ترکیبی هم بهتر کار کند (اختیاری)
                # 'profile__first_name__icontains', 'profile__last_name__icontains'
            ]
            filter_fields = {
                'is_active': {
                    'label': 'وضعیت',
                    'type': 'boolean',
                    'choices': [('', 'همه'), ('True', 'فعال'), ('False', 'غیرفعال')]
                },
            }
            queryset, query = apply_search(queryset, request, search_fields)
            queryset = apply_filters(queryset, request, filter_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل مدیریت</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست منشی‌ها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """
            
            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)
            columns = [
                {
                    'field': 'profile__first_name',
                    'title': 'نام و نام خانوادگی',
                    'display': lambda obj: f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip()
                },
                {'field': 'PsychologistType', 'title': 'عنوان'},
                {
                    'field': 'is_active', 
                    'title': 'وضعیت',
                    'display': lambda x: '<span class="badge bg-success">فعال</span>' if x else '<span class="badge bg-danger">غیرفعال</span>'
                },
            ]
            actions = [
                {'title': 'جزئیات', 'url': '/management/psychologist/detail/{pk}/', 'class': 'btn-info'},
            ]
            table_html = render_generic_table(
                items,
                columns,
                title="لیست منشی",
                actions=actions,
                model_name="psychologist",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),    
                filter_form=render_filter_form(filter_fields, request),
                pagination=render_pagination(current_page, total_pages, f"&q={query}" if query else ""),
                breadcrumb=breadcrumb
            )

            context = {
                'content': mark_safe(table_html),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/manager'),
                'extra_js': ['/static/js/table-data.js'],
            }
            
            return render(request, 'index1.html', context)

        return super().get(request, subject, action, **kwargs)














class RoleManagementView(BaseManagementView):
    
    def get(self, request, subject=None, action=None, pk=None ,**kwargs):
        
        if action == 'list':
            queryset = Role.objects.all()
            search_fields = [
                'name',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل مدیریت</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست متخصصان</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """
            
            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)
            columns = [
                {
                    'field': 'profile__first_name',
                    'title': 'نام و نام خانوادگی',
                    'display': lambda obj: '''
                        <a href="/management/psychologist/detail/{pk}/" 
                        class="btn btn-info btn-pill"
                        target="_blanck"
                        >
                            {full_name}
                        </a>
                    '''.format(
                        pk=getattr(obj, 'pk', getattr(obj, 'id', '')),
                        full_name=f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip() or '—'
                    )
                },
                {'field': 'PsychologistType', 'title': 'عنوان'},
                {
                    'field': 'is_active',
                    'title': 'وضعیت',
                    'display': {
                        'type': 'toggle',
                        'app': 'accounts',
                        'model': 'Psychologist',
                        'title': 'وضعیت',
                        'confirm': 'تغییر وضعیت',
                        'extra_class': ''
                    }
                },
            ]
            actions = [
                {
                    'type': 'edit',
                    'url': '/management/psychologist/edit/{pk}/'
                },
                {
                    'type': 'delete',
                    'app': 'accounts',
                    'model': 'Psychologist',
                    'field': 'is_deleted'
                },
            ]
            table_html = render_generic_table(
                items,
                columns,
                title="لیست متخصصان",
                actions=actions,
                model_name="psychologist",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),      # ← اضافه شد
                pagination=render_pagination(current_page, total_pages, f"&q={query}" if query else ""),
                breadcrumb=breadcrumb
            )

            context = {
                'content': mark_safe(table_html),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/manager'),
                'extra_css': [
                    '/static/js/table-data.js',
                    '/static/plugins/switcher/css/switcher.css',
                    '/static/plugins/gallery/css/picture.css',
                ],
                'extra_js': [
                    '/static/plugins/switcher/js/switcher.js',
                    '/static/plugins/gallery/js/picture.js',
                ],
                
            }
            
            return render(request, 'index1.html', context)

        if action == 'detail':
            psychologist=Psychologist.objects.get(profile_id=pk)
            
            template_string = """
                {% load jdate %}
                <div class="main-content with-sidebar">
                    
                    <div class="side-app">

                        <div class="main-container container-fluid">
                            <div class="page-header">
                                <ol class="breadcrumb">
                                    <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                    <li class="breadcrumb-item"><a href="/dashboard/user"><i class="fe fe-grid ml-1"></i>داشبورد</a></li>
                                    <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="fe fe-grid ml-1"></i>پنل مدیریت</a></li>
                                    <li class="breadcrumb-item"><a href="/management/psychologist/list/"><i class="fe fe-grid ml-1"></i>لیست متخصصان</a></li>
                                    <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-face ml-1"></i>{{psychologist.profile.first_name}} {{psychologist.profile.last_name}}</li>
                                    <li class="breadcrumb-back">
                                        <a href="/management/psychologist/list/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                    </li>
                                </ol>
                            </div>
                        </div>
                    </div>
                </div>
                
            """

            t = Template(template_string)
            content = t.render(Context({
                'psychologist':psychologist,
            }))

            context = {
                'content': mark_safe(content),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/manager'),
                'extra_css': [
                    '/static/plugins/switcher/css/switcher.css',
                ],
                'extra_js': [
                    '/static/plugins/switcher/js/switcher.js',
                ],
            }
            
            return render(request, 'index1.html', context)



        return super().get(request, subject, action, **kwargs)
