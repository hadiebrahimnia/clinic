# core/views.py
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.http import Http404, HttpResponseNotAllowed
from django.core.exceptions import PermissionDenied
from .errors import _error_response  # درست ایمپورت شد
import json
import importlib
import logging
from accounts.models import *
logger = logging.getLogger(__name__)

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
             'degrees__field', 
             'degrees__specialization', 
             'degrees__university', 
            'specialties', 
            'social_media'
        )

        psychologists_list = []

        for psych in psychologists:
            # جمع‌آوری مدارک تحصیلی
            degrees = []
            for degree in psych.degrees.all():
                degrees.append({
                    'level': degree.get_level_display(),
                    'field': degree.field.name,
                    'specialization': degree.specialization.name if degree.specialization else None,
                    'university': degree.university.name if degree.university else None,
                    'graduation_year': degree.graduation_year,
                })

            # جمع‌آوری شبکه‌های اجتماعی
            social_media = []
            for sm in psych.social_media.all():
                social_media.append({
                    'platform': sm.get_platform_display(),
                    'url': sm.url,
                })

            # جمع‌آوری تخصص‌ها
            specialties = [spec.name for spec in psych.specialties.all()]

            # ساخت دیکشنری کامل برای این متخصص
            psych_dict = {
                'id': psych.id,
                'full_name': f"{psych.profile.get_full_name() or psych.profile.username}",
                'PsychologistType':psych.PsychologistType,
                'username': psych.profile.username,
                'profile_picture': psych.profile_picture.url if psych.profile_picture else None,
                'banner_image': psych.banner_image.url if psych.banner_image else None,
                'bio': psych.bio or "بیوگرافی در دسترس نیست.",
                'start_date': psych.start_date_Psychology.strftime('%Y-%m-%d') if psych.start_date_Psychology else None,
                'is_accepting_new_patients': psych.is_accepting_new_patients,
                'specialties': specialties,
                'degrees': degrees,
                'social_media': social_media,
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

class DashboardView(View):
    def get(self, request):

        messages.add_message(
            request,
            messages.SUCCESS,
            '  خوش آمدید !',
            extra_tags=json.dumps({
                "title":"پیام",
                "style": 'success',
                "size": "medium",
                "duration": 3000,
                "location": "top-right",
                "fixed": False
            })
        )

        content = """
        <div class="main-content with-sidebar">
            <div class="side-app with_header">
                <div class="main-container container-fluid">
                <div class="page-header">
                    <ol class="breadcrumb">
                    <li class="breadcrumb-item">
                        <a href="/"> <i class="mdi mdi-home"></i>خانه </a>
                    </li>
                    <li class="breadcrumb-item text-dark" aria-current="page">
                        <i class="mdi mdi-view-dashboard"></i>داشبورد
                    </li>
                    <li class="breadcrumb-back">
                        <a href="/" class="btn btn-outline-default fw-900"
                        >بازگشت
                        <i class="mdi mdi-arrow-left-thick"></i>
                        </a>
                    </li>
                    </ol>
                </div>
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
                            <i class="fa fa-user-o text-white fs-30"></i>
                            </div>
                            <div class="text-white">
                            <h2 style="margin: 0">لیست نوبت‌ها</h2>
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
                            <i class="fa fa-user-o text-white fs-30"></i>
                            </div>
                            <div class="text-white">
                            <h2 style="margin: 0">لیست نتایج</h2>
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
                            <i class="fa fa-user-o text-white fs-30"></i>
                            </div>
                            <div class="text-white">
                            <h2 style="margin: 0">عنوان</h2>
                            </div>
                        </div>
                        </div>

                        <div class="card-back">
                        <div class="card-body">
                            <p class="back-text">پشت کارت ۳</p>
                        </div>
                        </div>
                    </a>
                    </div>
                </div>
                </div>
            </div>
        </div>


        """
        
        extra_css = [
            
        ]
        
        extra_js = [
        ]


        sidebar1= [
            {
                'title': 'اصلی',
                'items': [
                    {'label': 'داشبورد', 'url': '/dashboard', 'icon': 'fe fe-home', 'is_active': True},
                ]
            },
            {
                'title': 'فرعی',
                'items': [
                    {'label': 'ادمین', 'url': '/administrator', 'icon': 'fe fe-user', 'is_active': False},
                ]
            },
        ]
        context = {
            'sidebar_menu': [
                {
                    'title': 'اصلی',
                    'items': [
                        {'label': 'داشبورد', 'url': '/dashboard', 'icon': 'fe fe-home ', 'is_active': True},
                    ]
                },
                {
                    'title': 'فرعی',
                    'items': [
                        {'label': 'ادمین', 'url': '/administrator', 'icon': 'fe fe-user', 'is_active': False},
                    ]
                },
            ],
            'content': content,
            'sidebar1':sidebar1,
            'extra_css': extra_css,
            'extra_js': extra_js,
        }
        return render(request, 'index1.html', context)
    

class FormView(View):
    def get(self, request):
        return render(request, 'form.html')
    
class DynamicEntityView(View):
    ROUTES = {
        'psychologist': 'accounts.views.PsychologistActionView',
    }

    def dispatch(self, request, subject, action, pk=None):
        if subject not in self.ROUTES:
            return _error_response(request, 404, "OOPS! صفحه یافت نشد", "موضوع درخواستی پشتیبانی نمی‌شود.")

        try:
            module_path, view_name = self.ROUTES[subject].rsplit('.', 1)
            module = importlib.import_module(module_path)
            view_class = getattr(module, view_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Dynamic view import failed: {e}")
            return _error_response(request, 500, "خطای سرور", "ویوی مورد نظر یافت نشد.")

        try:
            view = view_class.as_view()
            return view(request, subject=subject, action=action, pk=pk)

        except Http404:
            return _error_response(request, 404, "صفحه یافت نشد", "آیتم مورد نظر وجود ندارد.")
        except PermissionDenied:
            return _error_response(request, 403, "دسترسی ممنوع", "شما اجازه انجام این عمل را ندارید.")
        except Exception as e:
            logger.exception(f"Unexpected error in dynamic view: {e}")
            return _error_response(request, 500, "خطای داخلی", "مشکلی رخ داده است.")