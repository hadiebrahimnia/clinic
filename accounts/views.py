from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from accounts.models import *
from django.http import JsonResponse
from accounts.forms import *
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
from django.utils.text import Truncator

class AccountView(View):
    template_name = 'form.html'

    def _get_form_context(self, request, action, form=None):
        """Context پایه برای همه فرم‌ها"""
        base_context = {
            'col_class': 'col-md-4 col-12 m-auto',
            'card_class': 'card shadow-lg',
            'card_header_class': 'card-header',
            'card_body_class': 'card-body p-4',
        }
        
        if action == 'register':
            base_context.update({
                'title': 'ثبت‌نام',
                'back_url': '/',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-outline-secondary',
                'back_icon': 'mdi mdi-arrow-left-thick',
                'form_action': reverse('accounts', args=['register']),
                'submit_text': 'ثبت‌نام',
                'submit_class': 'btn btn-primary btn-block w-100',
                'submit_style': '',
                'card_header_class': 'card-header text-dark',
            })
        
        elif action == 'login':
            base_context.update({
                'title': 'ورود به حساب کاربری',
                'back_url': '/',
                'back_text': 'بازگشت',
                'back_class': 'btn btn-outline-secondary',
                'back_icon': 'mdi mdi-home',
                'form_action': reverse('accounts', args=['login']),
                'submit_text': 'ورود',
                'submit_class': 'btn btn-success btn-block w-100',
                'card_header_class': 'card-header bg-success text-white',
            })
        
        elif action == 'profile':
            if not request.user.is_authenticated:
                return redirect('accounts', action='login')
            
            base_context.update({
                'title': 'ویرایش پروفایل',
                'back_url': '/',
                'back_text': 'صفحه اصلی',
                'back_class': 'btn btn-outline-secondary',
                'back_icon': 'mdi mdi-home',
                'form_action': reverse('accounts', args=['profile']),
                'submit_text': 'به‌روزرسانی پروفایل',
                'submit_class': 'btn btn-info btn-block w-100',
                'card_header_class': 'card-header bg-info text-white',
            })
        
        # اضافه کردن فرم
        if form:
            base_context['form'] = form
        
        return base_context

    def get(self, request, action):
        if action == 'logout':
            logout(request)
            messages.success(request, 'با موفقیت از سیستم خارج شدید.')
            return redirect('accounts', action='login')

        if action == 'register':
            form = CustomUserCreationForm()
        elif action == 'login':
            form = CustomAuthenticationForm()
        elif action == 'profile':
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')
            form = ProfileUpdateForm(user=request.user, instance=request.user)
        else:
            messages.error(request, 'عملیات نامعتبر است.')
            return redirect('accounts', action='login')

        context = self._get_form_context(request, action, form)
        return render(request, self.template_name, context)

    def post(self, request, action):
        if action == 'register':
            form = CustomUserCreationForm(request.POST, request.FILES)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'ثبت‌نام با موفقیت انجام شد! به پروفایل خود خوش آمدید.')
                return redirect('accounts', action='profile')
            
        elif action == 'login':
            form = CustomAuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    messages.success(request, 'با موفقیت وارد شدید.')
                    return redirect('accounts', action='profile')
                else:
                    messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
        
        elif action == 'profile':
            if not request.user.is_authenticated:
                messages.error(request, 'برای دسترسی به پروفایل باید وارد شوید.')
                return redirect('accounts', action='login')
            
            form = ProfileUpdateForm(request.POST, request.FILES, user=request.user, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'پروفایل با موفقیت به‌روزرسانی شد.')
                return redirect('accounts', action='profile')
        
        else:
            messages.error(request, 'عملیات نامعتبر است.')
            return redirect('accounts', action='login')

        # در صورت خطا، فرم را با خطاها نمایش بده
        context = self._get_form_context(request, action, form)
        return render(request, self.template_name, context)
    
