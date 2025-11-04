from django.contrib import admin
from django.urls import path
from core.views import *
from administrator.views import *
from accounts.views import *
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/<str:action>/', AccountView.as_view(), name='accounts'),
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('administrator/', AdministratorView.as_view(), name='administrator'),
    path('form/', FormView.as_view(), name='form'),
    path('<str:subject>/<str:action>/', DynamicEntityView.as_view(), name='entity-action'),
    path('<str:subject>/<str:action>/<int:pk>/', DynamicEntityView.as_view(), name='entity-detail'),
]