from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('gm/dashboard/', views.gm_dashboard, name='gm_dashboard'),
    path('dm/dashboard/', views.dm_dashboard, name='dm_dashboard'),
]