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
        


# ====================== Psychologist Degrees ======================
class PsychologistDegreeView(View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, pk=pk)
        if psychologist.profile != request.user:
            raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

        formset = DegreeFormSet(
            instance=psychologist, 
            queryset=psychologist.degrees.all()
        )

        base_context = {
            'col_class': 'col-md-5 col-12 m-auto',
            'card_class': 'card shadow-lg',
            'card_header_class': 'card-header',
            'card_body_class': 'card-body p-5',
        }
        base_context.update({
            'title': 'مدارک تحصیلی',
            'back_url': '/dashboard/psychologist/',
            'back_text': 'بازگشت ',
            'back_class': 'btn btn-default-light',
            'back_icon': 'fa fa-arrow-left',
            'formset': formset,
            'prefix':'مدرک',
            'add_button_text':"اضافه کردن مدرک جدید",
            'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
            'submit_text': 'ثبت و ادامه',
            'submit_class': 'btn btn-success btn-lg btn-block ',
            'submit_style': '',
            'card_header_class': 'card-header',
            'card_header_style': 'background-color: #1ab0fc;color: #fff;',
            'footer_content': ''''''
        })
        return render(request, 'formset.html', base_context)

    def post(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, pk=pk)
        if psychologist.profile != request.user:
            raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

        formset = DegreeFormSet(request.POST, request.FILES, instance=psychologist)

        if formset.is_valid():
            formset.save()
            messages.success(request, "مدارک تحصیلی ثبت شد.")
            return redirect('dashboard', subject='user')
        else:
            # error handling similar to get
            pass
    
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
         
    membership_code = getattr(psychologist, 'membership_code', None)
    license_code = getattr(psychologist, 'license_code', None)

    user_status = get_user_status(psychologist, request)
    is_owner = user_status.get('is_owner', False)

    degrees = psychologist.degrees.filter(is_active=True, is_deleted=False).order_by('-graduation_year') if hasattr(psychologist, 'degrees') else []
    sections = psychologist.sections.filter(is_active=True, is_deleted=False).order_by('order') if hasattr(psychologist, 'sections') else []

    # ====================== Context ======================
    context = Context({
        'full_name': full_name,
        'profile_picture': profile_picture,
        'PsychologistType': PsychologistType,
        'membership_code': membership_code,
        'license_code': license_code,
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