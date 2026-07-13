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
from django.db.models import Q

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
            specialties=PsychologistSpecialties.objects.all()
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
            psychologists, current_page, total_pages, total, per_page = apply_pagination(queryset, request, per_page=15)
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
                                        {% if not psychologist.is_deleted and psychologist.is_active %}
                                            <div class="col-12">
                                                <a
                                                    href="/psychologist/detail/{{psychologist.id}}"
                                                    class="card card-custom"
                                                    style="
                                                    height: 160px!important;
                                                    --front-gradient: linear-gradient(
                                                        135deg,
                                                        #ffffff 0%,
                                                        #ffffff 100%
                                                    );
                                                    --back-gradient: linear-gradient(
                                                        135deg,
                                                        #000000 0%,
                                                        #000000 100%
                                                    );
                                                    ">
                                                    <div class="card-front img-card">
                                                        <div class="floating-particles"></div>
                                                        <div class="card-body p-0">
                                                            <div class="arrow-ribbone-right bg-teal" style="top:15px!important;">{{psychologist.PsychologistType}}</div>
                                                            <div class="row w-100">
                                                                <div class="col-xl-2 col-lg-3 col-md-4 col-sm-5 col-6 px-0">
                                                                    <img src="/media/{{psychologist.profile_picture}}" class="card-img-left w-85" alt="{p.profile.first_name or p.profile.username}" style="object-fit: cover;">
                                                                </div>
                                                                <div class="col-xl-10 col-lg-9 col-md-8 col-sm-7 col-6 d-flex justify-content-center align-items-center flex-column">
                                                                    <div class="">
                                                                        <p class="display-8 mb-0" style="color: black;">
                                                                            {{psychologist.profile.first_name}} {{psychologist.profile.last_name}}
                                                                        </p>
                                                                    </div>
                                                                    <div class="mt-2">
                                                                        <span class="badge bg-info badge-sm">مشاهده و رزور نوبت</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            
                                                        </div>
                                                    </div>

                                                    <div class="card-back">
                                                        <div class="card-body">
                                                            <div class="arrow-ribbone-right bg-teal" style="top:15px!important;">{{psychologist.profile.first_name}} {{psychologist.profile.last_name}}</div>
                                                            <p class="back-text">
                                                                {% for ps in psychologist.specialties.all %}
                                                                    {% for specialty in ps.specialties.all %}
                                                                        <span class="badge rounded-pill bg-white text-dark me-1 mb-1 mt-1">
                                                                            {{ specialty.name }}
                                                                        </span>
                                                                    {% endfor %}
                                                                {% endfor %}        
                                                            </p>
                                                        </div>
                                                    </div>
                                                </a>
                                            </div>
                                        {% endif %}
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
                "specialties":specialties,
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
            user_status = get_user_status(psychologist, request)
            is_owner = user_status.get('is_owner', False)

            try:
                membership_card = PsychologistDocument.objects.filter(
                    psychologist=psychologist,
                    document_type="membership_card",
                    is_active=True,
                    is_deleted=False,
                    ).filter(
                    Q(display_config__code=True) |
                    Q(display_config__document_image=True) 
                ).last()
            except Exception:
                membership_card = None
            try:
                license_card = PsychologistDocument.objects.filter(
                    psychologist=psychologist,
                    document_type="license_card",
                    is_active=True,
                    is_deleted=False,
                    ).filter(
                    Q(display_config__code=True) |
                    Q(display_config__document_image=True) 
                ).last()
            except Exception:
                license_card = None
            try:
                newpatients = PsychologistNewPatients.objects.get(psychologist=psychologist)
                is_accepting_new_patients = newpatients.is_accepting_new_patients
            except PsychologistNewPatients.DoesNotExist:
                is_accepting_new_patients = False

            try:
                specialties = PsychologistSpecialties.objects.get(psychologist=psychologist)
            except Exception:
                specialties = None

            try:
                documents = PsychologistDocument.objects.filter(
                    psychologist=psychologist,
                    is_active=True,
                    is_deleted=False,
                    document_type="certificate",
                ).filter(
                    Q(display_config__document_type=True) |
                    Q(display_config__document_image=True) |
                    Q(display_config__code=True) |
                    Q(display_config__title=True) |
                    Q(display_config__description=True)
                )
            except Exception:
                documents = None

            try:
                degrees = PsychologistDegree.objects.filter(
                    psychologist=psychologist,
                    is_active=True,
                    is_deleted=False
                ).filter(
                    Q(display_config__specialization=True) |
                    Q(display_config__university=True) |
                    Q(display_config__start_year=True) |
                    Q(display_config__graduation_year=True) |
                    Q(display_config__gpa=True) |
                    Q(display_config__thesis_title=True) |
                    Q(display_config__degree_file=True)
                )
            except Exception:
                degrees = None

            try:
                socialmedias = PsychologistSocialMedia.objects.filter(
                    psychologist=psychologist,
                    is_active=True,
                    is_deleted=False
                ).filter(
                    Q(display_config__url=True) 
                )
            except Exception:
                socialmedias = None

            try:
                sections = PsychologistSection.objects.filter(
                    psychologist=psychologist,
                    is_active=True,
                    is_deleted=False
                ).filter(
                    Q(display_config__section_type=True) |
                    Q(display_config__description=True) 
                )
            except Exception:
                sections = None
            
            print(sections)

            # ==================== تمپلیت بهینه‌شده ====================
            template_string = """
                {% load jdate %}
                <div class="main-content">
                    <div class="side-app with_header">
                        <div class="main-container container-fluid">
                            {% if psychologist.is_deleted %}
                                <!-- کارت خطای حذف شده -->
                                <div class="row p-5">
                                    <div class="col-xl-3 col-sm-6 m-auto">
                                        <div class="card border p-0 pb-3">
                                            <div class="card-header border-0 pt-3">خطا</div>
                                            <div class="card-body text-center">
                                                <span>
                                                    <svg xmlns="http://www.w3.org/2000/svg" height="60" width="60" viewBox="0 0 24 24">
                                                        <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path>
                                                        <circle cx="12" cy="17" r="1" fill="#e62a45"></circle>
                                                        <path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                    </svg>
                                                </span>
                                                <h4 class="h4 mb-0 mt-3">متخصص مورد نظر یافت نشد</h4>
                                            </div>
                                            <div class="card-footer text-center border-0 pt-0">
                                                <a href="/psychologist/list" class="btn btn-white">بازگشت</a>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            {% elif not psychologist.is_active and not is_owner %}
                                <!-- کارت خطای غیرفعال برای کاربران عادی -->
                                <div class="row p-5">
                                    <div class="col-xl-3 col-sm-6 m-auto">
                                        <div class="card border p-0 pb-3">
                                            <div class="card-header border-0 pt-3">خطا</div>
                                            <div class="card-body text-center">
                                                <span>
                                                    <svg xmlns="http://www.w3.org/2000/svg" height="60" width="60" viewBox="0 0 24 24">
                                                        <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path>
                                                        <circle cx="12" cy="17" r="1" fill="#e62a45"></circle>
                                                        <path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                    </svg>
                                                </span>
                                                <h4 class="h4 mb-0 mt-3">متخصص مورد نظر یافت نشد</h4>
                                            </div>
                                            <div class="card-footer text-center border-0 pt-0">
                                                <a href="/psychologist/list" class="btn btn-white">بازگشت</a>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            {% else %}
                                {% if is_owner and not psychologist.is_active %}
                                    <div class="row">
                                        <div class="col-12">
                                            <div class="card bg-danger mb-0 p-2">
                                                <div class="row g-0">
                                                    <div class="col-md-1 col-4 d-flex align-items-center justify-content-end pl-0">
                                                        <span>
                                                            <svg xmlns="http://www.w3.org/2000/svg" height="60" width="60" viewBox="0 0 24 24">
                                                                <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path>
                                                                <circle cx="12" cy="17" r="1" fill="#e62a45"></circle>
                                                                <path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                            </svg>
                                                        </span>
                                                    </div>
                                                    <div class="col-md-11 col-8">
                                                        <div class="card-body">
                                                            <h4 class="text-white">وضعیت صفحه شما غیرفعال می‌باشد لطفا تا تایید توسط کلینیک صبور باشد</h4>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                {% endif %}

                                <div class="page-header">
                                    <ol class="breadcrumb">
                                        <li class="breadcrumb-item">
                                            <a href="/psychologist/list"><i class="icon icon-list ml-2"></i>لیست متخصصان کلینیک</a>
                                        </li>
                                        <li class="breadcrumb-item text-dark" aria-current="page">
                                            <i class="fa fa-user-circle ml-2"></i>{{ psychologist.profile.first_name }} {{ psychologist.profile.last_name }}
                                        </li>
                                        <li class="breadcrumb-back">
                                            <a href="/psychologist/list" class="btn btn-outline-default fw-900">
                                                بازگشت <i class="mdi mdi-arrow-left-thick"></i>
                                            </a>
                                        </li>
                                    </ol>
                                </div>

                                

                                <div class="row" id="user-profile">
                                    <div class="col-lg-12">
                                        <!-- کارت اصلی پروفایل -->
                                        <div class="card shadow-sm">
                                            <div class="card-body">
                                                <div class="row align-items-start g-3">
                                                    <!-- عکس + اطلاعات -->
                                                    <div class="col-12 col-md-10">
                                                        <div class="d-flex flex-column flex-sm-row align-items-start gap-3">
                                                            <img src="/media/{{ psychologist.profile_picture }}"
                                                                class="card-img-left flex-shrink-0 shadow-sm m-auto"
                                                                style="width: 130px; height: 160px;" 
                                                                alt="{{ psychologist.profile.first_name }} {{ psychologist.profile.last_name }}">

                                                            <div class="NameType flex-grow-1 pt-1">
                                                                <div class="d-flex flex-column flex-sm-row justify-content-between align-items-start gap-2">
                                                                    <div>
                                                                        <h3 class="mb-1 fw-bold">{{ psychologist.profile.first_name }} {{ psychologist.profile.last_name }}</h3>
                                                                        <p class="text-muted mb-0">{{ psychologist.PsychologistType }}</p>
                                                                    </div>
                                                                    {% if is_owner %}
                                                                        <a href="/psychologist/update/{{ psychologist.id }}/" class="btn btn-outline-info border-0 d-flex align-items-center gap-1 text-nowrap">
                                                                            <i class="fa fa-pencil-square-o"></i>
                                                                            <span>ویرایش</span>
                                                                        </a>
                                                                    {% endif %}
                                                                </div>
                                                                
                                                                <div class="mt-3 d-flex flex-column gap-2">
                                                                    {% if membership_card.display_config.code %}
                                                                        <div class="col-lg-3 col-md-4 col-12 px-0 mt-4">
                                                                            <span class="badge bg-primary fs-6 py-2 px-3 col-12">
                                                                                <i class="fa fa-id-card me-1"></i>
                                                                                کد عضویت: <strong>{{ membership_card.code|default:'-' }}</strong>
                                                                            </span>
                                                                        </div>
                                                                    {% endif %}
                                                                    {% if license_card.display_config.code %}
                                                                    <div class="col-lg-3 col-md-4 col-12 px-0">
                                                                        <span class="badge bg-success fs-6 py-2 px-3 col-12">
                                                                            <i class="fa fa-certificate me-1"></i>
                                                                            پروانه اشتغال: <strong>{{ license_card.code|default:'-' }}</strong>
                                                                        </span>
                                                                    </div>
                                                                    {% endif %}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    <!-- دکمه‌های سمت راست -->
                                                    <div class="col-12 col-md-2">
                                                        <div class="d-flex flex-column gap-2 h-100">
                                                            <div class="row g-2">
                                                                <div class="col-6 col-sm-12">
                                                                    <button class="btn btn-primary w-100 disabled"><i class="fa fa-rss"></i> دنبال کردن</button>
                                                                </div>
                                                                <div class="col-6 col-sm-12">
                                                                    <button class="btn btn-secondary w-100 disabled "><i class="fa fa-envelope"></i> پیام</button>
                                                                </div>
                                                            </div>
                                                            <div class="card-footer">
                                                                <div class="social-profile rounded text-center">
                                                                    {% for socialmedia in socialmedias %}
                                                                        <a href="{{socialmedia.platform.url}}/{{socialmedia.url}}/" target="_blanck">
                                                                            <img class="avatar brround avatar-md grayscale" src="/media/{{socialmedia.platform.icon}}" alt="">
                                                                        </a>
                                                                    {% endfor %}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div class="row">
                                            <!-- ستون چپ -->
                                            <div class="col-xl-3">
                                                <!-- روزهای کاری -->
                                                <div class="card">
                                                    <div class="card-header d-flex">
                                                        <div class="card-title">روزهای کاری</div>
                                                    </div>
                                                    {% if not is_accepting_new_patients %}
                                                        <div class="card-alert alert alert-danger mb-0">
                                                            <i class="fe fe-alert-triangle fs-5"></i>
                                                            <span> متخصص مراجع جدید نمی‌پذیرد</span>
                                                        </div>
                                                    {% endif %}
                                                    <div class="card-body"></div>
                                                </div>

                                                <!-- زمینه کاری -->
                                                {% if specialties and specialties.specialties.exists %}
                                                <div class="card">
                                                    <div class="card-header d-flex">
                                                        <div class="card-title">زمینه کاری</div>
                                                        {% if is_owner %}
                                                            <a href="/psychologistspecialties/update/{{psychologist.id}}" class="btn btn-outline-info border-0 mr-auto">
                                                                <i class="fa fa-pencil-square-o"></i> ویرایش
                                                            </a>
                                                        {% endif %}
                                                    </div>
                                                    <div class="card-body">
                                                        <div class="tags">
                                                            {% for specialtie in specialties.specialties.all %}
                                                                <a href="javascript:void(0)" class="btn btn-default-light me-2 mb-2">{{specialtie}}</a>
                                                            {% endfor %}
                                                        </div>
                                                    </div>
                                                </div>
                                                {% endif %}

                                                <!-- تحصیلات -->
                                                {% if degrees %}
                                                    <div class="card">
                                                        <div class="card-header d-flex">
                                                            <div class="card-title">تحصیلات</div>
                                                            {% if is_owner %}
                                                                <a href="/psychologistdegree/list/" class="btn btn-outline-info border-0 mr-auto">
                                                                    <i class="fa fa-pencil-square-o"></i> ویرایش
                                                                </a>
                                                            {% endif %}
                                                        </div>
                                                        <div class="card-body">
                                                            {% for degree in degrees %}
                                                                <div class="main-profile-contact-list">
                                                                    <div class="">
                                                                        <div class="media mb-4 d-flex">
                                                                            
                                                                            
                                                                            <div class="mb-3 mb-sm-0 me-3">
                                                                                {% if degree.display_config.university and degree.display_config.specialization %}
                                                                                    {% if degree.university.icon %}
                                                                                    <img class="avatar brround avatar-md grayscale" src="/media/{{ degree.university.icon }}" alt="">
                                                                                    {% else %}
                                                                                        <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                            <i class="fa fa-university"></i>
                                                                                        </span>
                                                                                    {% endif %}
                                                                                {% else %}
                                                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                                        <i class="fa fa-university"></i>
                                                                                    </span>
                                                                                {% endif %}
                                                                            </div>
                                                                            
                                                                            <div class="media-body">
                                                                                {% if degree.display_config.specialization %}
                                                                                    <span>
                                                                                        {{ degree.get_level_display }}
                                                                                        {{ degree.specialization.field.name|default:"—" }}
                                                                                        {{ degree.specialization.name|default:"—" }} 
                                                                                        {% if degree.display_config.university %}
                                                                                            از دانشگاه
                                                                                            {{ degree.university|default:"—" }}
                                                                                        {% endif %}
                                                                                        {% if degree.display_config.gpa and degree.gpa %}
                                                                                            با معدل {{ degree.gpa }}
                                                                                        {% endif %}
                                                                                    </span>
                                                                                {% endif %}
                                                                                {% if degree.display_config.start_year and degree.start_year %}
                                                                                    </br>
                                                                                    <span>
                                                                                        {% if degree.display_config.start_year and degree.start_year %}
                                                                                            از {{ degree.start_year|to_jalali:"%Y" }}
                                                                                        {% endif %}
                                                                                        
                                                                                        {% if degree.display_config.graduation_year and degree.graduation_year %}
                                                                                            تا {{ degree.graduation_year|to_jalali:"%Y" }}
                                                                                        {% endif %}
                                                                                    </span>
                                                                                {% endif %}

                                                                                <!-- عنوان پایان‌نامه -->
                                                                                {% if degree.display_config.thesis_title and degree.thesis_title %}
                                                                                    <p class="text-muted small">
                                                                                        عنوان پایان نامه : {{ degree.thesis_title }}
                                                                                    </p>
                                                                                {% endif %}

                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            {% endfor %}
                                                        </div>
                                                    </div>
                                                {% endif %}
                                            </div>

                                            <!-- ستون میانی (بخش‌ها) -->
                                            <div class="col-xl-6">
                                                {% if sections %}
                                                    {% for section in sections %}
                                                    <div class="card" style="background-color: {{ section.background_color|default:'#fff' }}; color: {{ section.color|default:'#000' }}; margin-bottom: 20px;">
                                                        <div class="card-header d-flex">
                                                            <div class="card-title">{{ section.section_type }}</div>
                                                            {% if is_owner %}
                                                                <a href="/psychologistsection/update/{{section.id}}/" class="btn btn-outline-info border-0 mr-auto">
                                                                    <i class="fa fa-pencil-square-o"></i> ویرایش
                                                                </a>
                                                            {% endif %}
                                                        </div>
                                                        <div class="card-body">
                                                            {{ section.description|safe }}
                                                        </div>
                                                    </div>
                                                    {% endfor %}
                                                {% endif %}

                                                {% if documents %}
                                                    {% for document in documents %}
                                                    <div class="card">
                                                        <div class="card-header d-flex">
                                                            <div class="card-title">{{ document.get_document_type_display}} - {{ document.title}}</div>
                                                            {% if is_owner %}
                                                                <a href="/psychologistdocument/update/{{document.id}}/" class="btn btn-outline-info border-0 mr-auto">
                                                                    <i class="fa fa-pencil-square-o"></i> ویرایش
                                                                </a>
                                                            {% endif %}
                                                        </div>
                                                        <div class="card-body">
                                                            
                                                            {% if document.document_image and document.display_config.document_image %}
                                                                <img src="/media/{{document.document_image}}" class="card-img-top mb-4" alt="img" style=" height: 300px;">
                                                            {% endif %}
                                                            {% if document.description and document.display_config.description %}
                                                                {{ document.description|safe }}</p>
                                                            {% endif %}
                                                        
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
                            {% endif %}
                        </div>
                    </div>
                </div>
            """

            t = Template(template_string)
            content = t.render(Context({
                'psychologist': psychologist,
                'is_owner': is_owner,
                'is_accepting_new_patients': is_accepting_new_patients,
                'specialties': specialties,
                'sections': sections,
                'degrees':degrees,
                'membership_card':membership_card,
                'license_card':license_card,
                'socialmedias':socialmedias,
                'documents':documents,
            }))

            context = {
                'content': mark_safe(content),
                'extra_css': ['/static/css/psychologist_detail.css'],
                'extra_js': [
                    '/static/js/psychologist_detail.js',
                    '/static/plugins/rating/jquery-rate-picker.js',
                    '/static/plugins/rating/rating-picker.js',
                    '/static/plugins/ratings-2/jquery.star-rating.js',
                    '/static/plugins/ratings-2/star-rating.js'
                ],
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
                PsychologistNewPatients.objects.get_or_create(
                    psychologist=psychologist,
                    defaults={
                        'is_accepting_new_patients': False
                    }
                )
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
                                    <li class="breadcrumb-item text-dark"><i class="fa fa-graduation-cap ml-1"></i>مدارک</li>
                                    
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
                                                {% if not psychologistdocument.is_deleted %}
                                                <a class="btn border-0 text-start side-menu__item tab-btn 
                                                        {% if forloop.first %}active{% endif %}"
                                                    id="tab-btn-{{ psychologistdocument.id }}"
                                                    data-bs-toggle="tab"
                                                    data-bs-target="#document-{{ psychologistdocument.id }}"
                                                    role="tab"
                                                    aria-controls="{{ psychologistdocument.id }}"
                                                    aria-selected="{% if forloop.first %}true{% else %}false{% endif %}"
                                                >
                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                        <i class="side-menu__icon 
                                                        {% if psychologistdocument.document_type == "membership_card" %}
                                                            fa fa-vcard
                                                        {% elif psychologistdocument.document_type == "license_card" %}
                                                            fa fa-drivers-license
                                                        {% else %}
                                                            fa fa-graduation-cap
                                                        {% endif %}
                                                        ">
                                                        </i>
                                                    </span>
                                                    <span class="side-menu__label mr-2">
                                                    {% if psychologistdocument.document_type == "membership_card" %}
                                                        {{ psychologistdocument.get_document_type_display }}
                                                    {% elif psychologistdocument.document_type == "license_card" %}
                                                        {{ psychologistdocument.get_document_type_display }}
                                                    {% else %}
                                                        {{ psychologistdocument.get_document_type_display }} - {{ psychologistdocument.title }} 
                                                    {% endif %}
                                                    </span>
                                                </a>
                                                {% endif %}
                                            {% endfor %}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-xl-9">
                                    <div class="tab-content" id="degreeTabContent">
                                        {% for psychologistdocument in psychologistdocuments %}
                                            {% if not psychologistdocument.is_deleted %}
                                                <div class="tab-pane fade {% if forloop.first %}show active{% endif %}" 
                                                    id="document-{{ psychologistdocument.id }}" 
                                                    role="tabpanel">
                                                    <div class="card">
                                                        <div class="card-header">

                                                            <div class="text-center mr-2 ml-3 mt-3">
                                                                {% if not psychologistdocument.is_active %}
                                                                    <span class="">
                                                                        <svg 
                                                                            xmlns="http://www.w3.org/2000/svg" 
                                                                            height="30" 
                                                                            width="30" 
                                                                            viewBox="0 0 24 24"
                                                                        >
                                                                            <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path><circle cx="12" cy="17" r="1" fill="#e62a45"></circle><path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                                        </svg>
                                                                        </span>
                                                                    <p class="mb-0 fs-10 text-danger">تایید نشده</p>
                                                                {% else %}
                                                                    <span class="">
                                                                        <svg 
                                                                            xmlns="http://www.w3.org/2000/svg" 
                                                                            height="30" 
                                                                            width="30" 
                                                                            viewBox="0 0 24 24"
                                                                        >
                                                                            <path fill="#71d8c9" d="M12,2A10,10,0,1,0,22,12,10.01146,10.01146,0,0,0,12,2Zm5.207,7.61328-6.1875,6.1875a.99963.99963,0,0,1-1.41406,0L6.793,12.98828A.99989.99989,0,0,1,8.207,11.57422l2.10547,2.10547L15.793,8.19922A.99989.99989,0,0,1,17.207,9.61328Z"></path>
                                                                        </svg>
                                                                        </span>
                                                                    <p class="mb-0 fs-10 text-success">تایید شده</p>
                                                                {% endif %}
                                                            </div>

                                                            <h3 class="card-title">
                                                            {% if psychologistdocument.document_type == "membership_card" %}
                                                                {{ psychologistdocument.get_document_type_display }}
                                                            {% elif psychologistdocument.document_type == "license_card" %}
                                                                {{ psychologistdocument.get_document_type_display }}
                                                            {% else %}
                                                                {{ psychologistdocument.get_document_type_display }} - {{ psychologistdocument.title }} 
                                                            {% endif %}
                                                            </span>
                                                            </h3>
                                                            
                                                            <div class="card-options">
                                                                <a href="/psychologistdocument/update/{{ psychologistdocument.id }}" 
                                                                class="me-3 email-icon text-success bg-success-transparent" data-bs-toggle="tooltip" title="ویرایش">
                                                                    <i class="fa fa-pencil-square-o"></i>
                                                                </a>
                                                                <button 
                                                                    class="me-3 email-icon text-danger bg-danger-transparent delete reload-on-success" 
                                                                    data-app="accounts" 
                                                                    data-model="PsychologistDocument"
                                                                    data-id="{{ psychologistdocument.id }}" 
                                                                    data-field="is_deleted"
                                                                    data-title="psychologistdocument"
                                                                    data-confirm="حذف کامل {{psychologistdocument.title}}"
                                                                    data-bs-toggle="tooltip" 
                                                                    title="حذف"
                                                                >
                                                                    <i class="fe fe-trash-2"></i>
                                                                </button>
                                                            </div>
                                                        </div>
                                                        
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
                                                                                class="toggle toggle-sm status-switch 
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
                                                                                class="toggle toggle-sm status-switch 
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
                                                                                class="toggle toggle-sm status-switch 
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
                                                                                class="toggle toggle-sm status-switch 
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

                                            {% endif %}
                                            
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


            else:
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
            else:
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
                                    <li class="breadcrumb-item text-dark"><i class="fa fa-graduation-cap ml-1"></i>مدارک تحصیلی</li>
                                    
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
                                                    مدرک تحصیلی جدید
                                                </a>
                                            </div>
                                            <div class="p-2">
                                            {% for psychologistdegree in psychologistdegrees %}

                                                <a class="btn border-0 text-start side-menu__item tab-btn 
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
                                                        <div class="text-center mr-2 ml-3 mt-3">
                                                            {% if not psychologistdegree.is_active %}
                                                                <span class="">
                                                                    <svg 
                                                                        xmlns="http://www.w3.org/2000/svg" 
                                                                        height="30" 
                                                                        width="30" 
                                                                        viewBox="0 0 24 24"
                                                                    >
                                                                        <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path><circle cx="12" cy="17" r="1" fill="#e62a45"></circle><path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                                    </svg>
                                                                    </span>
                                                                <p class="mb-0 fs-10 text-danger">تایید نشده</p>
                                                            {% else %}
                                                                <span class="">
                                                                    <svg 
                                                                        xmlns="http://www.w3.org/2000/svg" 
                                                                        height="30" 
                                                                        width="30" 
                                                                        viewBox="0 0 24 24"
                                                                    >
                                                                        <path fill="#71d8c9" d="M12,2A10,10,0,1,0,22,12,10.01146,10.01146,0,0,0,12,2Zm5.207,7.61328-6.1875,6.1875a.99963.99963,0,0,1-1.41406,0L6.793,12.98828A.99989.99989,0,0,1,8.207,11.57422l2.10547,2.10547L15.793,8.19922A.99989.99989,0,0,1,17.207,9.61328Z"></path>
                                                                    </svg>
                                                                    </span>
                                                                <p class="mb-0 fs-10 text-success">تایید شده</p>
                                                            {% endif %}
                                                        </div>
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
                                                            class="me-3 email-icon text-success bg-success-transparent" data-bs-toggle="tooltip" title="ویرایش">
                                                                <i class="fa fa-pencil-square-o"></i>
                                                            </a>
                                                            <button 
                                                                class="me-3 email-icon text-danger bg-danger-transparent delete reload-on-success" 
                                                                data-app="accounts" 
                                                                data-model="PsychologistDegree"
                                                                data-id="{{ psychologistdegree.id }}" 
                                                                data-field="is_deleted"
                                                                data-title="psychologistdegree"
                                                                data-confirm="حذف کامل {{psychologistdegree}}"
                                                                data-bs-toggle="tooltip" 
                                                                title="حذف"
                                                            >
                                                                <i class="fe fe-trash-2"></i>
                                                            </button>
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
                                                                        <button
                                                                            type="button"
                                                                            class="toggle toggle-sm status-switch 
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
                                                                            class="toggle toggle-sm status-switch 
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
                                                                            class="toggle toggle-sm status-switch 
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
                                                                            class="toggle toggle-sm status-switch 
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
                                                                            class="toggle toggle-sm status-switch 
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
                                                                            class="toggle toggle-sm status-switch 
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
                                                                            class="toggle toggle-sm status-switch 
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

            else:
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
                    'form_action':reverse('entity-action', kwargs={'subject': 'psychologistdegree','action': 'create'}),
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
            else:
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
    
# ====================== Psychologist Section ======================
class PsychologistSectionView(BaseDashboardView,View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, profile=request.user)
        if not psychologist:
            messages.error(request, "ابتدا پروفایل متخصص خود را تکمیل کنید.")
            return redirect('entity-action-detail', subject='psychologist', action='update', pk=psychologist.pk if psychologist else None)

        psychologistsections=PsychologistSection.objects.filter(psychologist=psychologist)

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
                                <li class="breadcrumb-item text-dark"><i class="fa fa-user ml-1"></i>بیوگرافی</li>
                                
                                <li class="breadcrumb-back">
                                    <a href="/dashboard/psychologist" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                </li>
                            </ol>
                        </div>

                        <div class="row">
                            <!-- Sidebar -->
                            <div class="col-xl-3">
                                <div class="card">
                                    <div class="list-group list-group-transparent mb-0 mail-inbox pb-3">
                                        <div class="mt-4 mx-4 mb-4 text-center">
                                            <a href="/psychologistsection/create" class="btn btn-outline-success btn-lg d-grid">
                                                بخش جدید
                                            </a>
                                        </div>
                                        <div class="p-2">
                                        {% for section in psychologistsections %}
                                            {% if not section.is_deleted %}
                                            <a class="btn border-0 text-start side-menu__item tab-btn 
                                                    {% if forloop.first %}active{% endif %}"
                                                id="tab-btn-{{ section.id }}"
                                                data-bs-toggle="tab"
                                                data-bs-target="#section-{{ section.id }}"
                                                role="tab"
                                                aria-controls="{{ section.id }}"
                                                aria-selected="{% if forloop.first %}true{% else %}false{% endif %}"
                                            >
                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                    <i class="side-menu__icon fa fa-layer-group"></i>
                                                </span>
                                                <span class="side-menu__label mr-2">
                                                    {{ section.section_type.title|default:"بخش بدون عنوان" }}
                                                    {% if section.order %} (ترتیب: {{ section.order }}) {% endif %}
                                                </span>
                                            </a>
                                            {% endif %}
                                        {% endfor %}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Main Content -->
                            <div class="col-xl-9">
                                <div class="tab-content" id="sectionTabContent">
                                    {% for section in psychologistsections %}
                                        {% if not section.is_deleted %}
                                            <div class="tab-pane fade {% if forloop.first %}show active{% endif %}" 
                                                id="section-{{ section.id }}" 
                                                role="tabpanel">
                                                <div class="card">
                                                    <div class="card-header">

                                                        <div class="text-center mr-2 ml-3 mt-3">
                                                            {% if not section.is_active %}
                                                                <span>
                                                                    <svg xmlns="http://www.w3.org/2000/svg" height="30" width="30" viewBox="0 0 24 24">
                                                                        <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path>
                                                                        <circle cx="12" cy="17" r="1" fill="#e62a45"></circle>
                                                                        <path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                                    </svg>
                                                                </span>
                                                                <p class="mb-0 fs-10 text-danger">غیرفعال</p>
                                                            {% else %}
                                                                <span>
                                                                    <svg xmlns="http://www.w3.org/2000/svg" height="30" width="30" viewBox="0 0 24 24">
                                                                        <path fill="#71d8c9" d="M12,2A10,10,0,1,0,22,12,10.01146,10.01146,0,0,0,12,2Zm5.207,7.61328-6.1875,6.1875a.99963.99963,0,0,1-1.41406,0L6.793,12.98828A.99989.99989,0,0,1,8.207,11.57422l2.10547,2.10547L15.793,8.19922A.99989.99989,0,0,1,17.207,9.61328Z"></path>
                                                                    </svg>
                                                                </span>
                                                                <p class="mb-0 fs-10 text-success">فعال</p>
                                                            {% endif %}
                                                        </div>

                                                        <h3 class="card-title">
                                                            {{ section.section_type.title|default:"بخش بدون عنوان" }}
                                                        </h3>
                                                        
                                                        <div class="card-options">
                                                            <a href="/psychologistsection/update/{{ section.id }}" 
                                                            class="me-3 email-icon text-success bg-success-transparent" data-bs-toggle="tooltip" title="ویرایش">
                                                                <i class="fa fa-pencil-square-o"></i>
                                                            </a>
                                                            <button 
                                                                class="me-3 email-icon text-danger bg-danger-transparent delete reload-on-success" 
                                                                data-app="accounts" 
                                                                data-model="PsychologistSection"
                                                                data-id="{{ section.id }}" 
                                                                data-field="is_deleted"
                                                                data-title="section"
                                                                data-confirm="حذف کامل {{ section.section_type.title|default:'این بخش' }}"
                                                                data-bs-toggle="tooltip" 
                                                                title="حذف"
                                                            >
                                                                <i class="fe fe-trash-2"></i>
                                                            </button>
                                                        </div>
                                                    </div>
                                                    
                                                    <div class="card-body">
                                                        <div class="visitor-list">

                                                            <!-- Section Type -->
                                                            <div class="row my-5 align-items-center">
                                                                <div class="col-md-1 col-2 text-center">
                                                                    <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                                        <i class="fa fa-tag"></i>
                                                                    </span>                                                        
                                                                </div>
                                                                <div class="col-md-8 col-5 px-0">
                                                                    {% if section.section_type %}
                                                                        <h5 class="mb-1">{{ section.section_type.title }}</h5>
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
                                                                            class="toggle toggle-sm status-switch 
                                                                            {% if section.display_config.section_type %}active{% endif %}"
                                                                            data-app="accounts" 
                                                                            data-model="PsychologistSection"
                                                                            data-id="{{ section.id }}"
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
                                                                    {% if section.description %}
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
                                                                                {{ section.description|safe }}
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
                                                                            class="toggle toggle-sm status-switch 
                                                                            {% if section.display_config.description %}active{% endif %}"
                                                                            data-app="accounts" 
                                                                            data-model="PsychologistSection"
                                                                            data-id="{{ section.id }}"
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
                                                                    {% if section.order is not None %}
                                                                        <h5 class="mb-1">{{ section.order }}</h5>
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
                                                                    <div style="background-color: {{ section.background_color }}; width: 60px; height: 30px; border: 1px solid #ddd; border-radius: 4px;"></div>
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
                                                                    <div style="background-color: {{ section.color }}; color: white; width: 60px; height: 30px; border: 1px solid #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px;"></div>
                                                                    <p class="text-muted mb-0">رنگ متن</p>
                                                                </div>
                                                            </div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        {% endif %}
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
                'psychologistsections':psychologistsections,
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
            form = PsychologistSectionForm()
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت بیوگرافی',
                'back_url': '/psychologistdegree/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action', kwargs={'subject': 'psychologistsection', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)

        elif action == 'update':
            section = get_object_or_404(PsychologistSection, pk=pk, psychologist=psychologist)
            form = PsychologistSectionForm(instance=section)
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش بیوگرافی',
                'back_url': '/psychologistsection/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistsection', 'action': 'update' , 'pk': section.pk }),
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
            form = PsychologistSectionForm(request.POST, request.FILES)
            if form.is_valid():
                section = form.save(commit=False)
                section.psychologist = psychologist
                section.save()
                messages.success(request, "مدرک تحصیلی با موفقیت ثبت شد.")
                return redirect('entity-action', subject='psychologistsection', action='list')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ثبت بیوگرافی',
                    'back_url': '/psychologistsection/list',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action':reverse('entity-action', kwargs={'subject': 'psychologistsection','action': 'create'}),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block',
                    'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                    'footer_content': ''
                })
            return render(request, 'form.html', base_context)

        elif action == 'update':
            section = get_object_or_404(PsychologistSection, pk=pk, psychologist=psychologist)
            form = PsychologistSectionForm(request.POST, request.FILES, instance=section)

            if form.is_valid():
                form.save()
                messages.success(request, "مدرک تحصیلی با موفقیت ویرایش شد.")
                return redirect('entity-action', subject='psychologistsection', action='list')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }

                base_context.update({
                    'title': 'ویرایش بیوگرافی',
                    'back_url': '/psychologistsection/list',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistsection','action': 'create', 'pk': section.pk }),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block',
                    'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                    'footer_content': ''
                })

            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
            


