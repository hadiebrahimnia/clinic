from django import forms
from core.widget import *
from .models import *
from ckeditor_uploader.widgets import CKEditorUploadingWidget


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ['title', 'name_fa', 'name_en', 'cost', 'question']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'name_fa': forms.TextInput(attrs={'class': 'form-control text-center'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control text-center'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control text-center', 'required': True}),
            'question': forms.NumberInput(attrs={'class': 'form-control text-center', 'required': True}),
        }


class AttributeForm(forms.ModelForm):
    class Meta:
        model = Attribute
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['questionnaire', 'attribute', 'text', 'question_type', 'order', 'required']
        widgets = {
            'questionnaire': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'attribute': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'text': forms.Textarea(attrs={'class': 'form-control text-center', 'required': True, 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'order': forms.NumberInput(attrs={'class': 'form-control text-center', 'required': True}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['question', 'text', 'value']
        widgets = {
            'question': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'text': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'value': forms.NumberInput(attrs={'class': 'form-control text-center', 'required': True}),
        }


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['questionnaire', 'respondent', 'completed_at', 'is_completed']
        widgets = {
            'questionnaire': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'respondent': forms.Select(attrs={'class': 'form-control text-center'}),
            'completed_at': forms.DateTimeInput(attrs={'class': 'form-control text-center', 'type': 'datetime-local'}),
            'is_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['response', 'question', 'choice', 'text_answer', 'scale_value', 'RT']
        widgets = {
            'response': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'question': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'choice': forms.Select(attrs={'class': 'form-control text-center'}),
            'text_answer': forms.Textarea(attrs={'class': 'form-control text-center', 'rows': 3}),
            'scale_value': forms.NumberInput(attrs={'class': 'form-control text-center'}),
            'RT': forms.NumberInput(attrs={'class': 'form-control text-center'}),
        }


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = [
            'user', 
            'questionnaire', 
            'response', 
            'attribute', 
            'num_questions', 
            'raw_score', 
            'average_score', 
            'sum_rt', 
            'average_rt'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'questionnaire': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'response': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'attribute': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'num_questions': forms.NumberInput(attrs={'class': 'form-control text-center', 'required': True}),
            'raw_score': forms.NumberInput(attrs={'class': 'form-control text-center', 'step': '0.01'}),
            'average_score': forms.NumberInput(attrs={'class': 'form-control text-center', 'step': '0.01'}),
            'sum_rt': forms.NumberInput(attrs={'class': 'form-control text-center'}),
            'average_rt': forms.NumberInput(attrs={'class': 'form-control text-center', 'step': '0.01'}),
        }


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'content_type', 'object_id']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'content_type': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
            'object_id': forms.NumberInput(attrs={'class': 'form-control text-center', 'required': True}),
        }