class PsychologistActionView(View):
    def get(self, request, subject, action, pk=None):
        if action == 'list':
            search_query = request.GET.get('search', '').strip()
            specialty_filter = request.GET.get('specialty', '').strip()
            page_number = request.GET.get('page', 1)
            
            psychologists = Psychologist.objects.all()
            if search_query:
                psychologists = psychologists.filter(name__icontains=search_query)
            if specialty_filter:
                psychologists = psychologists.filter(specialty__icontains=specialty_filter)

            paginator = Paginator(psychologists, 12)
            page_obj = paginator.get_page(page_number)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'html': self._render_cards_html(page_obj),
                    'pagination': self._render_pagination(page_obj, search_query, specialty_filter),
                })

            context = {
                'page_title': 'لیست روانشناسان',
                'extra_css': ['/static/css/psychologist_list.css'],
                'extra_js': ['/static/js/psychologist_list.js'],
                'content': self._render_full_list_page(page_obj, search_query, specialty_filter),
            }
            return render(request, 'index2.html', context)

        elif action == 'detail' and pk:
            psychologist = get_object_or_404(Psychologist, pk=pk)
            full_name = f"{psychologist.profile.first_name or ''} {psychologist.profile.last_name or ''}".strip()
            context = {
                'page_title': full_name,
                'extra_css': ['/static/css/psychologist_detail.css'],
                'extra_js': ['/static/js/psychologist_detail.js'],
                'content': render_psychologist_detail(psychologist),
            }
            return render(request, 'index2.html', context)

        else:
            raise Http404("Action not supported")

    # ========== متدهای کمکی (داخل کلاس) ==========

    def _render_full_list_page(self, page_obj, search_query='', specialties_filter=''):
        # لیست تخصص‌ها
        specialties = Specialty.objects.values_list('name', flat=True).distinct().order_by('name')

        # --- فرم فیلتر (ستون چپ) ---
        options_html = ''
        for s in specialties:
            selected = ' selected' if s == specialties_filter else ''
            options_html += f'<option value="{s}"{selected}>{s}</option>'

        filter_sidebar = f'''
        <div class="card shadow-sm">
            <div class="card-body">
                <h5 class="card-title mb-3">فیلترها</h5>
                <form id="filter-form" method="get">
                    <div class="mb-3">
                        <input type="text" class="form-control" name="search" placeholder="جستجو در نام..." 
                            value="{search_query}" id="search-input">
                    </div>
                    <div class="mb-3">
                        <select class="form-select" name="specialties" id="specialties-filter">
                            <option value="">همه تخصص‌ها</option>
                            {options_html}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">اعمال فیلتر</button>
                </form>
            </div>
        </div>
        '''

        # --- صفحه‌بندی ---
        pagination_html = self._render_pagination(page_obj, search_query, specialties_filter)

        # --- لیست کارت‌ها ---
        cards_html = self._render_cards_html(page_obj)

        # --- چیدمان نهایی ---
        full_page = f'''
        <div class="main-content">
            <div class="side-app with_header">
                <div class="main-container container-fluid">
                <div class="page-header">
                    <ol class="breadcrumb">
                    <li class="breadcrumb-item text-dark" aria-current="page">
                        <i class="icon icon-list ml-2"></i>لیست متخصصان کلینیک
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
                        <div class="col-lg-3 mb-4">
                            {filter_sidebar}
                        </div>
                        <div class="col-lg-9">
                            <div id="psychologists-container">
                                {cards_html}
                            </div>
                            <div id="pagination-container" class="d-flex justify-content-center mt-4">
                                {pagination_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>






        '''
        return mark_safe(full_page)

    def _render_cards_html(self, page_obj):
        cards = []
        for p in page_obj:
            # --- عکس ---
            if p.profile_picture:
                photo = f'<img src="{p.profile_picture.url}" class="card-img-left rounded-start h-100" alt="{p.profile.first_name or p.profile.username}" style="object-fit: cover; width: 100%;">'
            else:
                photo = '<div class="bg-light d-flex align-items-center justify-content-center h-100 rounded-start" style="min-height: 180px;"><i class="fas fa-user-md fa-4x text-muted"></i></div>'

            full_name = f"{p.profile.first_name or ''} {p.profile.last_name or ''}".strip()
            if not full_name:
                full_name = p.profile.username or "نامشخص"

            specs = [s.name for s in p.specialties.all()]
            specialties_text = ', '.join(specs) if specs else 'تخصصی ثبت نشده'

            bio = p.bio or 'در حال تکمیل بیوگرافی...'
            bio_snippet = bio[:180]
            if len(bio) > 180:
                bio_snippet += '...'

            # --- لینک ---
            detail_url = reverse('entity-detail', kwargs={'subject': 'psychologist', 'action': 'detail', 'pk': p.pk})

            # --- کارت افقی ---
            card = f'''
            <a href="{detail_url}" class="card mb-3 doctor-card shadow-sm animate-card border-0 text-decoration-none">
                <div class="row g-0 align-items-center">
                    <div class="col-md-2 position-relative overflow-hidden">
                        {photo}
                    </div>
                    <div class="col-md-10">
                        <div class="card-body">
                            <h5 class="card-title mb-2">{full_name}</h5>
                            <p class="card-text text-muted mb-2">
                                <strong>تخصص:</strong> {specialties_text}
                                <span class="specialty-badge">{specialties_text}</span>
                            </p>
                            <p class="card-text bio-snippet">{bio_snippet}</p>
                        </div>
                    </div>
                </div>
            </a>
            '''
            cards.append(card)

        if not cards:
            cards.append('<div class="text-center py-5 text-muted">هیچ روانشناسی یافت نشد.</div>')

        return ''.join(cards)

    def _render_pagination(self, page_obj, search_query='', specialty_filter=''):
        if page_obj.paginator.num_pages <= 1:
            return ''

        items = []
        if page_obj.has_previous():
            items.append(self._page_link(page_obj.previous_page_number(), 'قبلی', search_query, specialty_filter))

        for num in page_obj.paginator.page_range:
            if num == page_obj.number:
                items.append(f'<li class="page-item active"><span class="page-link">{num}</span></li>')
            else:
                items.append(self._page_link(num, num, search_query, specialty_filter))

        if page_obj.has_next():
            items.append(self._page_link(page_obj.next_page_number(), 'بعدی', search_query, specialty_filter))

        return mark_safe('<nav><ul class="pagination">' + ''.join(items) + '</ul></nav>')

    def _page_link(self, page, text, search_query, specialty_filter):
        params = {}
        if page != 1:
            params['page'] = page
        if search_query:
            params['search'] = search_query
        if specialty_filter:
            params['specialty'] = specialty_filter

        query_string = urlencode(params)
        full_url = f"?{query_string}" if query_string else "?"

        return f'<li class="page-item"><a class="page-link" href="#" data-page-url="{full_url}">{text}</a></li>'
    

