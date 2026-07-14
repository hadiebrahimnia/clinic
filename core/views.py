# core/views.py
from django.apps import apps
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.http import Http404, HttpResponseNotAllowed
from django.core.exceptions import PermissionDenied
from .errors import _error_response  # درست ایمپورت شد
from django.shortcuts import render, get_object_or_404
import json
import importlib
from django.http import JsonResponse
from accounts.models import *
from appointment.models import *
from core.utils import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.template import Template, Context
import logging
logger = logging.getLogger(__name__)


class DynamicBooleanView(PermissionRequiredMixin, View):
    def get_permission_required(self):
        return []
    def post(self, request, app_label=None, model_name=None, field=None, pk=None, **kwargs):
        if not all([app_label, model_name, field, pk]):
            return JsonResponse({"success": False, "message": "پارامترها ناقص است."}, status=400)
        try:
            ModelClass = apps.get_model(app_label, model_name)
            obj = get_object_or_404(ModelClass, pk=pk)
        except LookupError:
            return JsonResponse({"success": False, "message": "مدل یافت نشد."}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)

        # === پشتیبانی از display_config ===
        if hasattr(obj, 'toggle_visibility') and field in obj.CONTROLLABLE_FIELDS:
            try:
                new_value = obj.toggle_visibility(field)
                action = "فعال" if new_value else "غیرفعال"

                return JsonResponse({
                    "success": True,
                    "message": f"نمایش {field} برای {obj} {action} شد.",
                    "new_value": new_value,
                    "field": field
                })
            except Exception as e:
                return JsonResponse({"success": False, "message": str(e)}, status=500)

        # === fallback برای فیلدهای معمولی boolean ===
        if not hasattr(obj, field):
            return JsonResponse({"success": False, "message": f"فیلد {field} وجود ندارد."}, status=400)

        current_value = getattr(obj, field)
        if not isinstance(current_value, bool):
            return JsonResponse({"success": False, "message": "فیلد boolean نیست."}, status=400)

        new_value = not current_value
        setattr(obj, field, new_value)
        obj.save(update_fields=[field])

        return JsonResponse({
            "success": True,
            "message": f"{field} با موفقیت تغییر کرد.",
            "new_value": new_value,
            "field": field
        })
        

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # فقط متخصصان فعال و غیرحذف‌شده
        psychologists = Psychologist.objects.filter(
            is_active=True, 
            is_deleted=False
        ).select_related(
            'profile', 
            'profile__city', 
            'profile__city__province', 
            'profile__city__province__country'
            ) \
        .prefetch_related(
            'degrees__specialization', 
            'degrees__university', 
            'specialties', 
        )

        psychologists_list = []

        for psych in psychologists:
            # degrees = []
            # for degree in psych.degrees.all():
            #     degrees.append({
            #         'level': degree.get_level_display(),
            #         'specialization': degree.specialization.name if degree.specialization else None,
            #         'university': degree.university.name if degree.university else None,
            #         'graduation_year': degree.graduation_year,
            #     })


            psych_dict = {
                'id': psych.id,
                'full_name': f"{psych.profile.get_full_name() or psych.profile.username}",
                'PsychologistType':psych.PsychologistType,
                'username': psych.profile.username,
                'profile_picture': psych.profile_picture.url if psych.profile_picture else None,
                'location': {
                    'city': psych.profile.city.name if psych.profile.city else None,
                    'province': psych.profile.city.province.name if psych.profile.city and psych.profile.city.province else None,
                    'country': psych.profile.city.province.country.name if psych.profile.city and psych.profile.city.province and psych.profile.city.province.country else None,
                } if psych.profile.city else None,
                'contact': {
                    'phone': psych.profile.phone_number,
                    'email': psych.profile.email,
                }
            }

            psychologists_list.append(psych_dict)

        context['psychologists'] = psychologists_list
        return context


class FormView(View):
    def get(self, request):
        return render(request, 'form.html')
    

