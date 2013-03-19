from django.contrib import admin
from django.db import transaction
# from django.utils.translation import ugettext as _
from memory.models import School,Group,Teacher,Student,EventSetting
from manage.forms import SchoolEventSettingsForm

from oauth2app.models import Client, AccessToken, Code

from django.template.response import TemplateResponse
from django.utils.html import escape
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.admin.util import unquote
from memory.widgets import AdminImageWidget
from django.db import models
from django.forms.formsets import all_valid
from django.contrib.admin import helpers
from django.utils.encoding import force_unicode

csrf_protect_m = method_decorator(csrf_protect)

from memory.admin import BackendRoleAdmin


class EventSettingInline(admin.TabularInline):
    """ Inline message recipients """
    model = EventSetting
    classes = ('grp-collapse grp-closed',)


class SchoolAdmin(BackendRoleAdmin):
    inlines = [EventSettingInline,]
    list_display = ('name', 'city', 'area','creator')
    list_filter = ('city', 'area','creator')
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('admins',)
    fieldsets = (
        (None, {'fields': ('creator','is_active','admins','name',('city', 'area'),'description')}),
        (_('Other info'), {'classes': ('grp-collapse grp-closed',),'fields': ('sys','type','is_delete',)}),
    )

class GroupAdmin(BackendRoleAdmin):
    list_display = ('name', 'school','creator')
    list_filter = ('school','creator')
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('teachers',)
    #search_fields = ('first_name', 'last_name')
    #date_hierarchy = 'creator'
    #fields = ('is_active','admins','name',('city', 'area'),'description')
    fieldsets = (
        (None, {'fields': ('is_active','school','name','teachers','logo','announcement','description')}),
        (_('Other info'), {'classes': ('grp-collapse grp-closed',),'fields': ('creator','is_delete',)}),
    )

    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget},
    }

class StudentAdmin(BackendRoleAdmin):
    list_display = ('name', 'group', 'school', 'gender','sn','user')
    list_filter = ('school','group','gender','is_active')
    search_fields = ('name','user__username','group__name','school__name')
    ordering = ('name',)
    raw_id_fields = ('user',)
    change_form_template='admin/includes/user_change_form.html' 
    #search_fields = ('first_name', 'last_name')
    #date_hierarchy = 'creator'
    #fields = ('is_active','admins','name',('city', 'area'),'description')
    fieldsets = (
        (None, {'fields': ('is_active','school','group','user','name','sn',('gender', 'birth_date'),'description')}),
        (_('Other info'), {'classes': ('grp-collapse grp-closed',),'fields': ('creator','is_delete',)}),
    )

class TeacherAdmin(BackendRoleAdmin):
    list_display = ('name','user','school','appellation','description')
    search_fields = ('name','user__username','school__name','appellation','description')
    change_form_template='admin/includes/user_change_form.html' 
    ordering = ('name',)
    raw_id_fields = ('user','school')
   
    
admin.site.register(School, SchoolAdmin)
#FIXME: raise AlreadyRegistered

admin.site.register(Group,GroupAdmin)
admin.site.register(Teacher,TeacherAdmin)
admin.site.register(Student,StudentAdmin)

from guardian.admin import GuardedModelAdmin