def render_psychologist_detail(psychologist):
    full_name = f"{psychologist.profile.first_name or ''} {psychologist.profile.last_name or ''}".strip()
    profile_picture=psychologist.profile_picture
    banner_image=psychologist.banner_image


    # --- HTML نهایی ---
    html = format_html(f"""

        <div class="main-content">
                       
            <div class="side-app with_header">
                <div class="main-container container-fluid">
                    <div class="page-header">
                        <ol class="breadcrumb">
                        <li class="breadcrumb-item">
                            <a href="psychologist/list"><i class="icon icon-list ml-2"></i>لیست متخصصان کلینیک</a>
                        </li>
                        <li class="breadcrumb-item text-dark" aria-current="page">
                            <i class="fa fa-user-circle ml-2"></i>{full_name}
                        </li>
                        
                        <li class="breadcrumb-back">
                            <a href="/" class="btn btn-outline-default fw-900"
                            >بازگشت
                            <i class="mdi mdi-arrow-left-thick"></i>
                            </a>
                        </li>
                        </ol>
                    </div>
                    

                    <div class="row" id="user-profile">
                            <div class="col-lg-12">
                                <div class="card">
                                    <div class="card-body">
                                        <div class="wideget-user mb-2">
                                            <div class="row">
                                                <div class="col-lg-12 col-md-12">
                                                    <div class="row">
                                                        <div class="panel profile-cover">
                                                            <div class="profile-cover__action bg-img" style=" background-image: url('/{banner_image}'); "></div>
                                                            <div class="profile-cover__img">
                                                                <div class="profile-img-1">
                                                                    <img src="/{profile_picture}" alt="img">
                                                                </div>
                                                                <div class="profile-img-content text-dark text-start">
                                                                    <div class="text-dark">
                                                                        <h3 class="h3 mb-2">{full_name}</h3>
                                                                        <h5 class="text-muted">Web Developer</h5>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div class="btn-profile">
                                                                <button class="btn btn-primary mt-1 mb-1"> <i class="fa fa-rss"></i> <span>Follow</span></button>
                                                                <button class="btn btn-secondary mt-1 mb-1"> <i class="fa fa-envelope"></i> <span>Message</span></button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="px-0 px-sm-4">
                                                            <div class="social social-profile-buttons mt-5 float-end">
                                                                <div class="mt-3">
                                                                    <a class="social-icon text-primary" href="https://www.facebook.com/" target="_blank"><i class="fa fa-facebook"></i></a>
                                                                    <a class="social-icon text-primary" href="https://twitter.com/" target="_blank"><i class="fa fa-twitter"></i></a>
                                                                    <a class="social-icon text-primary" href="https://www.youtube.com/" target="_blank"><i class="fa fa-youtube"></i></a>
                                                                    <a class="social-icon text-primary" href="javascript:void(0)"><i class="fa fa-rss"></i></a>
                                                                    <a class="social-icon text-primary" href="https://www.linkedin.com/" target="_blank"><i class="fa fa-linkedin"></i></a>
                                                                    <a class="social-icon text-primary" href="https://myaccount.google.com/" target="_blank"><i class="fa fa-google-plus"></i></a>
                                                                </div>
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
                                            <div class="card-body">
                                                <div class="main-profile-contact-list">
                                                    <div class="me-5">
                                                        <div class="media mb-4 d-flex">
                                                            <div class="media-icon bg-secondary bradius me-3 mt-1">
                                                                <i class="fe fe-edit fs-20 text-white"></i>
                                                            </div>
                                                            <div class="media-body">
                                                                <span class="text-muted">Posts</span>
                                                                <div class="fw-semibold fs-25">
                                                                    328
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
                                                                <span class="text-muted">Followers</span>
                                                                <div class="fw-semibold fs-25">
                                                                    937k
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
                                                                <span class="text-muted">Following</span>
                                                                <div class="fw-semibold fs-25">
                                                                    2,876
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card">
                                            <div class="card-header">
                                                <div class="card-title">About</div>
                                            </div>
                                            <div class="card-body">
                                                <div>
                                                    <h5>Biography<i class="fe fe-edit-3 text-primary mx-2"></i></h5>
                                                    <p>Nor again is there anyone who loves or pursues or desires to obtain pain of itself, because it is pain, but because occasionally circumstances occur in which toil and pain can procure him some great pleasure.
                                                        <a href="javascript:void(0)">Read more</a>
                                                    </p>
                                                </div>
                                                <hr>
                                                <div class="d-flex align-items-center mb-3 mt-3">
                                                    <div class="me-4 text-center text-primary">
                                                        <span><i class="fe fe-briefcase fs-20"></i></span>
                                                    </div>
                                                    <div>
                                                        <strong>San Francisco, CA </strong>
                                                    </div>
                                                </div>
                                                <div class="d-flex align-items-center mb-3 mt-3">
                                                    <div class="me-4 text-center text-primary">
                                                        <span><i class="fe fe-map-pin fs-20"></i></span>
                                                    </div>
                                                    <div>
                                                        <strong>Francisco, USA</strong>
                                                    </div>
                                                </div>
                                                <div class="d-flex align-items-center mb-3 mt-3">
                                                    <div class="me-4 text-center text-primary">
                                                        <span><i class="fe fe-phone fs-20"></i></span>
                                                    </div>
                                                    <div>
                                                        <strong>+125 254 3562 </strong>
                                                    </div>
                                                </div>
                                                <div class="d-flex align-items-center mb-3 mt-3">
                                                    <div class="me-4 text-center text-primary">
                                                        <span><i class="fe fe-mail fs-20"></i></span>
                                                    </div>
                                                    <div>
                                                        <strong>georgeme@abc.com </strong>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card">
                                            <div class="card-header">
                                                <div class="card-title">Skills</div>
                                            </div>
                                            <div class="card-body">
                                                <div class="tags">
                                                    <a href="javascript:void(0)" class="tag">Laravel</a>
                                                    <a href="javascript:void(0)" class="tag">Angular</a>
                                                    <a href="javascript:void(0)" class="tag">HTML</a>
                                                    <a href="javascript:void(0)" class="tag">Vuejs</a>
                                                    <a href="javascript:void(0)" class="tag">Codiegniter</a>
                                                    <a href="javascript:void(0)" class="tag">JavaScript</a>
                                                    <a href="javascript:void(0)" class="tag">Bootstrap</a>
                                                    <a href="javascript:void(0)" class="tag">PHP</a>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card">
                                            <div class="card-header">
                                                <div class="card-title">Work &amp; Education</div>
                                            </div>
                                            <div class="card-body">
                                                <div class="main-profile-contact-list">
                                                    <div class="me-5">
                                                        <div class="media mb-4 d-flex">
                                                            <div class="media-icon bg-primary  mb-3 mb-sm-0 me-3 mt-1">
                                                                <svg style="width:24px;height:24px;margin-top:-8px" viewBox="0 0 24 24">
                                                                    <path fill="#fff" d="M12 3L1 9L5 11.18V17.18L12 21L19 17.18V11.18L21 10.09V17H23V9L12 3M18.82 9L12 12.72L5.18 9L12 5.28L18.82 9M17 16L12 18.72L7 16V12.27L12 15L17 12.27V16Z"></path>
                                                                </svg>
                                                            </div>
                                                            <div class="media-body">
                                                                <h6 class="font-weight-semibold mb-1">Web Designer at <a href="javascript:void(0)" class="btn-link">Spruko</a></h6>
                                                                <span>2018 - present</span>
                                                                <p>Past Work: Spruko, Inc.</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="me-5 mt-5 mt-md-0">
                                                        <div class="media mb-4 d-flex">
                                                            <div class="media-icon bg-success text-white mb-3 mb-sm-0 me-3 mt-1">
                                                                <svg style="width:24px;height:24px;margin-top:-8px" viewBox="0 0 24 24">
                                                                    <path fill="currentColor" d="M20,6C20.58,6 21.05,6.2 21.42,6.59C21.8,7 22,7.45 22,8V19C22,19.55 21.8,20 21.42,20.41C21.05,20.8 20.58,21 20,21H4C3.42,21 2.95,20.8 2.58,20.41C2.2,20 2,19.55 2,19V8C2,7.45 2.2,7 2.58,6.59C2.95,6.2 3.42,6 4,6H8V4C8,3.42 8.2,2.95 8.58,2.58C8.95,2.2 9.42,2 10,2H14C14.58,2 15.05,2.2 15.42,2.58C15.8,2.95 16,3.42 16,4V6H20M4,8V19H20V8H4M14,6V4H10V6H14M12,9A2.25,2.25 0 0,1 14.25,11.25C14.25,12.5 13.24,13.5 12,13.5A2.25,2.25 0 0,1 9.75,11.25C9.75,10 10.76,9 12,9M16.5,18H7.5V16.88C7.5,15.63 9.5,14.63 12,14.63C14.5,14.63 16.5,15.63 16.5,16.88V18Z"></path>
                                                                </svg>
                                                            </div>
                                                            <div class="media-body">
                                                                <h6 class="font-weight-semibold mb-1">Studied at <a href="javascript:void(0)" class="btn-link">University</a></h6>
                                                                <span>2004-2008</span>
                                                                <p>Graduation: Bachelor of Science in Computer Science</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-xl-6">
                                        <div class="card">
                                            <div class="card-body">
                                                <form class="profile-edit">
                                                    <textarea class="form-control" placeholder="What's in your mind right now" rows="7"></textarea>
                                                    <div class="profile-share border-top-0">
                                                        <div class="mt-2">
                                                            <a href="javascript:void(0)" class="me-2" title="" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Audio" aria-label="Audio"><span class="text-muted"><i class="fe fe-mic"></i></span></a>
                                                            <a href="javascript:void(0)" class="me-2" title="" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Video" aria-label="Video"><span class="text-muted"><i class="fe fe-video"></i></span></a>
                                                            <a href="javascript:void(0)" class="me-2" title="" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-original-title="Image" aria-label="Image"><span class="text-muted"><i class="fe fe-image"></i></span></a>
                                                        </div>
                                                        <button class="btn btn-sm btn-success ms-auto"><i class="fa fa-share ms-1"></i> Share</button>
                                                    </div>
                                                </form>
                                            </div>
                                        </div>
                                        <div class="card border p-0 shadow-none">
                                            <div class="card-body">
                                                <div class="d-flex">
                                                    <div class="media mt-0">
                                                        <div class="media-user me-2">
                                                            <div class=""><img alt="" class="rounded-circle avatar avatar-md" src="../assets/images/users/16.jpg"></div>
                                                        </div>
                                                        <div class="media-body">
                                                            <h6 class="mb-0 mt-1">Peter Hill</h6>
                                                            <small class="text-muted">just now</small>
                                                        </div>
                                                    </div>
                                                    <div class="ms-auto">
                                                        <div class="dropdown show">
                                                            <a class="new option-dots" href="JavaScript:void(0);" data-bs-toggle="dropdown">
                                                                <span class=""><i class="fe fe-more-vertical"></i></span>
                                                            </a>
                                                            <div class="dropdown-menu dropdown-menu-end">
                                                                <a class="dropdown-item" href="javascript:void(0)">Edit Post</a>
                                                                <a class="dropdown-item" href="javascript:void(0)">Delete Post</a>
                                                                <a class="dropdown-item" href="javascript:void(0)">Personal Settings</a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="mt-4">
                                                    <h4 class="fw-semibold mt-3">There is nothing more beautiful.</h4>
                                                    <p class="mb-0">There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable.
                                                    </p>
                                                </div>
                                            </div>
                                            <div class="card-footer user-pro-2">
                                                <div class="media mt-0">
                                                    <div class="media-user me-2">
                                                        <div class="avatar-list avatar-list-stacked">
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/12.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/2.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/9.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/2.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/4.jpg)"></span>
                                                            <span class="avatar brround text-primary">+28</span>
                                                        </div>
                                                    </div>
                                                    <div class="media-body">
                                                        <h6 class="mb-0 mt-2 ms-2">28 people like your photo</h6>
                                                    </div>
                                                    <div class="ms-auto">
                                                        <div class="d-flex mt-1">
                                                            <a class="new me-2 text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-heart"></i></span></a>
                                                            <a class="new me-2 text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-message-square"></i></span></a>
                                                            <a class="new text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-share-2"></i></span></a>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card border p-0 shadow-none">
                                            <div class="card-body">
                                                <div class="d-flex">
                                                    <div class="media mt-0">
                                                        <div class="media-user me-2">
                                                            <div class=""><img alt="" class="rounded-circle avatar avatar-md" src="../assets/images/users/16.jpg"></div>
                                                        </div>
                                                        <div class="media-body">
                                                            <h6 class="mb-0 mt-1">Peter Hill</h6>
                                                            <small class="text-muted">Sep 26 2019, 10:14am</small>
                                                        </div>
                                                    </div>
                                                    <div class="ms-auto">
                                                        <div class="dropdown show">
                                                            <a class="new option-dots" href="JavaScript:void(0);" data-bs-toggle="dropdown">
                                                                <span class=""><i class="fe fe-more-vertical"></i></span>
                                                            </a>
                                                            <div class="dropdown-menu dropdown-menu-end">
                                                                <a class="dropdown-item" href="javascript:void(0)">Edit Post</a>
                                                                <a class="dropdown-item" href="javascript:void(0)">Delete Post</a>
                                                                <a class="dropdown-item" href="javascript:void(0)">Personal Settings</a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="mt-4">
                                                    <div class="d-flex">
                                                        <a href="gallery.html" class="w-30 m-2"><img src="../assets/images/media/22.jpg" alt="img" class="br-5"></a>
                                                        <a href="gallery.html" class="w-30 m-2"><img src="../assets/images//media/24.jpg" alt="img" class="br-5"></a>
                                                    </div>
                                                    <h4 class="fw-semibold mt-3">There is nothing more beautiful.</h4>
                                                    <p class="mb-0">There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable.
                                                    </p>
                                                </div>
                                            </div>
                                            <div class="card-footer user-pro-2">
                                                <div class="media mt-0">
                                                    <div class="media-user me-2">
                                                        <div class="avatar-list avatar-list-stacked">
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/12.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/2.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/9.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/2.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/4.jpg)"></span>
                                                            <span class="avatar brround text-primary">+28</span>
                                                        </div>
                                                    </div>
                                                    <div class="media-body">
                                                        <h6 class="mb-0 mt-2 ms-2">28 people like your photo</h6>
                                                    </div>
                                                    <div class="ms-auto">
                                                        <div class="d-flex mt-1">
                                                            <a class="new me-2 text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-heart"></i></span></a>
                                                            <a class="new me-2 text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-message-square"></i></span></a>
                                                            <a class="new text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-share-2"></i></span></a>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card border p-0 shadow-none">
                                            <div class="card-body">
                                                <div class="d-flex">
                                                    <div class="media mt-0">
                                                        <div class="media-user me-2">
                                                            <div class=""><img alt="" class="rounded-circle avatar avatar-md" src="../assets/images/users/16.jpg"></div>
                                                        </div>
                                                        <div class="media-body">
                                                            <h6 class="mb-0 mt-1">Peter Hill</h6>
                                                            <small class="text-muted">Sep 24 2019, 09:14am</small>
                                                        </div>
                                                    </div>
                                                    <div class="ms-auto">
                                                        <div class="dropdown show">
                                                            <a class="new option-dots" href="JavaScript:void(0);" data-bs-toggle="dropdown">
                                                                <span class=""><i class="fe fe-more-vertical"></i></span>
                                                            </a>
                                                            <div class="dropdown-menu dropdown-menu-end">
                                                                <a class="dropdown-item" href="javascript:void(0)">Edit Post</a>
                                                                <a class="dropdown-item" href="javascript:void(0)">Delete Post</a>
                                                                <a class="dropdown-item" href="javascript:void(0)">Personal Settings</a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="mt-4">
                                                    <div class="d-flex">
                                                        <a href="gallery.html" class="w-30 m-2"><img src="../assets/images/media/26.jpg" alt="img" class="br-5"></a>
                                                        <a href="gallery.html" class="w-30 m-2"><img src="../assets/images/media/23.jpg" alt="img" class="br-5"></a>
                                                        <a href="gallery.html" class="w-30 m-2"><img src="../assets/images/media/21.jpg" alt="img" class="br-5"></a>
                                                    </div>
                                                    <h4 class="fw-semibold mt-3">There is nothing more beautiful.</h4>
                                                    <p class="mb-0">There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look even slightly believable.
                                                    </p>
                                                </div>
                                            </div>
                                            <div class="card-footer user-pro-2">
                                                <div class="media mt-0">
                                                    <div class="media-user me-2">
                                                        <div class="avatar-list avatar-list-stacked">
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/12.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/2.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/9.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/2.jpg)"></span>
                                                            <span class="avatar brround" style="background-image: url(../assets/images/users/4.jpg)"></span>
                                                            <span class="avatar brround text-primary">+28</span>
                                                        </div>
                                                    </div>
                                                    <div class="media-body">
                                                        <h6 class="mb-0 mt-2 ms-2">28 people like your photo</h6>
                                                    </div>
                                                    <div class="ms-auto">
                                                        <div class="d-flex mt-1">
                                                            <a class="new me-2 text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-heart"></i></span></a>
                                                            <a class="new me-2 text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-message-square"></i></span></a>
                                                            <a class="new text-muted fs-16" href="JavaScript:void(0);"><span class=""><i class="fe fe-share-2"></i></span></a>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-xl-3">
                                        <div class="card">
                                            <div class="card-header">
                                                <div class="card-title">Followers</div>
                                            </div>
                                            <div class="card-body">
                                                <div class="">
                                                    <div class="media overflow-visible">
                                                        <img class="avatar brround avatar-md me-3" src="../assets/images/users/18.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle mt-2">
                                                            <a href="javascript:void(0)" class=" fw-semibold text-dark">John Paige</a>
                                                            <p class="text-muted mb-0">johan@gmail.com</p>
                                                        </div>
                                                        <div class="media-body valign-middle text-end overflow-visible mt-2">
                                                            <button class="btn btn-sm btn-primary" type="button">Follow</button>
                                                        </div>
                                                    </div>
                                                    <div class="media overflow-visible mt-sm-5">
                                                        <span class="avatar cover-image avatar-md brround bg-pink me-3">LQ</span>
                                                        <div class="media-body valign-middle mt-2">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Lillian Quinn</a>
                                                            <p class="text-muted mb-0">lilliangore</p>
                                                        </div>
                                                        <div class="media-body valign-middle text-end overflow-visible mt-1">
                                                            <button class="btn btn-sm btn-secondary" type="button">Follow</button>
                                                        </div>
                                                    </div>
                                                    <div class="media overflow-visible mt-sm-5">
                                                        <img class="avatar brround avatar-md me-3" src="../assets/images/users/2.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle mt-2">
                                                            <a href="javascript:void(0)" class="text-dark fw-semibold">Harry Fisher</a>
                                                            <p class="text-muted mb-0">harryuqt</p>
                                                        </div>
                                                        <div class="media-body valign-middle text-end overflow-visible mt-1">
                                                            <button class="btn btn-sm btn-danger" type="button">Follow</button>
                                                        </div>
                                                    </div>
                                                    <div class="media overflow-visible mt-sm-5">
                                                        <span class="avatar cover-image avatar-md brround me-3 bg-primary">IH</span>
                                                        <div class="media-body valign-middle mt-2">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Irene Harris</a>
                                                            <p class="text-muted mb-0">harris@gmail.com</p>
                                                        </div>
                                                        <div class="media-body valign-middle text-end overflow-visible mt-1">
                                                            <button class="btn btn-sm btn-success" type="button">Follow</button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card">
                                            <div class="card-header">
                                                <div class="card-title">Our Latest News</div>
                                            </div>
                                            <div class="card-body">
                                                <div class="">
                                                    <div class="media media-xs overflow-visible">
                                                        <img class="avatar bradius avatar-xl me-3" src="../assets/images/users/12.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">John Paige</a>
                                                            <p class="text-muted mb-0">There are many variations of passages of Lorem Ipsum available ...</p>
                                                        </div>
                                                    </div>
                                                    <div class="media media-xs overflow-visible mt-5">
                                                        <img class="avatar bradius avatar-xl me-3" src="../assets/images/users/2.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Peter Hill</a>
                                                            <p class="text-muted mb-0">There are many variations of passages of Lorem Ipsum available ...</p>
                                                        </div>
                                                    </div>
                                                    <div class="media media-xs overflow-visible mt-5">
                                                        <img class="avatar bradius avatar-xl me-3" src="../assets/images/users/9.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Irene Harris</a>
                                                            <p class="text-muted mb-0">There are many variations of passages of Lorem Ipsum available ...</p>
                                                        </div>
                                                    </div>
                                                    <div class="media media-xs overflow-visible mt-5">
                                                        <img class="avatar bradius avatar-xl me-3" src="../assets/images/users/4.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Harry Fisher</a>
                                                            <p class="text-muted mb-0">There are many variations of passages of Lorem Ipsum available ...</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="card">
                                            <div class="card-header">
                                                <div class="card-title">Friends</div>
                                            </div>
                                            <div class="card-body">
                                                <div class="user-pro-1">
                                                    <div class="media media-xs overflow-visible">
                                                        <img class="avatar brround avatar-md me-3" src="../assets/images/users/18.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle">
                                                            <a href="javascript:void(0)" class=" fw-semibold text-dark">John Paige</a>
                                                            <p class="text-muted mb-0">Web Designer</p>
                                                        </div>
                                                        <div class="">
                                                            <div class="social social-profile-buttons float-end">
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-facebook"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-twitter"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-linkedin"></i></a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="media media-xs overflow-visible mt-5">
                                                        <span class="avatar cover-image avatar-md brround bg-pink me-3">LQ</span>
                                                        <div class="media-body valign-middle mt-0">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Lillian Quinn</a>
                                                            <p class="text-muted mb-0">Web Designer</p>
                                                        </div>
                                                        <div class="">
                                                            <div class="social social-profile-buttons float-end">
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-facebook"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-twitter"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-linkedin"></i></a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="media media-xs overflow-visible mt-5">
                                                        <img class="avatar brround avatar-md me-3" src="../assets/images/users/2.jpg" alt="avatar-img">
                                                        <div class="media-body valign-middle mt-0">
                                                            <a href="javascript:void(0)" class="text-dark fw-semibold">Harry Fisher</a>
                                                            <p class="text-muted mb-0">Web Designer</p>
                                                        </div>
                                                        <div class="">
                                                            <div class="social social-profile-buttons float-end">
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-facebook"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-twitter"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-linkedin"></i></a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="media media-xs overflow-visible mt-5">
                                                        <span class="avatar cover-image avatar-md brround me-3 bg-primary">IH</span>
                                                        <div class="media-body valign-middle mt-0">
                                                            <a href="javascript:void(0)" class="fw-semibold text-dark">Irene Harris</a>
                                                            <p class="text-muted mb-0">Web Designer</p>
                                                        </div>
                                                        <div class="">
                                                            <div class="social social-profile-buttons float-end">
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-facebook"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-twitter"></i></a>
                                                                <a class="social-icon bg-white" href="javascript:void(0)"><i class="fa fa-linkedin"></i></a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <!-- COL-END -->
                        </div>


                </div>
            </div>

        </div>
    
    """)

    return mark_safe(html)