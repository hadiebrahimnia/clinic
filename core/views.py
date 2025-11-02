# core/views.py
from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.http import Http404, HttpResponseNotAllowed
from django.core.exceptions import PermissionDenied
from .errors import _error_response  # درست ایمپورت شد
import json
import importlib
import logging
logger = logging.getLogger(__name__)

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

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