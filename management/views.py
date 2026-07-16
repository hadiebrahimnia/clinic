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
from core.jalali import *
from accounts.models import *
from appointment.models import *
from django.urls import reverse
from .forms import *
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
        'specialty':'management.views.SpecialtyManagementView',
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
                {
                    'field': 'profile_picture',
                    'title': 'تصویر پروفایل',
                    'display': lambda obj: '''
                        <a href="javascript:void(0)" 
                            onclick="showImageModal('{url}')"
                            class="d-inline-block">
                            <img 
                                class="img-responsive br-5 img-zoom shadow-sm"
                                src="{url}"
                                alt="{full_name}"
                                style="width: 55px; height: 55px; object-fit: cover; cursor: pointer; border: 2px solid #f1f1f1;"
                                onerror="this.src='/static/images/default-avatar.png';"
                            >
                        </a>
                    '''.format(
                        url=obj.profile_picture.url if getattr(obj, 'profile_picture', None) else '/static/images/default-avatar.png',
                        full_name=f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip() or 'متخصص'
                    )
                },
                {'field': 'PsychologistType', 'title': 'عنوان'},
                {
                    'field': 'hire_date',
                    'title': 'تاریخ استخدام',
                    'display': lambda obj: '''
                        <span class="text-nowrap" dir="ltr">
                            {}
                        </span>
                    '''.format(
                        gregorian_to_jalali(obj.hire_date) if obj.hire_date else '—'
                    )
                },
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
                # {
                #     'type': 'edit',
                #     'url': '/management/psychologist/edit/{pk}/'
                # },
                {
                    'type': 'delete',
                    'app': 'accounts',
                    'model': 'Psychologist',
                    'field': 'is_deleted',
                    'title': lambda obj: (
                        f'{getattr(obj.profile, "first_name", "")} '
                        f'{getattr(obj.profile, "last_name", "")}'
                    ).strip() or 'متخصص',
                },
            ]
            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست متخصصان",
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
            psychologistspecialties=PsychologistSpecialtie.objects.filter().exclude(is_deleted=True)
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
                            {% if psychologistspecialties %}
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h3 class="card-title">زمینه کاری</h3>
                                        </div>
                                        <div class="card-body ">
                                            <div class="accordion" id="psychologistspecialties">
                                                {% for psychologistspecialtie in  psychologistspecialties %}
                                                    
                                                    <div class="accordion-item">
                                                        <div class="row">
                                                            <div class="col-md-1 col-2 px-0 py-3">
                                                                <div class="toggle_div" style="justify-content: left;">
                                                                    <button 
                                                                        type="button" 
                                                                        class="toggle toggle-sm status-switch {% if psychologistspecialtie.is_active %}active{% endif %}" 
                                                                        data-app="accounts" 
                                                                        data-model="PsychologistSpecialtie" 
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
                                                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_psychologistspecialtie_{{psychologistspecialtie.id}}" aria-expanded="false" aria-controls="collapse_psychologistspecialtie_{{psychologistspecialtie.id}}">
                                                                        زمینه کاری
                                                                    </button>
                                                                </h2>
                                                            </div>
                                                        </div>
                                                        <div id="collapse_psychologistspecialtie_{{psychologistspecialtie.id}}" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#accordionExample" style="">
                                                            <div class="accordion-body">
                                                                <div class="card-body bg-aliceblue">
                                                                    <div class="tags">
                                                                        {% for ps in psychologistspecialties %}
                                                                            {% if ps.psychologist_id == psychologist.id %}   <!-- فقط تخصص‌های همین روانشناس -->
                                                                                {% for specialty in ps.specialties.all %}
                                                                                    <span class="tag tag-radius" style="background:{{ specialty.background_color }};color:{{ specialty.color }};border: 2px solid {{ specialty.color }};">
                                                                                        {% if specialty.icon%}
                                                                                            <span>
                                                                                                <img class="avatar brround avatar-md me-2 my-1" alt="avatra-img" src="/media/{{specialty.icon}}" style=" height: 17px; width: 17px">
                                                                                            </span>
                                                                                        {% endif %}
                                                                                        {{ specialty.name }}
                                                                                    </span>
                                                                                {% endfor %}
                                                                            {% endif %}
                                                                        {% endfor %}
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
                                                                <div class="card-body bg-aliceblue">
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
                                                                <div class="card-body bg-aliceblue">
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

                            {% if psychologistsections %}
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h3 class="card-title">بیوگرافی</h3>
                                        </div>
                                        <div class="card-body">
                                            <div class="accordion" id="psychologistsections">
                                                {% for psychologistsection in  psychologistsections %}
                                                    <div class="accordion-item">
                                                        <div class="row">
                                                            <div class="col-md-1 col-2 px-0 py-3">
                                                                <div class="toggle_div" style="justify-content: left;">
                                                                    <button 
                                                                        type="button" 
                                                                        class="toggle toggle-sm status-switch {% if psychologistsection.is_active %}active{% endif %}" 
                                                                        data-app="accounts" 
                                                                        data-model="PsychologistSection" 
                                                                        data-id="{{psychologistsection.id}}" 
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
                                                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_psychologistsection_{{psychologistsection.id}}" aria-expanded="false" aria-controls="collapse_psychologistsection_{{psychologistsection.id}}">
                                                                        {{psychologistsection.section_type}}
                                                                    </button>
                                                                </h2>
                                                            </div>
                                                        </div>
                                                        <div id="collapse_psychologistsection_{{psychologistsection.id}}" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#accordionExample" style="">
                                                            <div class="accordion-body">
                                                                <div class="card-body bg-aliceblue">
                                                                    <div class="visitor-list">
                                                                        <!-- Section Type -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-tag"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistsection.section_type %}
                                                                                    <h5 class="mb-1">{{ psychologistsection.section_type.title }}</h5>
                                                                                {% else %}
                                                                                    <cite class="text-muted">ثبت نشده</cite> 
                                                                                {% endif %}
                                                                                <p class="text-muted mb-0">نوع بخش</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistsection.display_config.section_type %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistSection"
                                                                                        data-id="{{ psychologistsection.id }}"
                                                                                        data-field="section_type"
                                                                                        data-title="نمایش نوع بخش"
                                                                                        data-confirm="نوع بخش">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- Description -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-align-right"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistsection.description %}
                                                                                    <div class="card card-collapsed mb-0 col-md-8 shadow-0 p-0 bg-aliceblue">
                                                                                        <a href="javascript:void(0)" class="card-options-collapse" data-bs-toggle="card-collapse">
                                                                                            <div class="card-header pr-0 py-0">
                                                                                                <h3 class="card-title text-dark">مشاهده</h3>
                                                                                                <div class="card-options">
                                                                                                    <a href="javascript:void(0)" class="card-options-collapse" data-bs-toggle="card-collapse"><i class="fe fe-chevron-up"></i></a>
                                                                                                </div>
                                                                                            </div>
                                                                                        </a>
                                                                                        <div class="card-body">
                                                                                            {{ psychologistsection.description|safe }}
                                                                                        </div>
                                                                                    </div>
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
                                                                                        {% if psychologistsection.display_config.description %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistSection"
                                                                                        data-id="{{ psychologistsection.id }}"
                                                                                        data-field="description"
                                                                                        data-title="نمایش توضیحات"
                                                                                        data-confirm="توضیحات">
                                                                                        <span class="thumb"></span>
                                                                                    </button>
                                                                                </div>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- Order -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="mdi mdi-numeric"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistsection.order is not None %}
                                                                                    <h5 class="mb-1">{{ psychologistsection.order }}</h5>
                                                                                {% else %}
                                                                                    <cite class="text-muted">ثبت نشده</cite> 
                                                                                {% endif %}
                                                                                <p class="text-muted mb-0">ترتیب نمایش</p>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- Background Color -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="ri ri-paint-brush-fill"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                <div style="background-color: {{ psychologistsection.background_color }}; width: 60px; height: 30px; border: 1px solid #ddd; border-radius: 4px;"></div>
                                                                                <p class="text-muted mb-0">رنگ زمینه</p>
                                                                            </div>
                                                                        </div>
                                                                        <hr class="hr">

                                                                        <!-- Text Color -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-font"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                <div style="background-color: {{ psychologistsection.color }}; color: white; width: 60px; height: 30px; border: 1px solid #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px;"></div>
                                                                                <p class="text-muted mb-0">رنگ متن</p>
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

                            {% if psychologistsocialmedias %}
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h3 class="card-title">شبکه اجتماعی</h3>
                                        </div>
                                        <div class="card-body">
                                            <div class="accordion" id="psychologistsocialmedias">
                                                {% for psychologistsocialmedia in  psychologistsocialmedias %}
                                                    <div class="accordion-item">
                                                        <div class="row">
                                                            <div class="col-md-1 col-2 px-0 py-3">
                                                                <div class="toggle_div" style="justify-content: left;">
                                                                    <button 
                                                                        type="button" 
                                                                        class="toggle toggle-sm status-switch {% if psychologistsocialmedia.is_active %}active{% endif %}" 
                                                                        data-app="accounts" 
                                                                        data-model="PsychologistSocialMedia" 
                                                                        data-id="{{psychologistsocialmedia.id}}" 
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
                                                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_psychologistsocialmedia_{{psychologistsocialmedia.id}}" aria-expanded="false" aria-controls="collapse_psychologistsocialmedia_{{psychologistsocialmedia.id}}">
                                                                        {{psychologistsocialmedia.platform.title}}
                                                                    </button>
                                                                </h2>
                                                            </div>
                                                        </div>

                                                        <div id="collapse_psychologistsocialmedia_{{psychologistsocialmedia.id}}" class="accordion-collapse collapse" aria-labelledby="headingOne" data-bs-parent="#accordionExample" style="">
                                                            <div class="accordion-body">
                                                                <div class="card-body bg-aliceblue">
                                                                    <div class="visitor-list">
                                                                        <!-- URL -->
                                                                        <div class="row my-5 align-items-center">
                                                                            <div class="col-md-1 col-2 text-center">
                                                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                    <i class="fa fa-link"></i>
                                                                                </span>                                                        
                                                                            </div>
                                                                            <div class="col-md-8 col-5 px-0">
                                                                                {% if psychologistsocialmedia.url %}
                                                                                    <h5 class="mb-1 text-break">
                                                                                        <a href="{{ psychologistsocialmedia.url }}" target="_blank" class="text-primary">
                                                                                            {{ psychologistsocialmedia.url }}
                                                                                        </a>
                                                                                    </h5>
                                                                                {% else %}
                                                                                    <cite class="text-muted">ثبت نشده</cite> 
                                                                                {% endif %}
                                                                                <p class="text-muted mb-0">آدرس لینک</p>
                                                                            </div>
                                                                            <div class="col-md-3 col-5 px-0">
                                                                                <div class="toggle_div">
                                                                                    <span class="custom-switch-description">نمایش به کاربران</span>
                                                                                    <button
                                                                                        type="button"
                                                                                        class="toggle toggle-sm status-switch disabled
                                                                                        {% if psychologistsocialmedia.display_config.url %}active{% endif %}"
                                                                                        data-app="accounts" 
                                                                                        data-model="PsychologistSocialMedia"
                                                                                        data-id="{{ psychologistsocialmedia.id }}"
                                                                                        data-field="url"
                                                                                        data-title="نمایش لینک"
                                                                                        data-confirm="لینک شبکه اجتماعی">
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
                'psychologistspecialties':psychologistspecialties,
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
            queryset = Secretary.objects.all().exclude(is_deleted=True).select_related('profile')
            search_fields = [
                'profile__first_name',
                'profile__last_name',
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
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست منشی</li>
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
                        <button 
                            class="btn btn-info btn-pill disabled"
                        >
                            {full_name}
                        </button >
                    '''.format(
                        pk=getattr(obj, 'pk', getattr(obj, 'id', '')),
                        full_name=f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip() or '—'
                    )
                },
                {
                    'field': 'profile_picture',
                    'title': 'تصویر پروفایل',
                    'display': lambda obj: '''
                        <a href="javascript:void(0)" 
                            onclick="showImageModal('{url}')"
                            class="d-inline-block">
                            <img 
                                class="img-responsive br-5 img-zoom shadow-sm"
                                src="{url}"
                                alt="{full_name}"
                                style="width: 55px; height: 55px; object-fit: cover; cursor: pointer; border: 2px solid #f1f1f1;"
                                onerror="this.src='/static/images/default-avatar.png';"
                            >
                        </a>
                    '''.format(
                        url=obj.profile_picture.url if getattr(obj, 'profile_picture', None) else '/static/images/default-avatar.png',
                        full_name=f"{getattr(obj.profile, 'first_name', '')} {getattr(obj.profile, 'last_name', '')}".strip() or 'متخصص'
                    )
                },
                {'field': 'employee_code', 'title': 'کد استخدام'},
                {
                    'field': 'hire_date',
                    'title': 'تاریخ استخدام',
                    'display': lambda obj: '''
                        <span class="text-nowrap" dir="ltr">
                            {}
                        </span>
                    '''.format(
                        gregorian_to_jalali(obj.hire_date) if obj.hire_date else '—'
                    )
                },
                {
                    'field': 'is_active',
                    'title': 'وضعیت',
                    'display': {
                        'type': 'toggle',
                        'app': 'accounts',
                        'model': 'Secretary',
                        'field': 'is_active',
                        'title': lambda obj: (
                            f'{getattr(obj.profile, "first_name", "")} '
                            f'{getattr(obj.profile, "last_name", "")}'
                        ).strip() or 'منشی',
                        'confirm': 'تغییر وضعیت',
                        'extra_class': ''
                    }
                },
            ]
            actions = [
                # {
                #     'type': 'edit',
                #     'url': '/management/psychologist/edit/{pk}/'
                # },
                {
                    'type': 'delete',
                    'app': 'accounts',
                    'model': 'Secretary',
                    'field': 'is_deleted',
                    'title': lambda obj: (
                        f'{getattr(obj.profile, "first_name", "")} '
                        f'{getattr(obj.profile, "last_name", "")}'
                    ).strip() or 'منشی',
                },
            ]
            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست منشی",
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
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست نقش‌ها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """
            
            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)
            columns = [
                {
                    'field': 'name',
                    'title': 'نام',
                    'display': lambda obj: '''
                        <a 
                            class="btn btn-info btn-pill disabled col-4"
                        >
                            {name}
                        </a>
                    '''.format(
                        pk=getattr(obj, 'pk', getattr(obj, 'id', '')),
                        name=f"{getattr(obj, 'name', '')}".strip() or '—'
                    )
                },
                
            ]
            actions = [
                {
                    'type': 'edit',
                    'url': '/management/role/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'accounts',
                #     'model': 'Role',
                #     'field': 'is_deleted'
                # },
            ]
            header_actions=[
                {
                    "type": "create",
                    "title": "افزودن نقش",
                    "url": "/management/role/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },

                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/accounts/role/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]
            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست نقش‌ها",
                actions=actions,
                header_actions=header_actions,
                model_name="psychologist",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = RoleForm()
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت نقش',
                'back_url': '/management/role/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('management-action', kwargs={'subject': 'role', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)

        elif action == 'update':
            role = get_object_or_404(Role, pk=pk)
            form = RoleForm(instance=role)
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش نقش',
                'back_url': '/management/role/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'role', 'action': 'update' , 'pk': role.pk }),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):
        if action == 'create':
            form = RoleForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "مدرک با موفقیت ثبت شد.")
                return redirect('management-action', subject='role', action='list')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }

                base_context.update({
                    'title': 'ثبت نقش',
                    'back_url': 'management/role/list',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action':reverse('management-action', kwargs={'subject': 'role','action': 'create'}),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block',
                    'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                    'footer_content': ''
                })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            role = get_object_or_404(Role, pk=pk)
            form = RoleForm(request.POST, request.FILES, instance=role)

            if form.is_valid():
                form.save()
                messages.success(request, "مدرک با موفقیت ویرایش شد.")
                return redirect('management-action', subject='role', action='list')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }

                base_context.update({
                    'title': 'ویرایش نقش ',
                    'back_url': '/management/role/list',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('management-action-detail', kwargs={'subject': 'role','action': 'update', 'pk': role.pk }),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block',
                    'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                    'footer_content': ''
                })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")




class CountryManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = Country.objects.all()
            search_fields = [
                'name',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست کشورها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام',
                    'display': lambda obj: '''
                        <a class="btn btn-info btn-pill disabled col-4">
                            {name}
                        </a>
                    '''.format(
                        name=f"{getattr(obj, 'name', '')}".strip() or '—'
                    )
                },
                {
                    'field': 'icon',
                    'title': 'آیکون',
                    'display': lambda obj: getattr(obj, 'icon', '') or '—'
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/country/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'Country',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن کشور",
                    "url": "/management/country/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/accounts/country/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست کشورها",
                actions=actions,
                header_actions=header_actions,
                model_name="country",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = CountryForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت کشور',
                'back_url': '/management/country/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'country', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            country = get_object_or_404(Country, pk=pk)
            form = CountryForm(instance=country)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش کشور',
                'back_url': '/management/country/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action-detail',
                    kwargs={
                        'subject': 'country',
                        'action': 'update',
                        'pk': country.pk
                    }
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = CountryForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "کشور با موفقیت ثبت شد.")
                return redirect('management-action', subject='country', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت کشور',
                'back_url': '/management/country/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action',
                    kwargs={
                        'subject': 'country',
                        'action': 'create'
                    }
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            country = get_object_or_404(Country, pk=pk)
            form = CountryForm(request.POST, request.FILES, instance=country)

            if form.is_valid():
                form.save()
                messages.success(request, "کشور با موفقیت ویرایش شد.")
                return redirect('management-action', subject='country', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش کشور',
                'back_url': '/management/country/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action-detail',
                    kwargs={
                        'subject': 'country',
                        'action': 'update',
                        'pk': country.pk
                    }
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")




class ProvinceManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = Province.objects.select_related('country').all()
            search_fields = [
                'name',
                'country__name',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست استان‌ها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام استان',
                    'display': lambda obj: '''
                        <a class="btn btn-info btn-pill disabled col-4">
                            {name}
                        </a>
                    '''.format(
                        name=f"{getattr(obj, 'name', '')}".strip() or '—'
                    )
                },
                {
                    'field': 'country',
                    'title': 'کشور',
                    'display': lambda obj: getattr(obj.country, 'name', '—')
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/province/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'Province',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن استان",
                    "url": "/management/province/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/province/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست استان‌ها",
                actions=actions,
                header_actions=header_actions,
                model_name="province",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = ProvinceForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت استان',
                'back_url': '/management/province/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'province', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            province = get_object_or_404(Province, pk=pk)
            form = ProvinceForm(instance=province)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش استان',
                'back_url': '/management/province/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'province', 'action': 'update', 'pk': province.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = ProvinceForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "استان با موفقیت ثبت شد.")
                return redirect('management-action', subject='province', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت استان',
                'back_url': '/management/province/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'province', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            province = get_object_or_404(Province, pk=pk)
            form = ProvinceForm(request.POST, request.FILES, instance=province)

            if form.is_valid():
                form.save()
                messages.success(request, "استان با موفقیت ویرایش شد.")
                return redirect('management-action', subject='province', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش استان',
                'back_url': '/management/province/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'province', 'action': 'update', 'pk': province.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
    


class CityManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = City.objects.select_related('province', 'province__country').all()
            search_fields = [
                'name',
                'province__name',
                'province__country__name',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست شهرها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام شهر',
                    'display': lambda obj: '''
                        <a class="btn btn-info btn-pill disabled col-4">
                            {name}
                        </a>
                    '''.format(
                        name=f"{getattr(obj, 'name', '')}".strip() or '—'
                    )
                },
                {
                    'field': 'province',
                    'title': 'استان',
                    'display': lambda obj: getattr(obj.province, 'name', '—')
                },
                {
                    'field': 'country',
                    'title': 'کشور',
                    'display': lambda obj: getattr(obj.province.country, 'name', '—')
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/city/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'City',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن شهر",
                    "url": "/management/city/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/city/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست شهرها",
                actions=actions,
                header_actions=header_actions,
                model_name="city",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = CityForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت شهر',
                'back_url': '/management/city/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'city', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            city = get_object_or_404(City, pk=pk)
            form = CityForm(instance=city)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش شهر',
                'back_url': '/management/city/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'city', 'action': 'update', 'pk': city.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = CityForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "شهر با موفقیت ثبت شد.")
                return redirect('management-action', subject='city', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت شهر',
                'back_url': '/management/city/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'city', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            city = get_object_or_404(City, pk=pk)
            form = CityForm(request.POST, request.FILES, instance=city)

            if form.is_valid():
                form.save()
                messages.success(request, "شهر با موفقیت ویرایش شد.")
                return redirect('management-action', subject='city', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش شهر',
                'back_url': '/management/city/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'city', 'action': 'update', 'pk': city.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
    

class SpecialtyManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = Specialty.objects.all()
            search_fields = [
                'name',
                'description',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست تخصص‌ها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام تخصص',
                    'display': lambda obj: f'''
                        <a class="btn btn-info btn-pill disabled">
                            {getattr(obj, 'name', '') or '—'}
                        </a>
                    '''
                },
                {
                    'field': 'icon',
                    'title': 'آیکون',
                    'display': lambda obj: f'''
                        <img src="{obj.icon.url if obj.icon else '/static/images/no-image.png'}" 
                             alt="آیکون" width="48" height="48" 
                             class="img-thumbnail" style="object-fit: contain;">
                    ''' if obj.icon else '—'
                },
                {
                    'field': 'background_color',
                    'title': 'رنگ زمینه',
                    'display': lambda obj: f'''
                        <span style="background-color: {obj.background_color}; color: {obj.color}; 
                                      padding: 6px 12px; border-radius: 50px; font-size: 13px; border: 1px solid #ddd;">
                            {obj.background_color}
                        </span>
                    '''
                },
                {
                    'field': 'color',
                    'title': 'رنگ متن',
                    'display': lambda obj: f'''
                        <span style="background-color: {obj.color}; color: white; 
                                      padding: 6px 12px; border-radius: 50px; font-size: 13px;">
                            {obj.color}
                        </span>
                    '''
                },
                {
                    'field': 'description',
                    'title': 'توضیحات',
                    'display': lambda obj: (str(obj.description)[:80] + '...') if obj.description else '—'
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/specialty/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'Specialty',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن تخصص",
                    "url": "/management/specialty/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/specialty/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست تخصص‌ها",
                actions=actions,
                header_actions=header_actions,
                model_name="specialty",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = SpecialtyForm()

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت تخصص جدید',
                'back_url': '/management/specialty/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'specialty', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            specialty = get_object_or_404(Specialty, pk=pk)
            form = SpecialtyForm(instance=specialty)

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش تخصص',
                'back_url': '/management/specialty/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'specialty', 'action': 'update', 'pk': specialty.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = SpecialtyForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "تخصص با موفقیت ثبت شد.")
                return redirect('management-action', subject='specialty', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت تخصص جدید',
                'back_url': '/management/specialty/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'specialty', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            specialty = get_object_or_404(Specialty, pk=pk)
            form = SpecialtyForm(request.POST, request.FILES, instance=specialty)

            if form.is_valid():
                form.save()
                messages.success(request, "تخصص با موفقیت ویرایش شد.")
                return redirect('management-action', subject='specialty', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش تخصص',
                'back_url': '/management/specialty/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'specialty', 'action': 'update', 'pk': specialty.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
    

class UniversityManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = University.objects.select_related('city', 'city__province', 'city__province__country').all()
            search_fields = [
                'name',
                'city__name',
                'city__province__name',
                'city__province__country__name',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست دانشگاه‌ها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام دانشگاه',
                    'display': lambda obj: '''
                        <a class="btn btn-info btn-pill disabled">
                            {name}
                        </a>
                    '''.format(
                        name=getattr(obj, 'name', '') or '—'
                    )
                },
                {
                    'field': 'icon',
                    'title': 'آیکون',
                    'display': lambda obj: f'''
                        <img src="{obj.icon.url if obj.icon else '/static/images/no-image.png'}" 
                             alt="آیکون" width="48" height="48" 
                             class="img-thumbnail" style="object-fit: contain;">
                    ''' if obj.icon else '—'
                },
                {
                    'field': 'city',
                    'title': 'شهر',
                    'display': lambda obj: getattr(obj.city, 'name', '—')
                },
                {
                    'field': 'province',
                    'title': 'استان',
                    'display': lambda obj: getattr(obj.city.province, 'name', '—') if obj.city and hasattr(obj.city, 'province') else '—'
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/university/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'University',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن دانشگاه",
                    "url": "/management/university/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/university/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست دانشگاه‌ها",
                actions=actions,
                header_actions=header_actions,
                model_name="university",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = UniversityForm()

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت دانشگاه جدید',
                'back_url': '/management/university/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'university', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            university = get_object_or_404(University, pk=pk)
            form = UniversityForm(instance=university)

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش دانشگاه',
                'back_url': '/management/university/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'university', 'action': 'update', 'pk': university.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = UniversityForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "دانشگاه با موفقیت ثبت شد.")
                return redirect('management-action', subject='university', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت دانشگاه جدید',
                'back_url': '/management/university/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'university', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            university = get_object_or_404(University, pk=pk)
            form = UniversityForm(request.POST, request.FILES, instance=university)

            if form.is_valid():
                form.save()
                messages.success(request, "دانشگاه با موفقیت ویرایش شد.")
                return redirect('management-action', subject='university', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش دانشگاه',
                'back_url': '/management/university/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'university', 'action': 'update', 'pk': university.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
    


class FieldOfStudyManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = FieldOfStudy.objects.all()

            search_fields = [
                'name',
                'description',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست رشته‌های تحصیلی</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(
                queryset,
                request,
                per_page=15
            )

            columns = [
                {
                    'field': 'name',
                    'title': 'نام رشته',
                    'display': lambda obj: f"{obj.name}"
                },
                # {
                #     'field': 'description',
                #     'title': 'توضیحات',
                #     'display': lambda obj: (
                #         strip_tags(obj.description)[:120] + "..."
                #         if obj.description and len(strip_tags(obj.description)) > 120
                #         else strip_tags(obj.description or "—")
                #     )
                # },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/fieldofstudy/update/{pk}/'
                },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن رشته تحصیلی",
                    "url": "/management/field-of-study/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست رشته‌های تحصیلی",
                actions=actions,
                header_actions=header_actions,
                model_name="field_of_study",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
                pagination=render_pagination(
                    current_page,
                    total_pages,
                    f"&q={query}" if query else ""
                ),
                breadcrumb=breadcrumb
            )

            context = {
                'content': mark_safe(table_html),
                'sidebar_menu': self.get_sidebar_menu(
                    request,
                    active_section='/dashboard/manager'
                ),
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

        elif action == 'create':

            form = FieldOfStudyForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت رشته تحصیلی',
                'back_url': '/management/field-of-study/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action',
                    kwargs={'subject': 'field-of-study', 'action': 'create'}
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_style': 'background-color: #1ab0fc;color:#fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':

            field_of_study = get_object_or_404(FieldOfStudy, pk=pk)
            form = FieldOfStudyForm(instance=field_of_study)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش رشته تحصیلی',
                'back_url': '/management/field-of-study/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action-detail',
                    kwargs={
                        'subject': 'field-of-study',
                        'action': 'update',
                        'pk': field_of_study.pk
                    }
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'submit_style': '',
                'card_header_style': 'background-color: #1ab0fc;color:#fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':

            form = FieldOfStudyForm(request.POST)

            if form.is_valid():
                form.save()
                messages.success(request, "رشته تحصیلی با موفقیت ثبت شد.")
                return redirect(
                    'management-action',
                    subject='field-of-study',
                    action='list'
                )

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت رشته تحصیلی',
                'back_url': '/management/field-of-study/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action',
                    kwargs={'subject': 'field-of-study', 'action': 'create'}
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc;color:#fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':

            field_of_study = get_object_or_404(FieldOfStudy, pk=pk)
            form = FieldOfStudyForm(
                request.POST,
                instance=field_of_study
            )

            if form.is_valid():
                form.save()
                messages.success(request, "رشته تحصیلی با موفقیت ویرایش شد.")
                return redirect(
                    'management-action',
                    subject='field-of-study',
                    action='list'
                )

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش رشته تحصیلی',
                'back_url': '/management/field-of-study/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse(
                    'management-action-detail',
                    kwargs={
                        'subject': 'field-of-study',
                        'action': 'update',
                        'pk': field_of_study.pk
                    }
                ),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc;color:#fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")



class SpecializationManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = Specialization.objects.select_related('field').all()
            search_fields = [
                'name',
                'field__name',           # فرض بر این است که FieldOfStudy فیلد name دارد
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست گرایش‌های تحصیلی</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام گرایش',
                    'display': lambda obj: f'''
                        <span class="badge bg-info fs-6">
                            {getattr(obj, 'name', '') or '—'}
                        </span>
                    '''
                },
                {
                    'field': 'field',
                    'title': 'رشته تحصیلی',
                    'display': lambda obj: getattr(obj.field, 'name', '—')
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/specialization/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'Specialization',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن گرایش",
                    "url": "/management/specialization/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/specialization/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست گرایش‌های تحصیلی",
                actions=actions,
                header_actions=header_actions,
                model_name="specialization",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = SpecializationForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت گرایش جدید',
                'back_url': '/management/specialization/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'specialization', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            specialization = get_object_or_404(Specialization, pk=pk)
            form = SpecializationForm(instance=specialization)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش گرایش',
                'back_url': '/management/specialization/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'specialization', 'action': 'update', 'pk': specialization.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = SpecializationForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "گرایش تحصیلی با موفقیت ثبت شد.")
                return redirect('management-action', subject='specialization', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت گرایش جدید',
                'back_url': '/management/specialization/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'specialization', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            specialization = get_object_or_404(Specialization, pk=pk)
            form = SpecializationForm(request.POST, request.FILES, instance=specialization)

            if form.is_valid():
                form.save()
                messages.success(request, "گرایش تحصیلی با موفقیت ویرایش شد.")
                return redirect('management-action', subject='specialization', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش گرایش',
                'back_url': '/management/specialization/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'specialization', 'action': 'update', 'pk': specialization.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")




class PsychologistTypeManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = PsychologistType.objects.all()
            search_fields = [
                'name',
                'description',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست انواع متخصص</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'name',
                    'title': 'نام نوع متخصص',
                    'display': lambda obj: '''
                        <a class="btn btn-info btn-pill disabled">
                            {name}
                        </a>
                    '''.format(
                        name=getattr(obj, 'name', '') or '—'
                    )
                },
                {
                    'field': 'icon',
                    'title': 'آیکون',
                    'display': lambda obj: f'''
                        <img src="{obj.icon.url if obj.icon else '/static/images/no-image.png'}" 
                             alt="آیکون" width="48" height="48" 
                             class="img-thumbnail" style="object-fit: contain;">
                    ''' if obj.icon else '—'
                },
                {
                    'field': 'description',
                    'title': 'توضیحات',
                    'display': lambda obj: (str(obj.description)[:100] + '...') if obj.description else '—'
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/psychologisttype/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'PsychologistType',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن نوع متخصص",
                    "url": "/management/psychologisttype/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/psychologisttype/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست انواع متخصص",
                actions=actions,
                header_actions=header_actions,
                model_name="psychologisttype",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = PsychologistTypeForm()

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت نوع متخصص جدید',
                'back_url': '/management/psychologisttype/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'psychologisttype', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            psychologist_type = get_object_or_404(PsychologistType, pk=pk)
            form = PsychologistTypeForm(instance=psychologist_type)

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش نوع متخصص',
                'back_url': '/management/psychologisttype/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'psychologisttype', 'action': 'update', 'pk': psychologist_type.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = PsychologistTypeForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "نوع متخصص با موفقیت ثبت شد.")
                return redirect('management-action', subject='psychologisttype', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت نوع متخصص جدید',
                'back_url': '/management/psychologisttype/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'psychologisttype', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            psychologist_type = get_object_or_404(PsychologistType, pk=pk)
            form = PsychologistTypeForm(request.POST, request.FILES, instance=psychologist_type)

            if form.is_valid():
                form.save()
                messages.success(request, "نوع متخصص با موفقیت ویرایش شد.")
                return redirect('management-action', subject='psychologisttype', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش نوع متخصص',
                'back_url': '/management/psychologisttype/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'psychologisttype', 'action': 'update', 'pk': psychologist_type.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")



class SectionTypeManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = SectionType.objects.all()
            search_fields = ['title']
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست انواع بخش</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'title',
                    'title': 'عنوان بخش',
                    'display': lambda obj: f'''
                        <span class="badge bg-primary fs-6">
                            {getattr(obj, 'title', '') or '—'}
                        </span>
                    '''
                },
                {
                    'field': 'icon',
                    'title': 'آیکون',
                    'display': lambda obj: f'''
                        <img src="{obj.icon.url if obj.icon else '/static/images/no-image.png'}" 
                             alt="آیکون" width="48" height="48" 
                             class="img-thumbnail" style="object-fit: contain;">
                    ''' if obj.icon else '—'
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/sectiontype/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'SectionType',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن نوع بخش",
                    "url": "/management/sectiontype/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/sectiontype/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست انواع بخش",
                actions=actions,
                header_actions=header_actions,
                model_name="sectiontype",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = SectionTypeForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت نوع بخش جدید',
                'back_url': '/management/sectiontype/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'sectiontype', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            section_type = get_object_or_404(SectionType, pk=pk)
            form = SectionTypeForm(instance=section_type)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش نوع بخش',
                'back_url': '/management/sectiontype/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'sectiontype', 'action': 'update', 'pk': section_type.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = SectionTypeForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "نوع بخش با موفقیت ثبت شد.")
                return redirect('management-action', subject='sectiontype', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت نوع بخش جدید',
                'back_url': '/management/sectiontype/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'sectiontype', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            section_type = get_object_or_404(SectionType, pk=pk)
            form = SectionTypeForm(request.POST, request.FILES, instance=section_type)

            if form.is_valid():
                form.save()
                messages.success(request, "نوع بخش با موفقیت ویرایش شد.")
                return redirect('management-action', subject='sectiontype', action='list')

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش نوع بخش',
                'back_url': '/management/sectiontype/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'sectiontype', 'action': 'update', 'pk': section_type.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
    



class PlatformManagementView(BaseManagementView):

    def get(self, request, subject=None, action=None, pk=None, **kwargs):

        if action == 'list':
            queryset = Platform.objects.all()
            search_fields = [
                'title',
                'url',
            ]
            queryset, query = apply_search(queryset, request, search_fields)

            breadcrumb = """
                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد </a></li>
                <li class="breadcrumb-item"><a href="/dashboard/manager"><i class="ri ri-user-settings-fill ml-1"></i>پنل ادمین</a></li>
                <li class="breadcrumb-item text-dark"><i class="fa fa-list ml-1 rotate-180"></i>لیست پلتفرم‌ها</li>
                <li class="breadcrumb-back">
                    <a href="/dashboard/user/" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                </li>
            """

            items, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)

            columns = [
                {
                    'field': 'title',
                    'title': 'عنوان پلتفرم',
                    'display': lambda obj: f'''
                        <span class="badge bg-primary fs-6">
                            {getattr(obj, 'title', '') or '—'}
                        </span>
                    '''
                },
                {
                    'field': 'url',
                    'title': 'پیشوند آدرس',
                    'display': lambda obj: f'''
                        <code class="text-dark">{getattr(obj, 'url', '') or '—'}</code>
                    '''
                },
                {
                    'field': 'icon',
                    'title': 'آیکون',
                    'display': lambda obj: f'''
                        <img src="{obj.icon.url if obj.icon else '/static/images/no-image.png'}" 
                             alt="آیکون" width="48" height="48" 
                             class="img-thumbnail" style="object-fit: contain;">
                    ''' if obj.icon else '—'
                },
            ]

            actions = [
                {
                    'type': 'edit',
                    'url': '/management/platform/update/{pk}/'
                },
                # {
                #     'type': 'delete',
                #     'app': 'your_app',
                #     'model': 'Platform',
                #     'field': 'is_deleted'
                # },
            ]

            header_actions = [
                {
                    "type": "create",
                    "title": "افزودن پلتفرم",
                    "url": "/management/platform/create/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                },
                {
                    "type": "create",
                    "title": "افزودن فایل",
                    "url": "/json/platform/",
                    "icon": "fe fe-plus",
                    "class": "btn btn-success"
                }
            ]

            table_html = render_generic_table(
                items,
                columns,
                table_title="لیست پلتفرم‌ها",
                actions=actions,
                header_actions=header_actions,
                model_name="platform",
                extra_context={'per_page': per_page},
                search_form=render_search_form(query),
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

        elif action == 'create':
            form = PlatformForm()

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت پلتفرم جدید',
                'back_url': '/management/platform/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'platform', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            platform = get_object_or_404(Platform, pk=pk)
            form = PlatformForm(instance=platform)

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش پلتفرم',
                'back_url': '/management/platform/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'platform', 'action': 'update', 'pk': platform.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk=None):

        if action == 'create':
            form = PlatformForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, "پلتفرم با موفقیت ثبت شد.")
                return redirect('management-action', subject='platform', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت پلتفرم جدید',
                'back_url': '/management/platform/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action', kwargs={'subject': 'platform', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            platform = get_object_or_404(Platform, pk=pk)
            form = PlatformForm(request.POST, request.FILES, instance=platform)

            if form.is_valid():
                form.save()
                messages.success(request, "پلتفرم با موفقیت ویرایش شد.")
                return redirect('management-action', subject='platform', action='list')

            base_context = {
                'col_class': 'col-md-6 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش پلتفرم',
                'back_url': '/management/platform/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('management-action-detail', kwargs={'subject': 'platform', 'action': 'update', 'pk': platform.pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")