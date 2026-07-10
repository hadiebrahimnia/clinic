from django.views import View
from django.shortcuts import render, get_object_or_404 ,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from accounts.models import *
from appointment.models import *
from django.http import JsonResponse
import json
from accounts.forms import *
from core.views import *
from core.utils import *
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.template import Template, Context
from django.core.paginator import Paginator
from django.utils.text import Truncator
from django.views.decorators.http import require_GET

from core.generic import (
    apply_search,
    apply_filters,
    apply_pagination,
    render_search_form,
    render_filter_form,
    render_pagination
)

@require_GET
def get_provinces(request):
    country_id = request.GET.get('country_id')
    if not country_id:
        return JsonResponse([], safe=False)
    
    provinces = Province.objects.filter(
        country_id=country_id
    ).values('id', 'name')
    
    return JsonResponse(list(provinces), safe=False)


def get_cities(request):
    province_id = request.GET.get('province_id')

    cities = City.objects.filter(
        province_id=province_id
    ).values('id', 'name')

    return JsonResponse(list(cities), safe=False)

def get_specializations(request):
    field_id = request.GET.get('field_id')

    specializations = Specialization.objects.filter(
        field_id=field_id
    ).values('id', 'name')

    return JsonResponse(list(specializations), safe=False)



# ====================== Psychologist Main ======================
class AccountView(View):
    template_name = 'form.html'

    def get(self, request, action):
        if action == 'logout':
            logout(request)
            messages.add_message(
                request, 
                messages.SUCCESS, 
                'با موفقیت از سیستم خارج شدید.',
                extra_tags=json.dumps({
                    "style": "success",
                    "alert_class": "success",
                    "size": "medium",
                    "duration": 6000,
                    "location": "top-right",
                    "title": "پیام",
                })
            )
            return redirect('accounts', action='login')
        
        elif action == 'register':
            if request.user.is_authenticated:
                return redirect('dashboard', subject='user')
            form = CustomUserCreationForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
                'title': 'ثبت‌نام',
                'back_url': '/',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form_action': reverse('accounts', args=['register']),
                'submit_text': 'ثبت‌نام',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': '''
                    <p class="display-10">
                        قبلاً حساب کاربری دارید؟
                        <a href="/accounts/login/" class="text-primary">ورود</a>
                    </p>
                ''',
                'form': form
            }
            return render(request, self.template_name, base_context)
        
        elif action == 'login':
            if request.user.is_authenticated:
                return redirect('dashboard', subject='user')
            form = CustomAuthenticationForm()

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
                'title': 'ورود به حساب کاربری',
                'back_url': '/',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form_action': reverse('accounts', args=['login']),
                'submit_text': 'ورود',
                'submit_class': 'btn btn-success btn-lg btn-block display-10',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': '''
                    <p class="display-10">
                        هنوز ثبت‌نام نکرده‌اید؟
                        <a href="/accounts/register/" class="text-primary">ثبت نام</a>
                    </p>

                    <p class="">
                        <a href="#" class="text-primary">فراموشی رمز عبور</a>
                    </p>
                ''',
                'form': form
            }
            return render(request, self.template_name, base_context)
        
        elif action == 'update':
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')
            
            form = ProfileUpdateForm(user=request.user, instance=request.user)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
                'title': 'ویرایش پروفایل',
                'back_url': '/dashboard/user',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form_action': reverse('accounts', args=['update']),
                'submit_text': 'به‌روزرسانی پروفایل',
                'submit_class': 'btn btn-info btn-block ',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'form': form
            }
            return render(request, self.template_name, base_context)
        
        else:
            messages.error(request, 'عملیات نامعتبر است.')
            return redirect('accounts', action='login')

    def post(self, request, action):
        if action == 'register':
            form = CustomUserCreationForm(request.POST, request.FILES)
            if form.is_valid():

                user = form.save(commit=False) 
                user.save()
                default_role, _ = Role.objects.get_or_create(name="user")
                user.roles.add(default_role)

                messages.success(request, 'ثبت‌نام با موفقیت انجام شد! به پروفایل خود خوش آمدید.')
                if not user.is_profile_complete:
                    messages.warning(request, 'لطفاً اطلاعات پروفایل خود را کامل کنید (شماره تلفن، تاریخ تولد، جنسیت و شهر).')
                    return redirect('accounts', action='update')
                return redirect('dashboard', subject='user')
            else:
                # نمایش دوباره فرم با خطاها
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                    'title': 'ثبت‌نام',
                    'back_url': '/',
                    'back_text': 'بازگشت ',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form_action': reverse('accounts', args=['register']),
                    'submit_text': 'ثبت‌نام',
                    'submit_class': 'btn btn-success btn-lg btn-block ',
                    'submit_style': '',
                    'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                    'footer_content': '''
                        <p class="display-10">
                            قبلاً حساب کاربری دارید؟
                            <a href="/accounts/login/" class="text-primary">ورود</a>
                        </p>
                    ''',
                    'form': form
                }
                return render(request, self.template_name, base_context)
            
        elif action == 'login':
            form = CustomAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    messages.add_message(
                        request, messages.SUCCESS,
                        'با موفقیت وارد شدید',
                        extra_tags=json.dumps({
                            "style": "success",
                            "size": "medium",
                            "duration": 6000,
                            "location": "top-right",
                            "title": "پیام",
                        })
                    )
                    if not user.is_profile_complete:
                        messages.warning(
                            request, 
                            'لطفاً اطلاعات پروفایل خود را کامل کنید (شماره تلفن، تاریخ تولد، جنسیت و شهر).'
                        )
                        return redirect('accounts', action='update')
                    return redirect('dashboard', subject='user')
                else:
                    messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
            else:
                messages.add_message(
                    request, messages.ERROR,
                    'نام کاربری یا رمز عبور اشتباه است.',
                    extra_tags=json.dumps({
                        "style": "error",
                        "size": "medium",
                        "duration": 6000,
                        "location": "top-right",
                        "title": "خطای ورود",
                    })
                )

            # نمایش دوباره فرم در صورت خطا
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
                'title': 'ورود به حساب کاربری',
                'back_url': '/',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form_action': reverse('accounts', args=['login']),
                'submit_text': 'ورود',
                'submit_class': 'btn btn-success btn-lg btn-block display-10',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': '''
                    <p class="display-10">
                        هنوز ثبت‌نام نکرده‌اید؟
                        <a href="/accounts/register/" class="text-primary">ثبت نام</a>
                    </p>
                    <p class="">
                        <a href="#" class="text-primary">فراموشی رمز عبور</a>
                    </p>
                ''',
                'form': form
            }
            return render(request, self.template_name, base_context)

        elif action == 'update':
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')
            
            form = ProfileUpdateForm(request.POST, request.FILES, user=request.user, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'پروفایل با موفقیت به‌روزرسانی شد.')
                return redirect('dashboard', subject='user')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                    'title': 'ویرایش پروفایل',
                    'back_url': '/dashboard/user',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form_action': reverse('accounts', args=['update']),
                    'submit_text': 'به‌روزرسانی پروفایل',
                    'submit_class': 'btn btn-info btn-block ',
                    'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                    'form': form
                }
                return render(request, self.template_name, base_context)
        
        else:
            messages.error(request, 'عملیات نامعتبر است.')
            return redirect('accounts', action='login')
    

# ====================== Psychologist Main ======================
class PsychologistActionView(View):
    def get(self, request, subject, action, pk=None):

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
                <div class="main-content ">
                    <div class="side-app with_header">
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
                                    {% for psychologist in psychologists %}
                                        <a href="{detail_url}" class="card mb-3 doctor-card shadow-sm animate-card border-0 text-decoration-none">
                                            <div class="arrow-ribbone-right bg-teal">{{psychologist.PsychologistType}}</div>
                                            
                                            <div class="row g-0 align-items-center">
                                                <div class="col-md-2 position-relative overflow-hidden">
                                                    {% if psychologist.profile_picture %}
                                                        <img src="/media/{{psychologist.profile_picture}}" class="card-img-left rounded-start h-100" alt="{p.profile.first_name or p.profile.username}" style="object-fit: cover; width: 100%;">
                                                    {% else %}
                                                        <div class="bg-light d-flex align-items-center justify-content-center h-100 rounded-start" style="min-height: 180px;"><i class="fas fa-user-md fa-4x text-muted"></i></div>
                                                    {% endif %}

                                                </div>
                                                <div class="col-md-10 align-self-start bd-highlight">
                                                    <div class="card-body px-0">
                                                        <h3 class="mb-2 text-dark fw-bold">{{psychologist.profile.first_name}} {{psychologist.profile.last_name}}</h3>
                                                        <p class="card-text text-muted mb-2">
                                                            <strong>تخصص:</strong> {{psychologist}}
                                                            <span class="specialty-badge">{{psychologist}}</span>
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        </a>
                                    {% endfor %}
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
                'extra_css': [],
                'extra_js': [],
            }
            
            return render(request, 'index2.html', context)

        elif action == 'register':
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')
            
            psychologist = Psychologist.objects.filter(profile=request.user).first()
            if psychologist:
                return redirect('entity-action-detail', subject='psychologist', action='specialties', pk=psychologist.pk)
            
            form = PsychologistCreationUpdateForm(request=request)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت‌نام متخصص',
                'back_url': '/dashboard/user',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action', kwargs={'subject': 'psychologist', 'action': 'register'}),
                'submit_text': 'ثبت‌نام',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)
        
        elif action == 'update' and pk:
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')

            psychologist = get_object_or_404(Psychologist, pk=pk)

            if psychologist.profile != request.user:
                raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

            form = PsychologistCreationUpdateForm(instance=psychologist, request=request)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش متخصص',
                'back_url': '/dashboard/psychologist',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })

            return render(request, 'form.html', base_context)

        elif action == 'detail' and pk:
            psychologist = get_object_or_404(Psychologist, pk=pk)
            full_name = f"{psychologist.profile.first_name or ''} {psychologist.profile.last_name or ''}".strip()
            context = {
                'page_title': full_name,
                'extra_css': [
                    '/static/css/psychologist_detail.css'
                    
                    ],
                'extra_js': [
                    '/static/js/psychologist_detail.js',
                    '/static/plugins/rating/jquery-rate-picker.js',
                    '/static/plugins/rating/rating-picker.js',
                    '/static/plugins/ratings-2/jquery.star-rating.js',
                    '/static/plugins/ratings-2/star-rating.js'
                    ],
                'content': render_psychologist_detail(psychologist,request),
            }
            return render(request, 'index2.html', context)

        else:
            raise Http404("Action not supported")
        
    def post(self, request, subject, action, pk=None): 
        if action == 'register':
            if not request.user.is_authenticated:
                return redirect('accounts', action='login')
            
            psychologist = Psychologist.objects.filter(profile=request.user).first()
            if psychologist:
                return redirect('entity-action-detail', subject='psychologist', action='update', pk=psychologist.pk)

            form = PsychologistCreationUpdateForm(request.POST, request.FILES, request=request)

            if form.is_valid():
                psychologist = form.save(commit=False)
                request.user.save()
                psychologist.profile = request.user
                psychologist.save()
                form.save_m2m()
                default_role, _ = Role.objects.get_or_create(name="psychologist")
                request.user.roles.add(default_role)
                messages.success(request, "اطلاعات متخصص با موفقیت ثبت شد.")
                return redirect('entity-action-detail', subject='psychologist', action='detail', pk=psychologist.pk)
                # return redirect('entity-action-detail', subject='psychologist', action='specialties', pk=psychologist.pk)
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ثبت‌نام متخصص',
                    'back_url': '/dashboard/user',
                    'back_text': 'بازگشت ',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action', kwargs={'subject': 'psychologist', 'action': 'register'}),
                    'submit_text': 'ثبت‌نام',
                    'submit_class': 'btn btn-success btn-lg btn-block ',
                    'card_header_class': 'card-header',
                    'card_header_style': 'background-color: #c2eafc;color: #fff;',
                })
                return render(request, 'form.html', base_context)
            
        elif action == 'update' and pk:
            if not request.user.is_authenticated:
                return redirect('accounts', action='login')

            psychologist = get_object_or_404(Psychologist, pk=pk)

            if psychologist.profile != request.user:
                raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

            form = PsychologistCreationUpdateForm(request.POST, request.FILES, instance=psychologist, request=request)

            if form.is_valid():
                form.save()
                messages.success(request, "اطلاعات متخصص با موفقیت ویرایش شد.")
                return redirect('entity-action-detail', subject='psychologist', action='detail', pk=psychologist.pk)
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ویرایش متخصص',
                    'back_url': '/dashboard/psychologist',
                    'back_text': 'بازگشت ',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block ',
                    'card_header_class': 'card-header',
                    'card_header_style': 'background-color: #c2eafc;color: #fff;',
                })
                return render(request, 'form.html', base_context)
            
        raise Http404("Action not supported")
    

    


# ====================== Psychologist Specialties ======================
class PsychologistSpecialtiesView(View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, pk=pk)
        if psychologist.profile != request.user:
            raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

        specialties_obj = PsychologistSpecialties.objects.filter(psychologist=psychologist).first()
        if not specialties_obj:
            specialties_obj = PsychologistSpecialties(psychologist=psychologist)

        print(specialties_obj)
        print(list(specialties_obj.specialties.all()) if specialties_obj.pk else [])

        form = PsychologistSpecialtiesForm(instance=specialties_obj)

        base_context = {
            'col_class': 'col-md-5 col-12 m-auto',
            'card_class': 'card shadow-lg',
            'card_header_class': 'card-header',
            'card_body_class': 'card-body p-5',
        }
        base_context.update({
            'title': 'زمینه کاری',
            'back_url': '/dashboard/psychologist/',
            'back_text': 'بازگشت ',
            'back_class': 'btn btn-default-light',
            'back_icon': 'fa fa-arrow-left',
            'form':form,
            'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
            'submit_text': 'ثبت اطلاعات',
            'submit_class': 'btn btn-success btn-lg btn-block ',
            'submit_style': '',
            'card_header_class': 'card-header',
            'card_header_style': 'background-color: #1ab0fc;color: #fff;',
            'footer_content': ''''''
        })

        return render(request, 'form.html', base_context)

    def post(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, pk=pk)
        if psychologist.profile != request.user:
            raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

        specialties_obj = PsychologistSpecialties.objects.filter(psychologist=psychologist).first()
        if not specialties_obj:
            specialties_obj = PsychologistSpecialties(psychologist=psychologist)

        form = PsychologistSpecialtiesForm(request.POST, instance=specialties_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "زمینه‌های کاری ثبت شد.")
            return redirect('dashboard', subject='user')
        else:
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'زمینه کاری',
                'back_url': '/dashboard/psychologist/',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
                'submit_text': 'ثبت اطلاعات',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
            })
            return render(request, 'form.html', base_context)
        


# ====================== Psychologist Document ======================
class PsychologistDocumentView(BaseDashboardView,View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, profile=request.user)
        if not psychologist:
            messages.error(request, "ابتدا پروفایل متخصص خود را تکمیل کنید.")
            return redirect('entity-action-detail', subject='psychologist', action='update', pk=psychologist.pk if psychologist else None)

        psychologistdocuments=PsychologistDocument.objects.filter(psychologist=psychologist)

        if action == 'list':
            template_string = """
            {% load jdate %}
                <div class="main-content with-sidebar">
                    <div class="side-app">
                        <div class="main-container container-fluid">
                            <div class="page-header">
                                <ol class="breadcrumb">
                                    <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                    <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</a></li>
                                    <li class="breadcrumb-item"><a href="/dashboard/psychologist"><i class="mdi mdi-stethoscope ml-1"></i>پنل متخصص</a></li>
                                    <li class="breadcrumb-item text-dark"><i class="fa fa-graduation-cap ml-1"></i>مدرک</li>
                                    
                                    <li class="breadcrumb-back">
                                        <a href="/dashboard/psychologist" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                    </li>
                                </ol>
                            </div>

                            <div class="row">
                                <div class="col-xl-3">
                                    <div class="card">
                                        <div class="list-group list-group-transparent mb-0 mail-inbox pb-3">
                                            <div class="mt-4 mx-4 mb-4 text-center">
                                                <a href="/psychologistdocument/create" class="btn btn-outline-success btn-lg d-grid">
                                                    مدرک جدید
                                                </a>
                                            </div>
                                            <div class="p-2">
                                            {% for psychologistdocument in psychologistdocuments %}
                                                <a class="btn border-0 text-start side-menu__item degree-tab-btn 
                                                        {% if forloop.first %}active{% endif %}"
                                                    id="tab-btn-{{ psychologistdocument.id }}"
                                                    data-bs-toggle="tab"
                                                    data-bs-target="#degree-{{ psychologistdocument.id }}"
                                                    role="tab"
                                                    aria-controls="degree-{{ psychologistdocument.id }}"
                                                    aria-selected="{% if forloop.first %}true{% else %}false{% endif %}"
                                                >
                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                        <i class="side-menu__icon fa fa-graduation-cap"></i>
                                                    </span>
                                                    
                                                    <span class="side-menu__label mr-2">{{ psychologistdocument }}</span>
                                                </a>
                                            {% endfor %}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-xl-9">
                                    <div class="tab-content" id="degreeTabContent">
                                        {% for psychologistdocument in psychologistdocuments %}
                                            <div class="tab-pane fade {% if forloop.first %}show active{% endif %}" 
                                                id="degree-{{ psychologistdocument.id }}" 
                                                role="tabpanel">
                                                
                                                <div class="card">
                                                    <div class="card-header">
                                                        <h3 class="card-title">
                                                        {{ psychologistdocument }}
                                                        </span>
                                                        </h3>
                                                        <div class="card-options">
                                                            <a href="/psychologistdocument/update/{{ psychologistdocument.id }}" 
                                                            class="me-3 text-success" data-bs-toggle="tooltip" title="ویرایش">
                                                                <i class="fa fa-pencil-square-o"></i>
                                                            </a>
                                                            <a href="#" onclick="if(confirm('آیا مطمئن هستید؟')) window.location.href='/psychologistdocument/delete/{{ psychologistdocument.id }}/'" 
                                                            class="text-danger" data-bs-toggle="tooltip" title="حذف">
                                                                <i class="fe fe-trash-2"></i>
                                                            </a>
                                                        </div>
                                                    </div>
                                                    
                                                    <div class="card-body">
                                                        <div class="visitor-list">
                                                            
                                                            
                                                            <div class="row my-5 align-items-center">
                                                                <div class="col-md-1 col-2 text-center">
                                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                        <i class="fa fa-book"></i>
                                                                    </span>                                                        
                                                                </div>
                                                                <div class="col-md-8 col-5 px-0">
                                                                    <h5 class="mb-1">{{ psychologistdocument }}</h5>
                                                                    <p class="text-muted mb-0">رشته تحصیلی</p>
                                                                </div>
                                                                <div class="col-md-3 col-5 px-0">
                                                                    <div class="toggle_div">
                                                                        <span class="custom-switch-description">نمایش به کاربران</span>
                                                                        <button type="button" class="toggle toggle-sm status-switch {% if psychologistdegree.is_visible %}active{% endif %}">
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
                                        {% endfor %}
                                    </div>
                                </div>

                               
                                
                            </div>
                        </div>
                    </div>
                </div>
                
            """



            t = Template(template_string)
            content = t.render(Context({
                'psychologistdocuments':psychologistdocuments,
            }))

            context = {
                'content': mark_safe(content),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/psychologist'),
                'extra_css': [
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
            form = PsychologistDocumentForm()
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت مدرک',
                'back_url': '/psychologistdocument/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action', kwargs={'subject': 'psychologistdocument', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)

        elif action == 'update':
            document = get_object_or_404(PsychologistDocument, pk=pk, psychologist=psychologist)
            form = PsychologistDocumentForm(instance=document)
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش مدرک',
                'back_url': '/psychologistdocument/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistdocument', 'action': 'update' , 'pk': document.pk }),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)


        raise Http404("Action not supported")
    
    def post(self, request, subject, action, pk=None):
        psychologist = get_object_or_404(Psychologist, profile=request.user)

        if action == 'create':
            form = PsychologistDocumentForm(request.POST, request.FILES)
            if form.is_valid():
                document = form.save(commit=False)
                document.psychologist = psychologist
                document.save()
                messages.success(request, "مدرک با موفقیت ثبت شد.")
                return redirect('entity-action', subject='psychologistdocument', action='list')


            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت مدرک تحصیلی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action':reverse('entity-action', kwargs={'subject': 'psychologistdocument','action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            document = get_object_or_404(PsychologistDocument, pk=pk, psychologist=psychologist)
            form = PsychologistDocumentForm(request.POST, request.FILES, instance=document)

            if form.is_valid():
                form.save()
                messages.success(request, "مدرک با موفقیت ویرایش شد.")
                return redirect('entity-action', subject='psychologistdocument', action='list')
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش مدرک تحصیلی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistdocument','action': 'create', 'pk': document.pk }),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
            





# ====================== Psychologist Degrees ======================
class PsychologistDegreeView(BaseDashboardView,View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, profile=request.user)
        if not psychologist:
            messages.error(request, "ابتدا پروفایل متخصص خود را تکمیل کنید.")
            return redirect('entity-action-detail', subject='psychologist', action='update', pk=psychologist.pk if psychologist else None)

        psychologistdegrees=PsychologistDegree.objects.filter(psychologist=psychologist)

        if action == 'list':
            template_string = """
            {% load jdate %}
                <div class="main-content with-sidebar">
                    <div class="side-app">
                        <div class="main-container container-fluid">
                            <div class="page-header">
                                <ol class="breadcrumb">
                                    <li class="breadcrumb-item"><a href="/"><i class="mdi mdi-home ml-1"></i>خانه</a></li>
                                    <li class="breadcrumb-item"><a href="/dashboard/user"><i class="mdi mdi-view-dashboard ml-1"></i>داشبورد</a></li>
                                    <li class="breadcrumb-item"><a href="/dashboard/psychologist"><i class="mdi mdi-stethoscope ml-1"></i>پنل متخصص</a></li>
                                    <li class="breadcrumb-item text-dark"><i class="fa fa-graduation-cap ml-1"></i>مدرک تحصیلی</li>
                                    
                                    <li class="breadcrumb-back">
                                        <a href="/dashboard/psychologist" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                    </li>
                                </ol>
                            </div>

                            <div class="row">
                                <div class="col-xl-3">
                                    <div class="card">
                                        <div class="list-group list-group-transparent mb-0 mail-inbox pb-3">
                                            <div class="mt-4 mx-4 mb-4 text-center">
                                                <a href="/psychologistdegree/create" class="btn btn-outline-success btn-lg d-grid">
                                                    مدرک جدید
                                                </a>
                                            </div>
                                            <div class="p-2">
                                            {% for psychologistdegree in psychologistdegrees %}
                                                <a class="btn border-0 text-start side-menu__item degree-tab-btn 
                                                        {% if forloop.first %}active{% endif %}"
                                                    id="tab-btn-{{ psychologistdegree.id }}"
                                                    data-bs-toggle="tab"
                                                    data-bs-target="#degree-{{ psychologistdegree.id }}"
                                                    role="tab"
                                                    aria-controls="degree-{{ psychologistdegree.id }}"
                                                    aria-selected="{% if forloop.first %}true{% else %}false{% endif %}"
                                                >
                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                        <i class="side-menu__icon fa fa-graduation-cap"></i>
                                                    </span>
                                                    
                                                    <span class="side-menu__label mr-2">{{ psychologistdegree.get_level_display }}</span>
                                                </a>
                                            {% endfor %}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-xl-9">
                                    <div class="tab-content" id="degreeTabContent">
                                        {% for psychologistdegree in psychologistdegrees %}
                                            <div class="tab-pane fade {% if forloop.first %}show active{% endif %}" 
                                                id="degree-{{ psychologistdegree.id }}" 
                                                role="tabpanel">
                                                
                                                <div class="card">
                                                    <div class="card-header">
                                                        <h3 class="card-title">
                                                        {{ psychologistdegree.get_level_display }}
                                                        <span 
                                                            class="badge
                                                            {% if psychologistdegree.study_status == "Studying" %}
                                                                bg-warning
                                                            {% elif psychologistdegree.study_status == "Graduated" %}
                                                                bg-success
                                                            {% else %}
                                                                bg-danger 
                                                            {% endif %}
                                                            badge-sm mr-1
                                                            "
                                                        >
                                                        {{psychologistdegree.get_study_status_display}}
                                                        </span>
                                                        </h3>
                                                        <div class="card-options">
                                                            <a href="/psychologistdegree/update/{{ psychologistdegree.id }}" 
                                                            class="me-3 text-success" data-bs-toggle="tooltip" title="ویرایش">
                                                                <i class="fa fa-pencil-square-o"></i>
                                                            </a>
                                                            <a href="#" onclick="if(confirm('آیا مطمئن هستید؟')) window.location.href='/psychologistdegree/delete/{{ psychologistdegree.id }}/'" 
                                                            class="text-danger" data-bs-toggle="tooltip" title="حذف">
                                                                <i class="fe fe-trash-2"></i>
                                                            </a>
                                                        </div>
                                                    </div>
                                                    
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
                                                                        <button type="button" class="toggle toggle-sm status-switch {% if psychologistdegree.is_visible %}active{% endif %}">
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
                                                                        <img class="avatar brround avatar-md" src="/media/{{ psychologistdegree.university.icon }}" alt="">
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
                                                                        <button type="button" class="toggle toggle-sm status-switch {% if psychologistdegree.is_visible %}active{% endif %}">
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
                                                                        <i class="fa fa-chart-bar"></i>
                                                                    </span>                                                        
                                                                </div>
                                                                <div class="col-md-8 col-5 px-0">
                                                                    <h5 class="mb-1">{{ psychologistdegree.gpa|default:"—" }}</h5>
                                                                    <p class="text-muted mb-0">معدل</p>
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
                                                                <div class="col-md-11 col-10 px-0">
                                                                    <h5 class="mb-1">{{ psychologistdegree.thesis_title|default:"—" }}</h5>
                                                                    <p class="text-muted mb-0">عنوان پایان‌نامه</p>
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
                                                                    <div class="col-md-8 col-5 px-0">
                                                                    <h5 class="mb-1">{{ psychologistdegree.start_year|to_jalali_date }}</h5>
                                                                    <p class="text-muted mb-0">تاریخ شروع تحصیل</p>
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
                                                            </div>

                                                            <hr class="hr">
                                                            <div class="row my-5 align-items-center">
                                                                <div class="col-md-1 col-2 text-center">
                                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                        <i class="fa fa-file-text-o"></i>
                                                                    </span>                                                        
                                                                </div>
                                                                <div class="col-md-11 col-10 px-0">
                                                                    <a href="javascript:void(0)" 
                                                                    onclick="showImageModal('/media/{{ psychologistdegree.degree_file }}', '{{ psychologistdegree.get_level_display }}')">
                                                                        <img class="img-responsive br-5 img-zoom w-10"
                                                                            src="/media/{{ psychologistdegree.degree_file }}"
                                                                            alt="{{ psychologistdegree.get_level_display }}"
                                                                            style="cursor: pointer;">
                                                                    </a>
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
                    </div>
                </div>
                
            """



            t = Template(template_string)
            content = t.render(Context({
                'psychologistdegrees':psychologistdegrees,
            }))

            context = {
                'content': mark_safe(content),
                'sidebar_menu': self.get_sidebar_menu(request, active_section='/dashboard/psychologist'),
                'extra_css': [
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
            form = PsychologistDegreeForm()
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت مدرک تحصیلی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action', kwargs={'subject': 'psychologistdegree', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)

        elif action == 'update':
            degree = get_object_or_404(PsychologistDegree, pk=pk, psychologist=psychologist)
            form = PsychologistDegreeForm(instance=degree)
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش مدرک تحصیلی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistdegree', 'action': 'update' , 'pk': degree.pk }),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)


        raise Http404("Action not supported")
    
    def post(self, request, subject, action, pk=None):
        psychologist = get_object_or_404(Psychologist, profile=request.user)

        if action == 'create':
            form = PsychologistDegreeForm(request.POST, request.FILES)
            if form.is_valid():
                degree = form.save(commit=False)
                degree.psychologist = psychologist
                degree.save()
                messages.success(request, "مدرک تحصیلی با موفقیت ثبت شد.")
                return redirect('entity-action', subject='psychologistdegree', action='list')


            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ثبت مدرک تحصیلی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action':reverse('entity-action-detail', kwargs={'subject': 'psychologistdegree','action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        elif action == 'update':
            degree = get_object_or_404(PsychologistDegree, pk=pk, psychologist=psychologist)
            form = PsychologistDegreeForm(request.POST, request.FILES, instance=degree)

            if form.is_valid():
                form.save()
                messages.success(request, "مدرک تحصیلی با موفقیت ویرایش شد.")
                return redirect('entity-action', subject='psychologistdegree', action='list')
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }

            base_context.update({
                'title': 'ویرایش مدرک تحصیلی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistdegree','action': 'create', 'pk': degree.pk }),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block',
                'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                'footer_content': ''
            })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
            

        
    
# ========== متدهای کمکی (داخل کلاس) ==========
def render_psychologist_detail(psychologist, request=None):
    full_name = f"{psychologist.profile.first_name or ''} {psychologist.profile.last_name or ''}".strip()
    profile_picture = psychologist.profile_picture.url if hasattr(psychologist, 'profile_picture') and psychologist.profile_picture else ''
    
    PsychologistType = getattr(psychologist, 'PsychologistType', '')
    if PsychologistType and hasattr(PsychologistType, 'name'):
        PsychologistType = PsychologistType.name    
    try:
        newpatients = PsychologistNewPatients.objects.get(psychologist=psychologist)
    except PsychologistNewPatients.DoesNotExist:
        newpatients = None  
    try:
        specialties = PsychologistSpecialties.objects.get(psychologist=psychologist)
    except PsychologistSpecialties.DoesNotExist:
        specialties = None  
         
    # membership_code = getattr(psychologist, 'membership_code', None)
    # license_code = getattr(psychologist, 'license_code', None)

    user_status = get_user_status(psychologist, request)
    is_owner = user_status.get('is_owner', False)

    degrees = psychologist.degrees.filter(is_active=True, is_deleted=False).order_by('-graduation_year') if hasattr(psychologist, 'degrees') else []
    sections = psychologist.sections.filter(is_active=True, is_deleted=False).order_by('order') if hasattr(psychologist, 'sections') else []

    # ====================== Context ======================
    context = Context({
        'full_name': full_name,
        'profile_picture': profile_picture,
        'PsychologistType': PsychologistType,
        # 'membership_code': membership_code,
        # 'license_code': license_code,
        'is_owner': is_owner,
        'is_accepting_new_patients': newpatients,
        'specialties': specialties,
        'degrees': degrees,
        'sections': sections,
    })

    template_string = """
        <div class="main-content">
            <div class="side-app with_header">
                <div class="main-container container-fluid">
                    <div class="page-header">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item ">
                                <a href="/psychologist/list"><i class="icon icon-list ml-2"></i>لیست متخصصان کلینیک</a>
                            </li>
                            <li class="breadcrumb-item text-dark" aria-current="page">
                                <i class="fa fa-user-circle ml-2"></i>{{full_name}}
                            </li>
                            <li class="breadcrumb-back">
                                <a href="/psychologist/list" class="btn btn-outline-default fw-900">
                                    بازگشت
                                    <i class="mdi mdi-arrow-left-thick"></i>
                                </a>
                            </li>
                        </ol>
                    </div>

                    <div class="row" id="user-profile">
                        <div class="col-lg-12">
                            <div class="card shadow-sm">
                                <div class="card-body">
                                    <div class="row align-items-start g-3">

                                        <!-- قسمت اصلی: عکس + اطلاعات -->
                                        <div class="col-12 col-md-10">
                                            <div class="d-flex flex-column flex-sm-row align-items-start gap-3">

                                                <!-- عکس -->
                                                <img src="{{ profile_picture }}"
                                                    class="card-img-left flex-shrink-0 shadow-sm m-auto"
                                                    style="width: 130px; height: 160px;" alt="{{full_name}}">

                                                <!-- اطلاعات -->
                                                <div class="NameType flex-grow-1 pt-1">
                                                    <div
                                                        class="NameType d-flex flex-column flex-sm-row justify-content-between align-items-start gap-2">
                                                        <div class="NameType">
                                                            <h3 class="mb-1 fw-bold">{{full_name}}</h3>
                                                            <p class="text-muted mb-0 ">{{PsychologistType}}</p>
                                                        </div>
                                                        {% if is_owner == True %}
                                                        <a href="javascript:void(0)" class="NameType btn btn-outline-info border-0 d-flex align-items-center gap-1 text-nowrap">
                                                            <i class="fa fa-pencil-square-o"></i>
                                                            <span>ویرایش</span> 
                                                        </a>
                                                        {% endif %}
                                                    </div>

                                                    <div class="mt-3 d-flex flex-column gap-2">

                                                        <div class="col-lg-3 col-md-4 col-12 px-0 mt-4">
                                                            <span class="badge bg-primary fs-6 py-2 px-3 col-12">
                                                                <i class="fa fa-id-card me-1"></i>
                                                                کد عضویت: <strong>{{membership_code}}</strong>
                                                            </span>
                                                        </div>

                                                        <div class="col-lg-3 col-md-4 col-12 px-0">
                                                            <span class="badge bg-success fs-6 py-2 px-3 col-12">
                                                                <i class="fa fa-certificate me-1"></i>
                                                                پروانه اشتغال: <strong>{{license_code}}</strong>
                                                            </span>
                                                        </div>

                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- قسمت راست: دکمه‌ها -->
                                        <div class="col-12 col-md-2">
                                            <div class="d-flex flex-column gap-2 h-100">
                                                <div class="row g-2">
                                                    <div class="col-6 col-sm-12">
                                                        <button class="btn btn-primary w-100">
                                                            <i class="fa fa-rss"></i>
                                                            <span>دنبال کردن</span>
                                                        </button>
                                                    </div>
                                                    <div class="col-6 col-sm-12">
                                                        <button class="btn btn-secondary w-100">
                                                            <i class="fa fa-envelope"></i>
                                                            <span>پیام</span>
                                                        </button>
                                                    </div>
                                                </div>

                                                <div class="card-footer">
                                                    <div class="row user-social-detail">
                                                        <div class="social-profile rounded text-center">
                                                            <a href="javascript:void(0)"><i class="fa fa-google"></i></a>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-xl-3">

                                    <div class="card">
                                        <div class="card-header d-flex">
                                            <div class="card-title">روزهای کاری</div>
                                        </div>
                                        {% if is_accepting_new_patients == False %}
                                        <div class="card-alert alert alert-danger mb-0">
                                            <i class="fe fe-alert-triangle fs-5"></i>
                                            <span> متخصص مراجع جدید نمی‌پذیرد</span>
                                        </div>
                                        {% endif %}
                                        <div class="card-body">
                                            <div class="d-flex align-items-center mb-3 mt-3">
                                                <div class="me-4 text-center text-primary">

                                                </div>
                                            </div>
                                        </div>

                                    </div>
                                    {% if specialties and specialties.specialties.exists %}
                                    <div class="card">
                                        <div class="card-header d-flex">
                                            <div class="card-title">زمینه کاری</div>
                                            {% if is_owner == True %}
                                                <a href="javascript:void(0)" class=" btn btn-outline-info border-0 mr-auto">
                                                    <i class="fa fa-pencil-square-o"></i>
                                                    <span>ویرایش</span> 
                                                </a>
                                            {% endif %}
                                        </div>
                                        <div class="card-body">
                                            <div class="tags">
                                                {% for specialtie in specialties.specialties.all %}
                                                    <a href="javascript:void(0)" class="tag">{{ specialtie }}</a>
                                                {% endfor %}
                                            </div>
                                        </div>
                                    </div>
                                    {% endif %}
                                    <div class="card">
                                        <div class="card-header d-flex">
                                            <div class="card-title">تحصیلات</div>
                                            {% if is_owner == True %}
                                                <a href="javascript:void(0)" class=" btn btn-outline-info border-0 mr-auto">
                                                    <i class="fa fa-pencil-square-o"></i>
                                                    <span>ویرایش</span> 
                                                </a>
                                            {% endif %}
                                        </div>
                                        <div class="card-body">
                                            <div class="main-profile-contact-list">

                                                <div class="me-5">
                                                    <div class="media mb-4 d-flex">
                                                        <div class="media-icon bg-primary mb-3 mb-sm-0 me-3 mt-1">
                                                            <svg style="width:24px;height:24px;margin-top:-8px"
                                                                viewBox="0 0 24 24">
                                                                <path fill="#fff"
                                                                    d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3M18.82 9L12 12.72L5.18 9L12 5.28L18.82 9M17 16L12 18.72L7 16V12.27L12 15L17 12.27V16Z">
                                                                </path>
                                                            </svg>
                                                        </div>
                                                        <div class="media-body">
                                                            <h6 class="font-weight-semibold mb-1">{{level}}</h6>
                                                            <span>{{uni}}</span>
                                                            <p>{{spec}} - {{status}}</p>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div class="me-5">
                                                    <div class="media mb-4 d-flex">
                                                        <div class="media-icon bg-primary mb-3 mb-sm-0 me-3 mt-1">
                                                            <svg style="width:24px;height:24px;margin-top:-8px"
                                                                viewBox="0 0 24 24">
                                                                <path fill="#fff"
                                                                    d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3M18.82 9L12 12.72L5.18 9L12 5.28L18.82 9M17 16L12 18.72L7 16V12.27L12 15L17 12.27V16Z">
                                                                </path>
                                                            </svg>
                                                        </div>
                                                        <div class="media-body">
                                                            <h6 class="font-weight-semibold mb-1">ثبت نشده</h6>
                                                            <p>اطلاعات تحصیلی موجود نیست</p>
                                                        </div>
                                                    </div>
                                                </div>

                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div class="col-xl-6">
                                    {% if sections %}
                                        {% for section in sections %}
                                        <div class="card"
                                            style="background-color: {{bg_color}}; color: {{text_color}}; margin-bottom: 20px;">
                                            <div class="card-header d-flex">
                                                <div class="card-title">{{title}}</div>
                                                <a href="javascript:void(0)" class=" btn btn-outline-info border-0 mr-auto">
                                                    <i class="fa fa-pencil-square-o"></i>
                                                    <span>ویرایش</span> 
                                                </a>
                                            </div>
                                            <div class="card-body">
                                                {{content}}
                                            </div>
                                        </div>
                                        {% endfor %}
                                    {% endif %}
                                </div>

                                <!-- ستون راست -->
                                <div class="col-xl-3">
                                    <div class="card">
                                        <div class="card-body">
                                            <div class="main-profile-contact-list">
                                                <div class="me-5">
                                                    <div class="media mb-4 d-flex">
                                                        <div class="media-icon bg-secondary bradius me-3 mt-1">
                                                            <i class="fe fe-edit fs-20 text-white"></i>
                                                        </div>
                                                        <div class="media-body">
                                                            <span class="text-muted">مطالب علمی منتشر شده</span>
                                                            <div class="fw-semibold fs-25">
                                                                0
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="me-5 mt-5 mt-md-0">
                                                    <div class="media mb-4 d-flex">
                                                        <div class="media-icon bg-danger bradius text-white me-3 mt-1">
                                                            <span class="mt-3">
                                                                <i class="fe fe-users fs-20"></i>
                                                            </span>
                                                        </div>
                                                        <div class="media-body">
                                                            <span class="text-muted">دنبال‌کنندگان</span>
                                                            <div class="fw-semibold fs-25">
                                                                0
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="me-0 mt-5 mt-md-0">
                                                    <div class="media">
                                                        <div class="media-icon bg-primary text-white bradius me-3 mt-1">
                                                            <span class="mt-3">
                                                                <i class="fe fe-cast fs-20"></i>
                                                            </span>
                                                        </div>
                                                        <div class="media-body">
                                                            <span class="text-muted">پیام ها پاسخ داده شده</span>
                                                            <div class="fw-semibold fs-25">
                                                                0
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="card">
                                        <div class="card-header">
                                            <div class="card-title">نظر مراجعین</div>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-4 col-5 m-auto text-center">
                                                    نظر 1
                                                </div>
                                                <div class="col-md-8 col-7 ltr">
                                                    <div class="rating-stars  block my-rating-2 ltr" data-rating="4.5"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="card">
                                        <div class="card-header">
                                            <div class="card-title">افراد مرتبط</div>
                                        </div>
                                        <div class="card-body">
                                            <div class="visitor-list">
                                                <div class="media m-0 mt-0 border-bottom">
                                                    <img class="avatar brround avatar-md me-3" alt="avatra-img"
                                                        src="../assets/images/users/18.jpg">
                                                    <div class="media-body">
                                                        <a href="javascript:void(0)" class="text-default fw-semibold">-</a>
                                                        <p class="text-muted ">-</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
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
    return mark_safe(t.render(context))



class SecretaryActionView(View):
    def get(self, request, subject, action, pk=None):

        if action == 'register':
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')
            
            secretary = Secretary.objects.filter(profile=request.user).first()
            if secretary:
                return redirect('dashboard', subject='secretary')
            
            form = SecretaryCreationUpdateForm(request=request)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت‌نام منشی',
                'back_url': '/dashboard/user',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action', kwargs={'subject': 'secretary', 'action': 'register'}),
                'submit_text': 'ثبت‌نام',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)
        
        elif action == 'update' and pk:
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')

            secretary = get_object_or_404(Secretary, pk=pk)

            if secretary.profile != request.user:
                raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

            form = SecretaryCreationUpdateForm(instance=secretary, request=request)

            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش منشی',
                'back_url': '/dashboard/secretary',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })

            return render(request, 'form.html', base_context)


        else:
            raise Http404("Action not supported")
        
    def post(self, request, subject, action, pk=None): 
        if action == 'register':
            if not request.user.is_authenticated:
                return redirect('accounts', action='login')
            
            secretary = Secretary.objects.filter(profile=request.user).first()
            if secretary:
                return redirect('dashboard', subject='secretary')

            form = SecretaryCreationUpdateForm(request.POST, request.FILES, request=request)

            if form.is_valid():
                secretary = form.save(commit=False)
                request.user.save()
                secretary.profile = request.user
                secretary.save()
                default_role, _ = Role.objects.get_or_create(name="secretary")
                request.user.roles.add(default_role)
                messages.success(request, "اطلاعات متخصص با موفقیت ثبت شد.")
                return redirect('dashboard', subject='secretary')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ثبت‌نام منشی',
                    'back_url': '/dashboard/user',
                    'back_text': 'بازگشت ',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action', kwargs={'subject': 'secretary', 'action': 'register'}),
                    'submit_text': 'ثبت‌نام',
                    'submit_class': 'btn btn-success btn-lg btn-block ',
                    'card_header_class': 'card-header',
                    'card_header_style': 'background-color: #c2eafc;color: #fff;',
                })
                return render(request, 'form.html', base_context)
            
        elif action == 'update' and pk:
            if not request.user.is_authenticated:
                return redirect('accounts', action='login')

            secretary = get_object_or_404(Secretary, pk=pk)

            if secretary.profile != request.user:
                raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

            form = SecretaryCreationUpdateForm(request.POST, request.FILES, instance=secretary, request=request)

            if form.is_valid():
                form.save()
                messages.success(request, "اطلاعات منشی با موفقیت ویرایش شد.")
                return redirect('dashboard', subject='secretary')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ویرایش منشی',
                    'back_url': '/dashboard/secretary',
                    'back_text': 'بازگشت ',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block ',
                    'card_header_class': 'card-header',
                    'card_header_style': 'background-color: #c2eafc;color: #fff;',
                })
                return render(request, 'form.html', base_context)
            
        raise Http404("Action not supported")
    
    