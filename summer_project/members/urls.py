from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
app_name = "members"

urlpatterns = [
    path('register/', views.RegisterView, name="register"),
    path('login/', views.LoginView, name='login'),
    path('logout/', views.LogoutView, name='logout'),

    path('student/dashboard/', views.StudentDashboard, name='student_dashboard'),
    path('department/dashboard/', views.DepartmentManagerDashboard, name='department_manager_dashboard'),
    path('general/dashboard/', views.GeneralManagerDashboard, name='general_manager_dashboard'),
    path('allComplaints/', views.AllComplaints, name="all_complaints"),
    path('departmentComplaints/', views.DepartmentComplaints, name="department_complaints"),
    path('submit/', views.submit_complaint, name='submit_complaint'),
    path('success/', views.Success, name='success'),
    path("general_manager_responses/", views.GeneralManagerResponses, name="general_manager_responses"),
    path("general_manager_responses/<int:response_id>/publish/", views.PublishResponse, name="publish_response"),
    path("track/", views.TrackComplaint, name="track_complaint"),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),
]