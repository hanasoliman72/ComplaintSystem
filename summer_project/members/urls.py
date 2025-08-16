from django.urls import path
from . import views
app_name = "members"

urlpatterns = [
    path('register/', views.register_view, name="register"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('department/dashboard/', views.department_manager_dashboard, name='department_manager_dashboard'),
    path('general/dashboard/', views.general_manager_dashboard, name='general_manager_dashboard'),
    path('allComplaints/', views.allComplaints_view, name="allComplaints"),
    path('departmentComplaints/', views.departmentComplaints_view, name="departmentComplaints"),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('success/', views.complaint_success, name='complaint_success'),
]
