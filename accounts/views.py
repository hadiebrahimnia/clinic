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
            return render(request, 'index3.html', context)

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
    """
    Returns HTML content for a single psychologist detail page.
    """
    # استفاده از format_html برای امنیت و خوانایی
    photo_html = ''
    if psychologist.profile_picture:
        photo_html = format_html(
            '<img src="{}" alt="{}" width="200" style="border-radius:50%; margin:15px 0;">',
            psychologist.profile_picture.url,
        )

    back_url = reverse('entity-action', kwargs={'subject': 'psychologist', 'action': 'list'})
    full_name = f"{psychologist.profile.first_name or ''} {psychologist.profile.last_name or ''}".strip()

    html = format_html(
        """
        <div class="psychologist-card">
            <h1>{}</h1>
            <p><strong>تخصص:</strong> {}</p>
            <p><strong>بیوگرافی:</strong> {}</p>
            {}
            <hr>
            <a href="{}" class="btn-back">بازگشت به لیست</a>
        </div>
        """,
        full_name,
        psychologist.specialty,
        psychologist.bio or 'در حال تکمیل...',
        photo_html,
        back_url
    )
    return mark_safe(html)