class DynamicDashboardView(View):
    ROUTES = {
        'user': 'core.views.DashboardUserView',
        'manager': 'core.views.DashboardManagerView',
        'psychologist': 'core.views.DashboardPsychologistView',
        'secretary': 'core.views.DashboardSecretaryView',
        'admin': 'core.views.DashboardAdminView',
        'colleague':'core.views.DashboardColleagueView',
    }

    def dispatch(self, request, subject):
        if subject not in self.ROUTES:
            return _error_response(request, 404, "OOPS! صفحه یافت نشد", "موضوع درخواستی پشتیبانی نمی‌شود.")

        try:
            module_path, view_name = self.ROUTES[subject].rsplit('.', 1)
            module = importlib.import_module(module_path)
            view_class = getattr(module, view_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Dynamic view import failed for {subject}: {e}")
            return _error_response(request, 500, "خطای سرور", "ویوی مورد نظر یافت نشد.")

        try:
            view = view_class.as_view()
            return view(request, subject=subject)

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
        
class DynamicEntityView(View):
    ROUTES = {
        # psychologist
        'psychologist': 'accounts.views.PsychologistActionView',
        'psychologistspecialties': 'accounts.views.PsychologistSpecialtiesView',
        'psychologistdocument': 'accounts.views.PsychologistDocumentView',
        'psychologistdegree': 'accounts.views.PsychologistDegreeView',
        'psychologistsection': 'accounts.views.PsychologistSectionView',
        'psychologistsocialmedia': 'accounts.views.PsychologistSocialMediaView',
        # secretary
        'secretary':'accounts.views.SecretaryActionView',

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
        


class BaseDashboardView(LoginRequiredMixin, View):
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


class DashboardUserView(BaseDashboardView):

    def get(self, request, **kwargs):
        try:
            psychologist = Psychologist.objects.get(profile=request.user)
        except Psychologist.DoesNotExist:
            psychologist = None

        try:
            workschedules = WorkSchedule.objects.filter(psychologist=psychologist)
        except WorkSchedule.DoesNotExist:
            workschedules = None    


        template_string = """
            <div class="main-content with-sidebar">
                <div class="side-app">
                    <div class="main-container container-fluid">
                        <div class="page-header">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</li>
                                <li class="breadcrumb-back">
                                    <a href="/" class="text-gray fs-6">بازگشت
                                        <i class="mdi mdi-arrow-left-thick"></i>
                                    </a>
                                </li>
                            </ol>
                        </div>
                        <!-- محتوای داشبورد کاربر -->
                        <div class="row">

                            <div class="col-md-6 col-xl-4">
                                <a
                                    href="#"
                                    class="card card-custom"
                                    style="
                                    --front-gradient: linear-gradient(
                                        135deg,
                                        #667eea 0%,
                                        #764ba2 100%
                                    );
                                    --back-gradient: linear-gradient(
                                        135deg,
                                        #ff6b6b 0%,
                                        #ee5a24 100%
                                    );
                                    ">
                                    <div class="card-front img-card">
                                    <div class="floating-particles"></div>
                                    <div class="card-body">
                                        <div>
                                        <i class="fa fa-list-alt text-white fs-30"></i>
                                        </div>
                                        <div class="text-white">
                                        <h2 style="margin: 0">نوبت‌های من</h2>
                                        </div>
                                    </div>
                                    </div>

                                    <div class="card-back">
                                    <div class="card-body">
                                        <p class="back-text">
                                        لیست نوبت‌های رزور شده را از این قسمت مشاهده نمایید
                                        </p>
                                    </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-md-6 col-xl-4">
                                <a
                                    href="#"
                                    class="card card-custom"
                                    style="
                                    --front-gradient: linear-gradient(
                                        135deg,
                                        #4facfe 0%,
                                        #00f2fe 100%
                                    );
                                    --back-gradient: linear-gradient(
                                        135deg,
                                        #43e97b 0%,
                                        #38f9d7 100%
                                    );
                                    ">
                                    <div class="card-front img-card">
                                    <div class="floating-particles"></div>
                                    <div class="card-body">
                                        <div>
                                        <i class="fa fa-list-ol text-white fs-30"></i>
                                        </div>
                                        <div class="text-white">
                                        <h2 style="margin: 0">نتایج من</h2>
                                        </div>
                                    </div>
                                    </div>

                                    <div class="card-back">
                                    <div class="card-body">
                                        <p class="back-text">
                                        لیست نتایج آزمون های تکمیل شده توسط شما را از این قسمت مشاهده
                                        نمایید
                                        </p>
                                    </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-md-6 col-xl-4">
                                <a
                                    href="/accounts/update"
                                    class="card card-custom"
                                    style="
                                    --front-gradient: linear-gradient(
                                        135deg,
                                        #f5cac3 0%,
                                        #f28482 100%
                                    );
                                    --back-gradient: linear-gradient(
                                        135deg,
                                        #84a59d 0%,
                                        #bdb8b0 100%
                                    );
                                    ">
                                    <div class="card-front img-card">
                                    <div class="floating-particles"></div>
                                    <div class="card-body">
                                        <div>
                                        <i class="fa fa-handshake-o text-white fs-30"></i>
                                        </div>
                                        <div class="text-white">
                                        <h2 style="margin: 0">ویرایش پروفایل</h2>
                                        </div>
                                    </div>
                                    </div>

                                    <div class="card-back">
                                    <div class="card-body">
                                        <p class="back-text">در صورتی که قصد تغییر اطلاعات را دارید از این قسمت اقدام نمایید</p>
                                    </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-md-6 col-xl-4">
                                <a
                                    href="#"
                                    class="card card-custom"
                                    style="
                                    --front-gradient: linear-gradient(
                                        135deg,
                                        #fa709a 0%,
                                        #fee140 100%
                                    );
                                    --back-gradient: linear-gradient(
                                        135deg,
                                        #a8edea 0%,
                                        #fed6e3 100%
                                    );
                                    ">
                                    <div class="card-front img-card">
                                    <div class="floating-particles"></div>
                                    <div class="card-body">
                                        <div>
                                        <i class="fa fa-handshake-o text-white fs-30"></i>
                                        </div>
                                        <div class="text-white">
                                        <h2 style="margin: 0">درخواست همکاری</h2>
                                        </div>
                                    </div>
                                    </div>

                                    <div class="card-back">
                                    <div class="card-body">
                                        <p class="back-text">در صورت تمایل به همکاری با کلینیک عرفان ثبت نام نمایید</p>
                                    </div>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """

        # رندر کردن تمپلیت
        t = Template(template_string)
        content = t.render(Context({
            'psychologist': psychologist,
            'workschedules': workschedules,
        }))

        context = {
            'content': mark_safe(content),
            'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/user'),
            'extra_css': [],
            'extra_js': [],
        }

        return render(request, 'index1.html', context)


class DashboardManagerView(BaseDashboardView):

    def get(self, request, **kwargs):
        psychologist = Psychologist.objects.get(profile=request.user)
        workschedules = WorkSchedule.objects.filter(psychologist=psychologist)
        template_string = """
            <div class="main-content with-sidebar">
                <div class="side-app">
                    <div class="main-container container-fluid">
                        <div class="page-header">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                <li class="breadcrumb-item"><a href="/dashboard/user"><i class="fe fe-grid ml-1"></i>داشبورد</a></li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="ri ri-user-settings-fill ml-1"></i>پنل مدیریت</li>
                                <li class="breadcrumb-back">
                                        <a href="/dashboard/user" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                </li>
                            </ol>
                        </div>
                        <div class="row">
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/psychologist/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2"> متخصصان</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-success-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-success text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">منشی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """

        # رندر کردن تمپلیت
        t = Template(template_string)
        content = t.render(Context({
            'psychologist': psychologist,
            'workschedules': workschedules,
        }))

        context = {
            'content': mark_safe(content),
            'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/manager'),
            'extra_css': [],
            'extra_js': [],
        }

        return render(request, 'index1.html', context)


