# accounts/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('ogrenci/kayit/', views.student_register, name='student_register'),
    path('ogrenci/giris/', views.student_login, name='student_login'),
    path('akademisyen/giris/', views.academic_login, name='academic_login'),
    path('ogrenci/panel/', views.student_panel, name='student_panel'),
    path('akademisyen/panel/', views.academic_panel, name='academic_panel'),
    path('akademisyen/ders/ekle/', views.course_create, name='course_create'),
    path('akademisyen/ders/<int:course_id>/', views.course_detail, name='course_detail'),
    path('akademisyen/ders/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('akademisyen/qr/olustur/', views.qr_session_create, name='qr_session_create'),
    path('akademisyen/qr/goruntule/<int:session_id>/', views.qr_session_display, name='qr_session_display'),
    path('akademisyen/qr/sonlandir/<int:session_id>/', views.qr_session_end, name='qr_session_end'),
    path('qr_attendance/<int:session_id>/', views.qr_attendance, name='qr_attendance'),
    path('akademisyen/yoklama/kayitlari/', views.attendance_record_list, name='attendance_record_list'),
    path('sifre-degistir/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('sifre-degistirildi/', auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'), name='password_change_done'),
]
