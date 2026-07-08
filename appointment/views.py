from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404 ,redirect
from django.core.exceptions import PermissionDenied
from .models import *
from .form import *



# ====================== Psychologist New Patients ======================
class PsychologistNewPatientsView(View):
    def get(self, request, subject, action, pk):
        psychologist = get_object_or_404(Psychologist, pk=pk)
        if psychologist.profile != request.user:
            raise PermissionDenied("شما اجازه ویرایش این پروفایل را ندارید.")

        new_patients_obj = PsychologistNewPatients.objects.filter(psychologist=psychologist).first()
        if not new_patients_obj:
            new_patients_obj = PsychologistNewPatients(psychologist=psychologist)

        form = PsychologistNewPatientsForm(instance=new_patients_obj)

        base_context = {
            'col_class': 'col-md-5 col-12 m-auto',
            'card_class': 'card shadow-lg',
            'card_header_class': 'card-header',
            'card_body_class': 'card-body p-5',
        }
        base_context.update({
            'title': 'مراجع جدید',
            'back_url': '/dashboard/',
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

        new_patients_obj = PsychologistNewPatients.objects.filter(psychologist=psychologist).first()
        if not new_patients_obj:
            new_patients_obj = PsychologistNewPatients(psychologist=psychologist)

        form = PsychologistNewPatientsForm(request.POST, instance=new_patients_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات مراجع جدید ثبت شد.")
            return redirect('dashboard')
        else:
            base_context = {
                'col_class': 'col-md-5 col-12 m-auto',
                'card_class': 'card shadow-lg',
                'card_header_class': 'card-header',
                'card_body_class': 'card-body p-5',
            }
            base_context.update({
                'title': 'مراجع جدید',
                'back_url': '/dashboard/',
                'back_text': 'بازگشت ',
                'back_class': 'btn btn-default-light',
                'back_icon': 'fa fa-arrow-left',
                'form': form,
                'form_action': reverse('entity-action-detail', kwargs={'subject': subject, 'action': action, 'pk': pk}),
                'submit_text': 'ذخیره',
                'submit_class': 'btn btn-success btn-lg btn-block ',
                'card_header_style': 'background-color: #1ab0fc;color: #fff;',
            })
            return render(request, 'form.html', base_context)