class DashboardPsychologistView(BaseDashboardView):
    
    def get(self, request, **kwargs):
        psychologist = Psychologist.objects.get(profile=request.user)
        workschedules = WorkSchedule.objects.filter(psychologist=psychologist)

        template_string = """
            <div class="main-content with-sidebar">
                <div class="side-app">
                    <div class="main-container container-fluid">
                        <div class="page-header">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-stethoscope ml-1"></i>پنل متخصص</li>
                            </ol>
                        </div>
                        
                        <div class="row">
                            <!-- کارت پروفایل -->
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/psychologist/update/{{ psychologist.id }}" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">پروفایل</h2>
                                                <h5 class="fw-normal mb-0">ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <!-- بقیه کارت‌ها (فعلاً لینک خالی) -->
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/psychologistspecialties/update/{{ psychologist.id }}" class="btn btn-success-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-success text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">زمینه کاری</h2>
                                                <h5 class="fw-normal mb-0">ثبت و ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/psychologistdocument/list" class="btn btn-warning-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-warning text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">مدارک</h2>
                                                <h5 class="fw-normal mb-0">ثبت و ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/psychologistdegree/list" class="btn btn-cyan-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-cyan text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">مدارک تحصیلی</h2>
                                                <h5 class="fw-normal mb-0">ثبت و ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/psychologistsection/list" class="btn btn-secondary-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-secondary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">بیوگرافی</h2>
                                                <h5 class="fw-normal mb-0">ثبت و ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/psychologistsocialmedia/list" class="btn btn-danger-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-danger text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">شبکه اجتماعی</h2>
                                                <h5 class="fw-normal mb-0">ثبت و ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                        </div>

                        <!-- بخش روزهای کاری -->
                        <div class="row">
                            <div class="col-md-6 col-xl-4">
                                <div class="card">
                                    <div class="card-header border-bottom">
                                        <h5 class="card-title">روزهای کاری</h5>
                                    </div>
                                    <div class="card-alert alert alert-danger mb-0">
                                        روزهای کاری منحصرا توسط کلینیک ثبت می‌گردد
                                    </div>
                                    <div class="card-body">
                                        {% for schedule in workschedules %}
                                        <div class="clearfix row mb-4">
                                            <div class="col">
                                                <div class="float-start">
                                                    <h5 class="mb-0">{{ schedule.day|default:"روز نامشخص" }}</h5>
                                                </div>
                                            </div>
                                            <div class="col">
                                                <div class="float-end">
                                                    <h5 class="mb-0 text-muted">
                                                        {{ schedule.start_time|time:"H:i" }} - {{ schedule.end_time|time:"H:i" }}
                                                    </h5>
                                                </div>
                                            </div>
                                        </div>
                                        {% empty %}
                                        <p class="text-muted text-center py-4">هنوز برنامه کاری ثبت نشده است.</p>
                                        {% endfor %}
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        """

        # رندر کردن تمپلیت
        t = Template(template_string)
        content = t.render(Context({
            'psychologist': psychologist,
            'workschedules': workschedules,
        }))

        context = {
            'content': mark_safe(content),
            'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/psychologist'),
            'extra_css': [],
            'extra_js': [],
        }

        return render(request, 'index1.html', context)


