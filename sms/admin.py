# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models

# from django.utils.translation import ugettext as _

from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.admin import widgets, helpers
from django.contrib.admin.util import unquote

from sms.models import SmsNotifyStatus,SmsReceipt,SmsReceive,SmsPort2mobile
from memory.admin import BackendRoleAdmin


class SmsPort2mobileAdmin(BackendRoleAdmin):
    list_display = ('sender','send_mobile','receive_mobile','send_status')    
    list_filter = ('sender','send_mobile','receive_mobile')
    search_fields = ['sender','send_mobile','receive_mobile']

    def send_status(self, obj):        
        #得到某个唯一匹配的最后发送状态
        send_mobile = obj.send_mobile
        mobile = obj.receive_mobile
        sr = SmsReceipt.objects.filter(ucNum=send_mobile,cee=mobile).order_by('-pk')
        if sr.count():
            res = sr[0].res
        else:
            res = ''
        return res
    send_status.short_description = '最后发送状态'  

admin.site.register(SmsPort2mobile,SmsPort2mobileAdmin)






