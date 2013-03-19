# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models

# from django.utils.translation import ugettext as _
from memory.models import Tile, TileType, TileTag, EventSetting, EventType, Device,ApplePushNotification,\
Mentor,Waiter,Cookbook, CookbookSet,Sms,TileCategory,Activity,SmsType,RelevantStaff,Schedule
from oauth2app.models import Client, AccessToken, Code
from memory.forms import (TileCreationForm)

from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.admin import widgets, helpers
from django.contrib.admin.util import unquote

from memory.widgets import AdminImageWidget
from memory import settings
from sms.models import SmsNotifyStatus,SmsReceipt,SmsReceive,SmsSend
from django.contrib.comments import Comment
from django.core.urlresolvers import reverse

class BackendRoleAdmin(admin.ModelAdmin):
    yunying_fieldsets = ()

    def is_limit_yunying(self,request):
        try:
            perm = u'运营部'
            is_yunying =  request.user.groups.filter(name = perm).exists()
            if (is_yunying and not request.user.is_superuser):
                return True
            else:
                return False
        except Exception:
            pass
        return False

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}

        is_limit_yunying = self.is_limit_yunying(request)
        if is_limit_yunying:
	        # if opeatior is pm
            try:
    	        if obj is None:
                    self.fieldsets = self.yunying_fieldsets or self.fieldsets
                    defaults.update({
                        'form': self.add_form,
                        'fields': admin.util.flatten_fieldsets(self.fieldsets),
                    })
    	        defaults.update(kwargs)
            except Exception:
                pass
        form = super(BackendRoleAdmin, self).get_form(request, obj, **defaults)
          
        try:
            if hasattr(self.model, 'creator'):                    
                form.base_fields['creator'].initial = request.user
                form.base_fields['creator'].widget.attrs['readonly'] = True
                form.base_fields['creator'].widget.attrs['hidden'] = True
        except Exception:
            pass

        if not request.user.is_superuser:
            try:
                form.base_fields['is_delete'].widget.attrs['hidden'] = True
            except Exception, e:
                pass
            try:
                form.base_fields['creator'].widget.attrs['hidden'] = True
            except Exception, e:
                pass

        return form

class ApplePushNotificationInline(admin.StackedInline):
    model = ApplePushNotification
    readonly_fields = ('is_send',) 
    exclude = ('creator',)   

