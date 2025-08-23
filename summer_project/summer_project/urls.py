from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('admin/', admin.site.urls),
    path('members/', include('members.urls', namespace='members')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