class PsychologistSocialMediaView(BaseDashboardView,View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, profile=request.user)
        if not psychologist:
            messages.error(request, "ابتدا پروفایل متخصص خود را تکمیل کنید.")
            return redirect('entity-action-detail', subject='psychologist', action='update', pk=psychologist.pk if psychologist else None)

        psychologistsocialmedias=PsychologistSocialMedia.objects.filter(psychologist=psychologist)

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
                                <li class="breadcrumb-item text-dark"><i class="fa fa-share-alt ml-1"></i>شبکه‌های اجتماعی</li>
                                
                                <li class="breadcrumb-back">
                                    <a href="/dashboard/psychologist" class="text-gray fs-6">بازگشت <i class="mdi mdi-arrow-left-thick"></i></a>
                                </li>
                            </ol>
                        </div>

                        <div class="row">
                            <!-- Sidebar -->
                            <div class="col-xl-3">
                                <div class="card">
                                    <div class="list-group list-group-transparent mb-0 mail-inbox pb-3">
                                        <div class="mt-4 mx-4 mb-4 text-center">
                                            <a href="/psychologistsocialmedia/create" class="btn btn-outline-success btn-lg d-grid">
                                                شبکه اجتماعی جدید
                                            </a>
                                        </div>
                                        <div class="p-2">
                                        {% for psychologistsocialmedia in psychologistsocialmedias %}
                                            {% if not psychologistsocialmedia.is_deleted %}
                                            <a class="btn border-0 text-start side-menu__item tab-btn 
                                                    {% if forloop.first %}active{% endif %}"
                                                id="tab-btn-{{ psychologistsocialmedia.id }}"
                                                data-bs-toggle="tab"
                                                data-bs-target="#social-{{ psychologistsocialmedia.id }}"
                                                role="tab"
                                                aria-controls="{{ psychologistsocialmedia.id }}"
                                                aria-selected="{% if forloop.first %}true{% else %}false{% endif %}"
                                            >
                                                <span class="m-auto email-icon text-dark bg-dark-transparent">
                                                    <img class="avatar brround avatar-md grayscale" src="/media/{{psychologistsocialmedia.platform.icon}}" alt="">
                                                </span>
                                                <span class="side-menu__label mr-2">
                                                    {{ psychologistsocialmedia.platform.title|default:"شبکه اجتماعی" }}
                                                </span>
                                            </a>
                                            {% endif %}
                                        {% endfor %}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Main Content -->
                            <div class="col-xl-9">
                                <div class="tab-content" id="socialTabContent">
                                    {% for psychologistsocialmedia in psychologistsocialmedias %}
                                        {% if not psychologistsocialmedia.is_deleted %}
                                            <div class="tab-pane fade {% if forloop.first %}show active{% endif %}" 
                                                id="social-{{ psychologistsocialmedia.id }}" 
                                                role="tabpanel">
                                                <div class="card">
                                                    <div class="card-header">

                                                        <div class="text-center mr-2 ml-3 mt-3">
                                                            {% if not psychologistsocialmedia.is_active %}
                                                                <span>
                                                                    <svg xmlns="http://www.w3.org/2000/svg" height="30" width="30" viewBox="0 0 24 24">
                                                                        <path fill="#f07f8f" d="M20.05713,22H3.94287A3.02288,3.02288,0,0,1,1.3252,17.46631L9.38232,3.51123a3.02272,3.02272,0,0,1,5.23536,0L22.6748,17.46631A3.02288,3.02288,0,0,1,20.05713,22Z"></path>
                                                                        <circle cx="12" cy="17" r="1" fill="#e62a45"></circle>
                                                                        <path fill="#e62a45" d="M12,14a1,1,0,0,1-1-1V9a1,1,0,0,1,2,0v4A1,1,0,0,1,12,14Z"></path>
                                                                    </svg>
                                                                </span>
                                                                <p class="mb-0 fs-10 text-danger">غیرفعال</p>
                                                            {% else %}
                                                                <span>
                                                                    <svg xmlns="http://www.w3.org/2000/svg" height="30" width="30" viewBox="0 0 24 24">
                                                                        <path fill="#71d8c9" d="M12,2A10,10,0,1,0,22,12,10.01146,10.01146,0,0,0,12,2Zm5.207,7.61328-6.1875,6.1875a.99963.99963,0,0,1-1.41406,0L6.793,12.98828A.99989.99989,0,0,1,8.207,11.57422l2.10547,2.10547L15.793,8.19922A.99989.99989,0,0,1,17.207,9.61328Z"></path>
                                                                    </svg>
                                                                </span>
                                                                <p class="mb-0 fs-10 text-success">فعال</p>
                                                            {% endif %}
                                                        </div>

                                                        <h3 class="card-title">
                                                            {{ psychologistsocialmedia.platform.title|default:"شبکه اجتماعی" }}
                                                        </h3>
                                                        
                                                        <div class="card-options">
                                                            <a href="/psychologistsocialmedia/update/{{ psychologistsocialmedia.id }}" 
                                                            class="me-3 email-icon text-success bg-success-transparent" data-bs-toggle="tooltip" title="ویرایش">
                                                                <i class="fa fa-pencil-square-o"></i>
                                                            </a>
                                                            <button 
                                                                class="me-3 email-icon text-danger bg-danger-transparent delete reload-on-success" 
                                                                data-app="accounts" 
                                                                data-model="PsychologistSocialMedia"
                                                                data-id="{{ psychologistsocialmedia.id }}" 
                                                                data-field="is_deleted"
                                                                data-title="socialmedia"
                                                                data-confirm="حذف {{ psychologistsocialmedia.platform.name|default:'این شبکه اجتماعی' }}"
                                                                data-bs-toggle="tooltip" 
                                                                title="حذف"
                                                            >
                                                                <i class="fe fe-trash-2"></i>
                                                            </button>
                                                        </div>
                                                    </div>
                                                    
                                                    <div class="card-body">
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
                                                                            class="toggle toggle-sm status-switch 
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
                                        {% endif %}
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
                'psychologistsocialmedias':psychologistsocialmedias,
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
            form = PsychologistSocialMediaForm()
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ثبت بیوگرافی',
                'back_url': '/psychologistsocialmedia/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action', kwargs={'subject': 'psychologistsocialmedia', 'action': 'create'}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'submit_style': '',
                'card_header_class': 'card-header',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
                'footer_content': ''''''
            })
            
            return render(request, 'form.html', base_context)

        elif action == 'update':
            socialmedia = get_object_or_404(PsychologistSocialMedia, pk=pk, psychologist=psychologist)
            form = PsychologistSocialMediaForm(instance=socialmedia)
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'ویرایش بیوگرافی',
                'back_url': '/psychologistsocialmedia/list',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form':form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': 'psychologistsocialmedia', 'action': 'update' , 'pk': socialmedia.pk }),
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
            form = PsychologistSocialMediaForm(request.POST, request.FILES)
            
            if form.is_valid():
                socialmedia = form.save(commit=False)
                socialmedia.psychologist = psychologist
                socialmedia.save()
                messages.success(request, "شبکه اجتماعی با موفقیت ثبت شد.")
                return redirect('entity-action', subject='psychologistsocialmedia', action='list')
            
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ثبت شبکه اجتماعی',
                    'back_url': '/psychologistsocialmedia/list',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action', kwargs={'subject': 'psychologistsocialmedia', 'action': 'create'}),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block',
                    'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                    'footer_content': ''
                })
            return render(request, 'form.html', base_context)

        elif action == 'update':
            socialmedia = get_object_or_404(PsychologistSocialMedia, pk=pk, psychologist=psychologist)
            form = PsychologistSocialMediaForm(request.POST, request.FILES, instance=socialmedia)
            
            if form.is_valid():
                form.save()
                messages.success(request, "شبکه اجتماعی با موفقیت ویرایش شد.")
                return redirect('entity-action', subject='psychologistsocialmedia', action='list')
            else:
                base_context = {
                    'col_class': 'col-md-5 col-12 m-auto',
                    'card_class': 'card shadow-lg',
                    'card_header_class': 'card-header',
                    'card_body_class': 'card-body p-5',
                }
                base_context.update({
                    'title': 'ویرایش شبکه اجتماعی',
                    'back_url': '/psychologistsocialmedia/list',
                    'back_text': 'بازگشت',
                    'back_class': 'btn btn-default-light',
                    'back_icon': 'fa fa-arrow-left',
                    'form': form,
                    'form_action': reverse('entity-action-detail', kwargs={
                        'subject': 'psychologistsocialmedia', 
                        'action': 'update', 
                        'pk': socialmedia.pk
                    }),
                    'submit_text': 'ذخیره',
                    'submit_class': 'btn btn-success btn-lg btn-block',
                    'card_header_style': 'background-color: #1ab0fc; color: #fff;',
                    'footer_content': ''
                }) 
            
            return render(request, 'form.html', base_context)

        raise Http404("Action not supported")
        
    

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
    
    