class DashboardSecretaryView(BaseDashboardView):
    
    def get(self, request, **kwargs):
        secretary = Secretary.objects.get(profile=request.user)
        template_string = """
            <div class="main-content with-sidebar">
                <div class="side-app">
                    <div class="main-container container-fluid">
                        <div class="page-header">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="ti ti-microphone ml-1"></i>پنل منشی</li>
                            </ol>
                        </div>
                        
                        <div class="row">
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/secretary/update/{{ secretary.id }}" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">پروفایل</h2>
                                                <h5 class="fw-normal mb-0">ویرایش</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        """

        # رندر کردن تمپلیت
        t = Template(template_string)
        content = t.render(Context({
            'secretary': secretary,
        }))

        context = {
            'content': mark_safe(content),
            'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/secretary'),
            'extra_css': [],
            'extra_js': [],
        }

        return render(request, 'index1.html', context)
    

class DashboardAdminView(BaseDashboardView):
    def get(self, request, subject=None, **kwargs):
        content = """
            <div class="main-content with-sidebar">
                <div class="side-app">
                    <div class="main-container container-fluid">
                        <div class="page-header">
                            <ol class="breadcrumb">
                                <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</li>
                                <li class="breadcrumb-item text-dark" aria-current="page"><i class="ri ri-admin-fill ml-1"></i>پنل ادمین</li>
                            </ol>
                        </div>

                        <div class="row">
                            <div class="col-12 mb-5">
                                <div class="alert alert-primary" role="alert">
                                    اطلاعات کاربران  
                                </div>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/progile/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2"> کاربران</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/psychologist/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2"> متخصصان</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">پذیرش مراجع</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">روزهای کاری متخصصین</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">مدارک متخصصین</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">زمینه کاری متخصصین</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>


                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">مدارک تحصیلی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">بیوگرافی متخصصین</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">شبکه‌های اجتماعی متخصصین</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-info-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-primary text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">منشی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-12 mb-5 mt-5">
                                <div class="alert alert-success" role="alert">
                                    اطلاعات کلینیک  
                                </div>
                             </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/progile/list" class="btn btn-success-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-success text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2"> اتاق‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/psychologist/list" class="btn btn-success-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-success text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2"> نوع جلسات</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-success-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-success text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">روزهای کاری</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-success-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-success text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">نوبت‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-12 mb-5 mt-5">
                                <div class="alert alert-warning" role="alert">
                                    اطلاعات آزمون‌ها  
                                </div>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/progile/list" class="btn btn-warning-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-warning text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2"> آزمون‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/psychologist/list" class="btn btn-warning-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-warning text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">ویژگی‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/secretary/list" class="btn btn-warning-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-warning text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">نتایج</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                        </div>

                         <div class="row">
                            <div class="col-12 mb-5 mt-5">
                                <div class="alert alert-danger" role="alert">
                                    تاریخچه  
                                </div>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/management/progile/list" class="btn btn-danger-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-danger text-center align-self-center box-primary-shadow bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30  text-white mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">تاریخچه تفییرات</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-12 mb-5 mt-5">
                                <div class="alert alert-default" role="alert">
                                    اطلاعات عمومی
                                </div>
                            </div>
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">نقش‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>
                            
                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">کشور</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">استان</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">شهر</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">تخصص‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">دانشگاه‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">رشته تحصیلی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>


                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">گرایش‌های تحصیلی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">نوع تخصص ‌ها</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">زمینه‌های کاری</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">بخش‌های بیوگرافی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-sm-6 col-lg-6 col-md-12 col-xl-4 mb-5">
                                <a href="/" class="btn btn-default-light col-12 p-0">
                                    <div class="row">
                                        <div class="col-4">
                                            <div class="card-img-absolute circle-icon bg-default text-center align-self-center bradius">
                                                <img src="/static/images/svgs/circle.svg" alt="img" class="card-img-absolute">
                                                <i class="lnr lnr-user fs-30 text-dark mt-4"></i>
                                            </div>
                                        </div>
                                        <div class="col-8">
                                            <div class="card-body">
                                                <h2 class="mb-2 fw-normal mt-2">شبکه‌های اجتماعی</h2>
                                                <h5 class="fw-normal mb-0">لیست</h5>
                                            </div>
                                        </div>
                                    </div>
                                </a>
                            </div>


                        </div>
                    </div>
                </div>
            </div>
        """

        context = {
            'content': content,
            'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/admin'),
            'extra_css': [],
            'extra_js': [],
        }
        return render(request, 'index1.html', context)





