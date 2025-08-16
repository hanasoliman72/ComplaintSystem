from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import User, Department, Complaint, Response, ChatbotSession

class CustomUserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide GPA field for DepartmentManager
        if self.instance and self.instance.Role == "DepartmentManager":
            self.fields.pop('GPA', None)

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('Role')
        department_id = cleaned_data.get('DepartmentId')
        # Require DepartmentId for DepartmentManager
        if role == "DepartmentManager" and not department_id:
            self.add_error('DepartmentId', "Department is required for Department Manager.")
        return cleaned_data

class CustomUserAdmin(UserAdmin):
    model = User
    form = CustomUserAdminForm
    list_display = ['username', 'email', 'Name', 'Role', 'is_staff']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('Name', 'email', 'GPA', 'Role', 'DepartmentId')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'Name', 'Role', 'DepartmentId', 'password1', 'password2'),
        }),
    )
    search_fields = ['username', 'email', 'Name']
    ordering = ['username']

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.Role == "DepartmentManager":
            # Remove GPA from fieldsets for DepartmentManager
            fieldsets = (
                (None, {'fields': ('username', 'password')}),
                ('Personal Info', {'fields': ('Name', 'email', 'Role', 'DepartmentId')}),
                ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
                ('Important dates', {'fields': ('last_login', 'date_joined')}),
            )
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.Role == "DepartmentManager":
            # Remove GPA from add/edit form for existing DepartmentManager
            form.base_fields.pop('GPA', None)
        return form

admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Complaint)
admin.site.register(Response)
admin.site.register(ChatbotSession)