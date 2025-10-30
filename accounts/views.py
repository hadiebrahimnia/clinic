from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from .forms import (
    CustomUserCreationForm, 
    CustomAuthenticationForm, 
    ProfileUpdateForm
)
from .models import Profile

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