class DashboardColleagueView(BaseDashboardView):
    def get(self, request, subject=None, **kwargs):
        content = """


            <div class="page" style="background-image: linear-gradient(90deg, #756fd2, #3ca9ce);">
                <div class="page-content error-page error2 text-white">
                    <div class="container text-center">
                        <div class="error-template">
                            
                            <div class="row">

                            <div class="col-md-6 col-xl-6">
                                <a
                                    href="/psychologist/register"
                                    class="card card-custom"
                                    style="
                                    --front-gradient: linear-gradient(
                                        135deg,
                                        #03045e 0%,
                                        #023e8a 100%
                                    );
                                    --back-gradient: linear-gradient(
                                        135deg,
                                        #ade8f4 0%,
                                        #caf0f8 100%
                                    );
                                    ">
                                    <div class="card-front img-card">
                                    <div class="floating-particles"></div>
                                    <div class="card-body">
                                        <div>
                                        <i class="mdi mdi-stethoscope text-white fs-30"></i>
                                        </div>
                                        <div class="text-white">
                                        <h2 style="margin: 0">ثبت‌نام مـــــتخصص</h2>
                                        </div>
                                    </div>
                                    </div>

                                    <div class="card-back">
                                    <div class="card-body">
                                        <p class="back-text text-dark">
                                        در صورتی که متخصص این کلینیک هستید از این قسمت وارد شوید
                                        </p>
                                    </div>
                                    </div>
                                </a>
                            </div>

                            <div class="col-md-6 col-xl-6">
                                <a
                                    href="/secretary/register"
                                    class="card card-custom"
                                    style="
                                    --front-gradient: linear-gradient(
                                        135deg,
                                        #03045e 0%,
                                        #023e8a 100%
                                    );
                                    --back-gradient: linear-gradient(
                                        135deg,
                                        #ade8f4 0%,
                                        #caf0f8 100%
                                    );
                                    ">
                                    <div class="card-front img-card">
                                    <div class="floating-particles"></div>
                                    <div class="card-body">
                                        <div>
                                        <i class="ti ti-microphone text-white fs-30"></i>
                                        </div>
                                        <div class="text-white">
                                        <h2 style="margin: 0">ثبت‌نام مـــــــنشی</h2>
                                        </div>
                                    </div>
                                    </div>

                                    <div class="card-back">
                                    <div class="card-body">
                                        <p class="back-text text-dark">
                                        در صورتی که منشی این کلینیک هستید از این قسمت وارد شوید
                                        </p>
                                    </div>
                                    </div>
                                </a>
                            </div>
                           
                        </div>

                            <div class="text-center">
                                <a class="btn btn-secondary mt-5 mb-5" href="/dashboard/user">
                                    بازگشت به داشبورد  
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            
        """

        context = {
            'content': content,
            'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/admin'),
            'extra_css': [],
            'extra_js': [],
        }
        return render(request, 'index3.html', context)
