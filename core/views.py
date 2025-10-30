from django.shortcuts import render
from django.views import View
from django.contrib import messages
import json

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
        
        <!--app-content open-->
        <div class="main-content app-content mt-0">
          <div class="side-app">
            <!-- CONTAINER -->
            <div class="main-container container-fluid">
              <!-- PAGE-HEADER -->
              <div class="page-header">
                  <ol class="breadcrumb">
                    <li class="breadcrumb-item">
                      <a href="/">
                        <i class="mdi mdi-home"></i>خانه
                        </a>
                    </li>
                    <li class="breadcrumb-item text-dark" aria-current="page">
                        <i class="mdi mdi-view-dashboard"></i>داشبورد
                    </li>
                    <li class="breadcrumb-back">
                        <a href="/" class="btn btn-outline-default fw-900">بازگشت
                            <i class="mdi mdi-arrow-left-thick"></i>
                        </a>
                    </li>
                  </ol>
              </div>
              <!-- PAGE-HEADER END -->
                <div class="row">
                
                    <div class="col-md-6 col-xl-4">
                        <a href="#" class="card card-custom" style="
                            --front-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            --back-gradient: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                        ">
                            <!-- FRONT SIDE -->
                            <div class="card-front img-card">
                                <div class="floating-particles"></div>
                                <div class="card-body">
                                    <div> 
                                        <i class="fa fa-user-o text-white fs-30" ></i> 
                                    </div>
                                    <div class="text-white">
                                        <h2 style="margin: 0;">لیست نوبت‌ها</h2>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- BACK SIDE -->
                            <div class="card-back">
                                <div class="card-body">
                                    <p class="back-text">لیست نوبت‌های رزور شده را از این قسمت مشاهده نمایید</p>
                                </div>
                            </div>
                        </a>
                    </div>

                    <div class="col-md-6 col-xl-4">
                        <a href="#" class="card card-custom" style="
                            --front-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                            --back-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                        ">
                            <!-- FRONT SIDE -->
                            <div class="card-front img-card">
                                <div class="floating-particles"></div>
                                <div class="card-body">
                                    <div> 
                                        <i class="fa fa-user-o text-white fs-30" ></i> 
                                    </div>
                                    <div class="text-white">
                                        <h2 style="margin: 0;">لیست نتایج</h2>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- BACK SIDE -->
                            <div class="card-back">
                                <div class="card-body">
                                    <p class="back-text">لیست نتایج آزمون های تکمیل شده توسط شما را از این قسمت مشاهده نمایید</p>
                                </div>
                            </div>
                        </a>
                    </div>

                    <div class="col-md-6 col-xl-4">
                        <a href="#" class="card card-custom" style="
                            --front-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                            --back-gradient: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                        ">
                            <!-- FRONT SIDE -->
                            <div class="card-front img-card">
                                <div class="floating-particles"></div>
                                <div class="card-body">
                                    <div> 
                                        <i class="fa fa-user-o text-white fs-30" ></i> 
                                    </div>
                                    <div class="text-white">
                                        <h2 style="margin: 0;">عنوان</h2>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- BACK SIDE -->
                            <div class="card-back">
                                <div class="card-body">
                                    <p class="back-text">پشت کارت ۳</p>
                                </div>
                            </div>
                        </a>
                    </div>
                </div>
                    

                </div>
            <!-- CONTAINER END -->
          </div>
        </div>
        <!--app-content close-->
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