class ApplePushNotificationAdmin(BackendRoleAdmin):    
    readonly_fields = ('is_send',)
    list_display = ('alert','tile','creator','is_send','send_time')
    date_hierarchy = 'send_time'
    list_filter = ('is_send','creator','tile','send_time')  
    raw_id_fields = ('tile',)
    search_fields = ('alert',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            if obj.is_send:
                return ('creator','alert','badge','sound','send_time','is_send','tile') 
            else:
                return ('creator','is_send')
        else:
            pass    
        return super(ApplePushNotificationAdmin, self).get_readonly_fields(request,obj)  


class TileAdmin(BackendRoleAdmin):
    
    class Media:
        js = (
              settings.STATIC_URL + 'media/js/tinymce/jscripts/tiny_mce/tiny_mce.js',
              settings.STATIC_URL + 'media/js/textareas.js',
         )
    #add_form_template = 'admin/memory/tile/add_form.html'
    search_fields = ('title','description')
    date_hierarchy = 'start_time'
    filter_horizontal = ('tags',)
    add_form = TileCreationForm
    list_display = ('title','type','category','is_tips','is_public','user','group','creator','n_likers','n_comments', 'picture', 'decade_create_time','start_times','end_times')
    list_filter = ('is_tips', 'is_public', 'tags', 'type','category','creator','user')
    raw_id_fields = ('creator','user','group')
    prepopulated_fields = {"description": ("title",)}
    readonly_fields = ('n_comments','n_likers')
    inlines = [
        ApplePushNotificationInline,
    ]
    ordering = ['-start_time']
    change_form_template='admin/includes/tile_change_form.html' 
    fieldsets = (
        (None, {'fields': (('is_tips','is_public'),'title', 'url', 'img','type','category','description', 'content', 'tags')}),
        (u'预期发布',{'fields':(('start_time','end_time'),)}),
        (u'瓦片范围控制（可选为用户、班级、所有用户（全空））', {'fields': ('group', 'user')}),
        (_('Other info'), {'fields': ('n_comments', 'n_likers','creator')}),
        #(_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    yunying_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (('is_tips','is_public'),'title','url', 'img', 'type', 'category', 'description', 'content',  'tags'),
            }
        ),
        (u'预期发布',{'fields':(('start_time','end_time'),)}),
        ('Advanced options', {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('creator','video')
        }),
    )

    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget},
    }

    def start_times(self, obj):
        return obj.start_time.strftime('%Y-%m-%d %H:%M:%S')
    start_times.short_description = '起始时间'
    start_times.admin_order_field = 'start_time'

    def end_times(self, obj):
        return obj.end_time.strftime('%Y-%m-%d %H:%M:%S')
    end_times.short_description = '结束时间'
    end_times.admin_order_field = 'end_time'

    # 让推送消息中，根据is_send的值，判断，发送后，所有字段都变为只读。如果没有发送，其它字段可以修改
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, unquote(object_id))   
        ApplePushNotificationInline.readonly_fields = ('is_send',)  
        try:
            if obj.applepushnotification.is_send:                
                ApplePushNotificationInline.readonly_fields = ('creator','alert','badge','sound','send_time','is_send')               
        
        except Exception, e:
            pass
        return super(TileAdmin, self).change_view(request, object_id, form_url='', extra_context=None)

    def add_view(self, request, form_url='', extra_context=None):
        ApplePushNotificationInline.readonly_fields = ('is_send',)

        return super(TileAdmin, self).add_view(request, form_url='', extra_context=None)

    def queryset(self, request):
        qs = super(TileAdmin, self).queryset(request)
        perm = u'运营部'
        is_limit_yunying = self.is_limit_yunying(request)
        if is_limit_yunying:
            qs = qs.filter(is_tips=True)
        return qs

    def get_form(self, request, obj=None, **kwargs):        
        form = super(TileAdmin, self).get_form(request, obj, **kwargs)        
        is_tips = None
        is_limit_yunying = self.is_limit_yunying(request)        
        if is_limit_yunying:
            is_tips = 1
            form.base_fields['type'].queryset = TileType.objects.filter(id__in=[1,2]).all()           

        form.base_fields['category'].choices = templates_as_choices(request,is_tips)
        return form

    # 让notification 的creator值保持为当前用户。解决了非要保存notification的问题。
    def save_formset(self, request, form, formset, change):
        if formset.model != ApplePushNotification:
            return super(TileAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.creator = request.user
            instance.save()
        formset.save_m2m()

def templates_as_choices(request,is_tips=None):
    templates = []
    parent_category = TileCategory.objects.get_category(layer='parent',tips=is_tips)   
    category_list = []
    for p in parent_category:        
        sub_category = TileCategory.objects.get_one_parent_sub(p.pk)
        sub_list = []
        for s in sub_category:
            sub_list.append([s.id, s.name])
        templates.append([p.name, sub_list])   
    return templates



class TileCategoryAdmin(BackendRoleAdmin):
    search_fields = ('name',)
    list_display = ('name','description','img','parent','is_tips','picture')
    list_filter = ('parent','is_tips')
    fieldsets = (
        (None, {'fields': ('is_tips','name','parent')}),
        (_('Other info'), {'classes': ('grp-collapse grp-closed',),'fields': ('img', 'description','is_delete')}),
    )
    
    
    def get_form(self, request, obj=None, **kwargs):
        try:   
            if obj.parent_id:
                self.fieldsets = (
                    (None, {'fields': ('is_tips','name','parent')}),
                    (_('Other info'), {'classes': ('grp-collapse grp-closed',),'fields': ('description','is_delete')}),
                )
            else:
                self.fieldsets = (
                    (None, {'fields': ('is_tips','name','parent')}),
                    (_('Other info'), {'classes': ('grp-collapse grp-closed',),'fields': ('img','description','is_delete')}),
                )
        except:
            pass
        form = super(TileCategoryAdmin, self).get_form(request, obj, **kwargs)
        
        form.base_fields['parent'].queryset = TileCategory.objects.filter(parent_id=0).all()
        return form
    
class EventTypeInline(admin.TabularInline):
    """ Inline message recipients """
    model = EventType

class EventSettingInline(admin.TabularInline):
    """ Inline message recipients """
    model = EventSetting

class EventTypeAdmin(BackendRoleAdmin):
    #add_form_template = 'admin/memory/tile/add_form.html'
    search_fields = ('name',)
    list_display = ('name','group')
    list_filter = ('group',)


class EventSettingAdmin(BackendRoleAdmin):
    #add_form_template = 'admin/memory/tile/add_form.html'
    search_fields = ('content',)
    list_display = ('content','type','school')
    list_filter = ('type','school')
    
    
class CommentAdmin(BackendRoleAdmin):
    search_fields = ('comment','user_name')
    list_display = ('sender_name','content','ctype','content_obj','ip_address','submit_date','is_public','is_removed')
    list_filter = ('user','content_type','submit_date','is_removed','ip_address')
    raw_id_fields = ('user',)
    
    def sender_name(self,obj):
        return obj.user_name
    sender_name.short_description = '用户姓名'
    
    def content(self,obj):
        return obj.comment
    content.short_description = '评论内容'
    
    def ctype(self,obj):
        return obj.content_type
    ctype.short_description = '对象类型'
    ctype.admin_order_field = 'content_type'
    
    def content_obj(self,obj):
        return obj.content_object
    content_obj.short_description = '评论对象'


class SmsAdmin(BackendRoleAdmin):
    list_display = ('sender','receiver','content','mobile','is_send','is_gateway','is_receive','send_times','type')
    date_hierarchy = 'ctime'
    list_filter = ('mobile','sender','receiver','type','send_time')
    search_fields = ('content','mobile','sender__username','receiver__username')
    change_list_template='admin/includes/sms_change_list.html' 

    def send_times(self, obj):
        return obj.send_time.strftime('%Y年%m月%d日 %H:%M')
    send_times.short_description = '发送时间'
    send_times.admin_order_field = 'send_time'
    
    def is_gateway(self, obj): 
        """
        在SmsNotifyStatus  中找到 sms_send id 表示已到达网关
        """
        # 从 sms_send 得到
        ss = SmsSend.objects.filter(tag_id=obj.pk,source=0).order_by('-tag_id')
        if ss.exists():
            return SmsNotifyStatus.objects.filter(sessionID=ss[0].pk).exists()        
        return False

    is_gateway.short_description = '是否到网关'
    is_gateway.boolean = True

    def is_receive(self, obj):
        ss = SmsSend.objects.filter(tag_id=obj.pk,source=0).order_by('-tag_id')
        if ss.exists():
            return SmsReceipt.objects.filter(msgid=ss[0].pk).exists()        
        return False        
    is_receive.short_description = '是否收到'
    is_receive.boolean = True
    

class MentorAdmin(BackendRoleAdmin):
    raw_id_fields = ('creator','user',)
    search_fields = ['name']
    change_form_template='admin/includes/mentor_change_form.html' 
 
    
class WaiterAdmin(BackendRoleAdmin):
    raw_id_fields = ('creator','user',)
    search_fields = ['name']
    change_form_template='admin/includes/waiter_change_form.html' 


class CookbookAdmin(BackendRoleAdmin):
    list_display = ('__unicode__','cookbookdate','school','group','is_send','detail')
    readonly_fields = (['is_send'])
    raw_id_fields = ('school','group')
    list_filter = ('date','school','group','is_send')
    search_fields = ['breakfast', 'dinner', 'lunch']
    
    def cookbookdate(self, obj):
        return obj.date.strftime('%Y-%m-%d')
    cookbookdate.short_description = '日期'
    cookbookdate.admin_order_field = 'date'
    
    def detail(self, obj):
        url = reverse('admin_cookbook_info',kwargs={'cid':obj.id})
        return '<a href="' + url + '">查看</a>'
    detail.short_description = '操作'
    detail.allow_tags = True


class ActivityAdmin(BackendRoleAdmin):
    readonly_fields = (['creator'])
    change_form_template='admin/includes/user_change_form.html' 
    fieldsets = (
        (None, {'fields': ('creator','user','group','start_time','description')}),
    )
    list_display = ('start_times','user','group')
    list_filter = ('start_time','user','group')
    search_fields = ['start_time']
    raw_id_fields = ('user','group')
    
    def start_times(self, obj):
        return obj.start_time.strftime('%Y-%m-%d')
    start_times.short_description = '日期'
    start_times.admin_order_field = 'start_time'
    

class RelevantStaffAdmin(BackendRoleAdmin):
    
    list_display = ('name','mobile','email','send_mentor','send_waiter')
    list_filter = ('send_mentor','send_waiter')
    search_fields = ['name','mobile','email']
    
    
      

admin.site.unregister(Comment)
admin.site.register(Comment,CommentAdmin)
admin.site.register(Tile)
admin.site.register(TileCategory,TileCategoryAdmin)
admin.site.register(TileType,BackendRoleAdmin)

admin.site.register(Client)
admin.site.register(AccessToken)
admin.site.register(Code)

admin.site.register(TileTag,BackendRoleAdmin)

admin.site.register(EventSetting,EventSettingAdmin)
admin.site.register(EventType,EventTypeAdmin)

admin.site.register(Device)

admin.site.register(ApplePushNotification,ApplePushNotificationAdmin)
admin.site.register(RelevantStaff,RelevantStaffAdmin)


admin.site.register(Mentor,MentorAdmin)
admin.site.register(Waiter,WaiterAdmin)

admin.site.register(Cookbook,CookbookAdmin)
admin.site.register(CookbookSet)

admin.site.register(Activity,ActivityAdmin)

admin.site.register(Sms,SmsAdmin)
admin.site.register(SmsType)
admin.site.register(Schedule)




