from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.record_list, name='record_list'),
    path('record/<int:record_id>/', views.record_detail, name='record_detail'),

    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('create/', views.create_record, name='create_record'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
