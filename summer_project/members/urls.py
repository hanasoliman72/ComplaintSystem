from django.urls import path
from . import views
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
    path('submit/', views.SubmitComplaint, name='submit_complaint'),
    path('success/', views.Success, name='success'),
    path("general_manager_responses/", views.GeneralManagerResponses, name="general_manager_responses"),
    path("general_manager_responses/<int:response_id>/publish/", views.PublishResponse, name="publish_response"),
    path("track/", views.TrackComplaint, name="track_complaint"),
]