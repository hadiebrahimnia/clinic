from django.contrib import admin
from django.urls import path, include
from core.views import *
from management.views import *
from accounts.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ckeditor
    path('django-ckeditor-5/', include('django_ckeditor_5.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    # ajax
    path('ajax/provinces/', get_provinces, name='get_provinces'),
    path('ajax/cities/', get_cities, name='get_cities'),
    path('ajax/specializations/', get_specializations, name='get_specializations'),
    # Mian
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('form/', FormView.as_view(), name='form'),
    # Accounts
    path('accounts/<str:action>/', AccountView.as_view(), name='accounts'),
    # Dashboard
    path('dashboard/<str:subject>/', DynamicDashboardView.as_view(), name='dashboard'),
    # Model
    path('<str:subject>/<str:action>/', DynamicEntityView.as_view(), name='entity-action'),
    path('<str:subject>/<str:action>/<int:pk>/', DynamicEntityView.as_view(), name='entity-action-detail'),
    # Management
    path('management/<str:subject>/<str:action>/', ManagementView.as_view(), name='management-action'),
    path('management/<str:subject>/<str:action>/<int:pk>/', ManagementView.as_view(), name='management-action-detail'),
    # Other
    path('boolean/<str:app_label>/<str:model_name>/<str:field>/<int:pk>/',DynamicBooleanView.as_view(),name='dynamic_boolean_toggle'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
