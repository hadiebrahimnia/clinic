from django.shortcuts import render, get_object_or_404 ,redirect
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
        'psychologistspecialtie': 'management.views.PsychologistSpecialtieManagementView',
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

        elif action == 'detail':
            psychologist = get_object_or_404(Psychologist, pk=pk)
            PsychologistSpecialties=PsychologistSpecialtie.objects.filter().exclude(is_deleted=True)
            psychologistdocuments=PsychologistDocument.objects.filter().exclude(is_deleted=True)
            psychologistdegrees=PsychologistDegree.objects.filter().exclude(is_deleted=True)
            psychologistsections=PsychologistSection.objects.filter().exclude(is_deleted=True)
            psychologistsocialmedias=PsychologistSocialMedia.objects.filter().exclude(is_deleted=True)
            
            template_string = """
            {% load jdate %}
            <div class="main-content with-sidebar">
                <div class="side-app">
                    <div class="main-container container-fluid">
                        <div class="page-header">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل مدیریت</a></li>
                                <li class="breadcrumb-item"><a href="/management/psychologist/list/"><i class="fa fa-list ml-1"></i>لیست متخصصان</a></li>
                                <li class="breadcrumb-item text-dark"><i class="fa fa-user ml-1"></i>{{psychologist.profile.first_name}} {{psychologist.profile.last_name}}</li>
                                <li class="breadcrumb-back">
                                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                </li>
                            </ol>
                        </div>


                        <div class="row">
                            {% if PsychologistSpecialties %}
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h3 class="card-title">زمینه کاری</h3>
                                        </div>
                                        <div class="card-body">

                                            <div class="accordion" id="PsychologistSpecialties">

                                                {% for PsychologistSpecialtie in  PsychologistSpecialties %}
                                                    <div class="accordion-item">
                                                        <div class="row">
                                                            <div class="col-md-1 col-2 px-0 py-3">
                                                                <div class="toggle_div" style="justify-content: left;">
                                                                    <button 
                                                                        type="button" 
                                                                        class="toggle toggle-sm status-switch {% if psychologistdocument.is_active %}active{% endif %}" 
                                                                        data-app="accounts" 
                                                                        data-model="PsychologistDocument" 
                                                                        data-id="{{psychologistspecialtie.id}}" 
                                                                        data-field="is_active" 
                                                                        data-title="" 
                                                                        data-confirm="فعالسازی"
                                                                        >
                                                                        <span class="thumb"></span>
                                                                    </button>
                                                                </div>

                                                            </div>

                                                            <div class="col-md-11 col-10">

                                                                <h2 class="accordion-header" id="headingOne">
                                                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_PsychologistSpecialtie_{{PsychologistSpecialtie.id}}" aria-expanded="false" aria-controls="collapse_psychologistspecialtie_{{psychologistspecialtie.id}}">
                                                                        {{psychologistdocument.get_document_type_display}}
                                                                    </button>
                                                                </h2>

                                                            </div>

                                                        </div>

                                                        

                                                        <div id="collapse_psychologistdocument_{{psychologistdocument.id}}" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#accordionExample" style="">
                                                            <div class="accordion-body">
                                                                <div class="card-body">
                                                            <div class="visitor-list">
                                                                
                                                                <div class="row my-5 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="fa fa-tag rotate-90"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.title %}
                                                                            <h5 class="mb-1">{{ psychologistdocument.title }}</h5>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                        <p class="text-muted mb-0">عنوان</p>
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.title %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="title"
                                                                                data-title="نمایش عنوان "
                                                                                data-confirm="عنوان">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">

                                                                <div class="row my-5 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="mdi mdi-numeric"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.code %}
                                                                            <h5 class="mb-1">{{ psychologistdocument.code }}</h5>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                        <p class="text-muted mb-0">کد</p>
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.code %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="code"
                                                                                data-title="نمایش کد "
                                                                                data-confirm="کد">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">

                                                                <div class="row my-3 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="fa fa-image"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.document_image %}
                                                                            <a href="javascript:void(0)" 
                                                                                onclick="showImageModal('/media/{{ psychologistdocument.document_image }}', '{{ psychologistdocument.title }}')">
                                                                                <img 
                                                                                    class="img-responsive br-5 img-zoom p-0 col-md-1 col-4"
                                                                                    src="/media/{{ psychologistdocument.document_image}}"
                                                                                    alt="{{ psychologistdocument.document_image}}"
                                                                                    style="cursor: pointer">
                                                                            </a>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.document_image %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="document_image"
                                                                                data-title="نمایش تصویر "
                                                                                data-confirm="تصویر">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">

                                                                <div class="row my-5 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="fa fa-align-right"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.description %}
                                                                            <div class="card card-collapsed mb-0 col-md-8 shadow-0 p-0 ">
                                                                                <a href="javascript:void(0)" class="card-options-collapse" data-bs-toggle="card-collapse">
                                                                                    <div class="card-header pr-0 py-0">
                                                                                        <h3 class="card-title text-dark">مشاهده</h3>
                                                                                        <div class="card-options">
                                                                                            <a href="javascript:void(0)" class="card-options-collapse" data-bs-toggle="card-collapse"><i class="fe fe-chevron-up"></i></a>
                                                                                        </div>
                                                                                    </div>
                                                                                </a>
                                                                                <div class="card-body">
                                                                                    {{ psychologistdocument.description|safe }}
                                                                                </div>
                                                                            </div>

                                                                            <h5 class="mb-1"></h5>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                        <p class="text-muted mb-0">توضیحات</p>
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.description %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="description"
                                                                                data-title="نمایش توضیحات "
                                                                                data-confirm="توضیحات">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">
                                                            </div>
                                                        </div>


                                                            
                                                            
                                                            </div>
                                                        </div>
                                                    </div>
                                                {% endfor %}

                                                
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {% endif %}

                            {% if psychologistdocuments %}
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h3 class="card-title">مدارک</h3>
                                        </div>
                                        <div class="card-body">

                                            <div class="accordion" id="psychologistdocuments">

                                                {% for psychologistdocument in  psychologistdocuments %}
                                                    <div class="accordion-item">
                                                        <div class="row">
                                                            <div class="col-md-1 col-2 px-0 py-3">
                                                                <div class="toggle_div" style="justify-content: left;">
                                                                    <button 
                                                                        type="button" 
                                                                        class="toggle toggle-sm status-switch {% if psychologistdocument.is_active %}active{% endif %}" 
                                                                        data-app="accounts" 
                                                                        data-model="PsychologistDocument" 
                                                                        data-id="{{psychologistdocument.id}}" 
                                                                        data-field="is_active" 
                                                                        data-title="" 
                                                                        data-confirm="فعالسازی"
                                                                        >
                                                                        <span class="thumb"></span>
                                                                    </button>
                                                                </div>

                                                            </div>

                                                            <div class="col-md-11 col-10">

                                                                <h2 class="accordion-header" id="headingOne">
                                                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_psychologistdocument_{{psychologistdocument.id}}" aria-expanded="false" aria-controls="collapse_psychologistdocument_{{psychologistdocument.id}}">
                                                                        {{psychologistdocument.get_document_type_display}}
                                                                    </button>
                                                                </h2>

                                                            </div>

                                                        </div>

                                                        

                                                        <div id="collapse_psychologistdocument_{{psychologistdocument.id}}" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#accordionExample" style="">
                                                            <div class="accordion-body">
                                                                <div class="card-body">
                                                            <div class="visitor-list">
                                                                
                                                                <div class="row my-5 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="fa fa-tag rotate-90"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.title %}
                                                                            <h5 class="mb-1">{{ psychologistdocument.title }}</h5>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                        <p class="text-muted mb-0">عنوان</p>
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.title %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="title"
                                                                                data-title="نمایش عنوان "
                                                                                data-confirm="عنوان">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">

                                                                <div class="row my-5 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="mdi mdi-numeric"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.code %}
                                                                            <h5 class="mb-1">{{ psychologistdocument.code }}</h5>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                        <p class="text-muted mb-0">کد</p>
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.code %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="code"
                                                                                data-title="نمایش کد "
                                                                                data-confirm="کد">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">

                                                                <div class="row my-3 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="fa fa-image"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.document_image %}
                                                                            <a href="javascript:void(0)" 
                                                                                onclick="showImageModal('/media/{{ psychologistdocument.document_image }}', '{{ psychologistdocument.title }}')">
                                                                                <img 
                                                                                    class="img-responsive br-5 img-zoom p-0 col-md-1 col-4"
                                                                                    src="/media/{{ psychologistdocument.document_image}}"
                                                                                    alt="{{ psychologistdocument.document_image}}"
                                                                                    style="cursor: pointer">
                                                                            </a>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.document_image %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="document_image"
                                                                                data-title="نمایش تصویر "
                                                                                data-confirm="تصویر">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">

                                                                <div class="row my-5 align-items-center">
                                                                    <div class="col-md-1 col-2 text-center">
                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                            <i class="fa fa-align-right"></i>
                                                                        </span>                                                        
                                                                    </div>
                                                                    <div class="col-md-8 col-5 px-0">
                                                                        {% if psychologistdocument.description %}
                                                                            <div class="card card-collapsed mb-0 col-md-8 shadow-0 p-0 ">
                                                                                <a href="javascript:void(0)" class="card-options-collapse" data-bs-toggle="card-collapse">
                                                                                    <div class="card-header pr-0 py-0">
                                                                                        <h3 class="card-title text-dark">مشاهده</h3>
                                                                                        <div class="card-options">
                                                                                            <a href="javascript:void(0)" class="card-options-collapse" data-bs-toggle="card-collapse"><i class="fe fe-chevron-up"></i></a>
                                                                                        </div>
                                                                                    </div>
                                                                                </a>
                                                                                <div class="card-body">
                                                                                    {{ psychologistdocument.description|safe }}
                                                                                </div>
                                                                            </div>

                                                                            <h5 class="mb-1"></h5>
                                                                        {% else %}
                                                                            <cite class="text-muted">ثبت نشده</cite> 
                                                                        {% endif %}
                                                                        <p class="text-muted mb-0">توضیحات</p>
                                                                    </div>
                                                                    <div class="col-md-3 col-5 px-0">
                                                                        <div class="toggle_div">
                                                                            <span class="custom-switch-description">نمایش به کاربران</span>
                                                                            <button
                                                                                type="button"
                                                                                class="toggle toggle-sm status-switch disabled
                                                                                {% if psychologistdocument.display_config.description %}active{% endif %}"
                                                                                data-app="accounts" 
                                                                                data-model="PsychologistDocument"
                                                                                data-id="{{ psychologistdocument.id }}"
                                                                                data-field="description"
                                                                                data-title="نمایش توضیحات "
                                                                                data-confirm="توضیحات">
                                                                                <span class="thumb"></span>
                                                                            </button>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <hr class="hr">
                                                            </div>
                                                        </div>


                                                            
                                                            
                                                            </div>
                                                        </div>
                                                    </div>
                                                {% endfor %}

                                                
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {% endif %}

                            {% if psychologistdegrees %}
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h3 class="card-title">مدارک تحصیلی</h3>
                                        </div>
                                        <div class="card-body">

                                            <div class="accordion" id="psychologistdegrees">

                                                {% for psychologistdegree in  psychologistdegrees %}
                                                    <div class="accordion-item">
                                                        <div class="row">
                                                            <div class="col-md-1 col-2 px-0 py-3">
                                                                <div class="toggle_div" style="justify-content: left;">
                                                                    <button 
                                                                        type="button" 
                                                                        class="toggle toggle-sm status-switch {% if psychologistdegree.is_active %}active{% endif %}" 
                                                                        data-app="accounts" 
                                                                        data-model="PsychologistDegree" 
                                                                        data-id="{{psychologistdegree.id}}" 
                                                                        data-field="is_active" 
                                                                        data-title="مدرک" 
                                                                        data-confirm="فعالسازی"
                                                                        >
                                                                        <span class="thumb"></span>
                                                                    </button>
                                                                </div>

                                                            </div>

                                                            <div class="col-md-11 col-10">

                                                                <h2 class="accordion-header" id="headingOne">
                                                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_psychologistdegree_{{psychologistdegree.id}}" aria-expanded="false" aria-controls="collapse_psychologistdegree_{{psychologistdegree.id}}">
                                                                        {{psychologistdegree.get_level_display}}
                                                                    </button>
                                                                </h2>

                                                            </div>

                                                        </div>

                                                        

                                                        <div id="collapse_psychologistdegree_{{psychologistdegree.id}}" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#accordionExample" style="">
                                                            <div class="accordion-body">                                                                
                                                                
                                                                <div class="card-body">
                                                                    <div class="visitor-list">
                                                                        
                                                                        <!-- رشته تحصیلی -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-book"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                <h5 class="mb-1">{{ psychologistdegree.specialization }}</h5>
                                                                                <p class="text-muted mb-0">رشته تحصیلی</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.specialization %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="specialization"
                                                                                        data-title="نمایش رشته تحصیلی"
                                                                                        data-confirm="رشته تحصیلی">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- دانشگاه -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                {% if psychologistdegree.university.icon %}
                                                                                    <img class="avatar brround avatar-md grayscale" src="/media/{{ psychologistdegree.university.icon }}" alt="" style="filter: grayscale(1);">
                                                                                {% else %}
                                                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                        <i class="fa fa-university"></i>
                                                                                    </span>
                                                                                {% endif %}
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                <h5 class="mb-1">{{ psychologistdegree.university }}</h5>
                                                                                <p class="text-muted mb-0">دانشگاه محل تحصیل</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.university %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="university"
                                                                                        data-title="نمایش  دانشگاه"
                                                                                        data-confirm="دانشگاه">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- معدل -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-graduation-cap"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistdegree.gpa %}
                                                                                    <h5 class="mb-1">{{ psychologistdegree.gpa }}</h5>
                                                                                {% else %}
                                                                                    <cite class="text-muted">ثبت نشده</cite> 
                                                                                {% endif %}
                                                                                <p class="text-muted mb-0">معدل</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.gpa %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="gpa"
                                                                                        data-title="نمایش معدل "
                                                                                        data-confirm="معدل">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- عنوان پایان‌نامه -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-file-text-o"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistdegree.thesis_title %}
                                                                                    <h5 class="mb-1">{{ psychologistdegree.thesis_title }}</h5>
                                                                                {% else %}
                                                                                    <cite class="text-muted">ثبت نشده</cite> 
                                                                                {% endif %}
                                                                                <p class="text-muted mb-0">عنوان پایان‌نامه</p>
                                                                            </div>

                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.thesis_title %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="thesis_title"
                                                                                        data-title="نمایش  پایان نامه "
                                                                                        data-confirm="پایان نامه ">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>

                                                                        </div>
                                                                        <hr class="hr">
                                                                        
                                                                        
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-calendar"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                
                                                                                <h5 class="mb-1">{{ psychologistdegree.start_year|to_jalali_date }}</h5>
                                                                                <p class="text-muted mb-0">تاریخ شروع تحصیل</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.start_year %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="start_year"
                                                                                        data-title="نمایش سال شروع "
                                                                                        data-confirm="سال شروع">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                            
                                                                        </div>
                                                                        <hr class="hr">
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-calendar"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                <h5 class="mb-1">{{ psychologistdegree.graduation_year|to_jalali_date }}</h5>
                                                                                <p class="text-muted mb-0">تاریخ پایان تحصیل</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.graduation_year %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="graduation_year"
                                                                                        data-title="نمایش سال پایان "
                                                                                        data-confirm="سال پایان">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>

                                                                        </div>

                                                                        <hr class="hr">
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-image"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistdegree.degree_file %}
                                                                                    <a href="javascript:void(0)" 
                                                                                        onclick="showImageModal('/media/{{ psychologistdegree.degree_file }}', '{{ psychologistdegree.get_level_display }}')">
                                                                                        <img 
                                                                                            class="img-responsive br-5 img-zoom p-0 col-md-1 col-4"
                                                                                            src="/media/{{ psychologistdegree.degree_file}}"
                                                                                            alt="{{ psychologistdegree.degree_file}}"
                                                                                            style="cursor: pointer">
                                                                                    </a>
                                                                                {% else %}
                                                                                    <cite class="text-muted">ثبت نشده</cite> 
                                                                                {% endif %}
                                                                            </div>

                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistdegree.display_config.degree_file %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistDegree"
                                                                                        data-id="{{ psychologistdegree.id }}"
                                                                                        data-field="degree_file"
                                                                                        data-title="نمایش مدرک تحصیلی "
                                                                                        data-confirm="مدرک تحصیلی">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>

                                                                    </div>
                                                                </div>

                                                            
                                                            
                                                            </div>
                                                        </div>


                                                    </div>
                                                {% endfor %}

                                                
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {% endif %}




                        </div>
                    </div>
                </div>
            </div>
                
            """
            t = Template(template_string)
            content = t.render(Context({
                'psychologist':psychologist,
                'psychologistdocuments':psychologistdocuments,
                'psychologistdegrees':psychologistdegrees,
                'PsychologistSpecialties':PsychologistSpecialties,
                'psychologistsections':psychologistsections,
                'psychologistsocialmedias':psychologistsocialmedias,
            }))


            context = {
                'content': mark_safe(content),
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
