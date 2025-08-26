from . import views
from django.urls import path

app_name = "members"

urlpatterns = [
    path('register/', views.RegisterView, name="register"),
    path('login/', views.LoginView, name='login'),
    path('logout/', views.LogoutView, name='logout'),

    path('student/profile/', views.StudentProfile, name='student_profile'),
    path('department/dashboard/', views.DepartmentManagerDashboard, name='department_manager_dashboard'),
    path('general/dashboard/', views.GeneralManagerDashboard, name='general_manager_dashboard'),
    path('allComplaints/', views.AllComplaints, name="all_complaints"),
    path('departmentComplaints/', views.DepartmentComplaints, name="department_complaints"),
    path('submit/', views.SubmitComplaint, name='submit_complaint'),
    path("general_manager_responses/", views.GeneralManagerResponses, name="general_manager_responses"),
    path("general_manager_responses/<int:response_id>/publish/", views.PublishResponse, name="publish_response"),
    path("track/", views.TrackComplaint, name="track_complaint"),

    path("password-reset/", views.password_reset_request, name="password_reset"),
    path("password-reset-confirm/<str:uidb64>/<str:token>/", views.password_reset_confirm, name="password_reset_confirm"),
    # path(
    #     'password_reset/',
    #     auth_views.PasswordResetView.as_view(
    #         template_name='password_reset.html',
    #         email_template_name='password_reset_email.html',
    #         success_url=reverse_lazy('members:password_reset_done')
    #     ),
    #     name='password_reset'
    # ),
    # path(
    #     'password_reset_done/',
    #     auth_views.PasswordResetDoneView.as_view(
    #         template_name='password_reset_done.html'
    #     ),
    #     name='password_reset_done'
    # ),
    # path(
    #     'reset/<uidb64>/<token>/',
    #     auth_views.PasswordResetConfirmView.as_view(
    #         template_name='password_reset_confirm.html',
    #         success_url=reverse_lazy('members:password_reset_complete')
    #     ),
    #     name='password_reset_confirm'
    # ),
    # path(
    #     'reset/done/',
    #     auth_views.PasswordResetCompleteView.as_view(
    #         template_name='password_reset_complete.html'
    #     ),
    #     name='password_reset_complete'
    # ),
]
