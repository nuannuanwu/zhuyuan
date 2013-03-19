# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from memory.models import Cookbook,CookbookRead,TileCategory,Sms,RelevantStaff
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from aq.views.default import get_unread_mentor_count as unread_mentor
from waiter.views.default import get_unread_waiter_count as unread_waiter

from memory import helpers
from django.http import Http404
from django.http import HttpResponse

from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import connection
import re
import urllib

import datetime,time
from decimal import Decimal as D
try:
    import simplejson as json
except ImportError:
    import json

try:
    from sae.taskqueue import Task, TaskQueue
except:
    pass
    
import sys
reload(sys)
sys.setdefaultencoding('utf8') 

SITE_INFO = Site.objects.get_current()
 
@staff_member_required
def tile_change_form(request): 
    is_tips = request.POST.get('is_tips','0')
    
    category_list = []
    parent_category = TileCategory.objects.filter(parent_id=0,is_tips=is_tips).all()
    for p in parent_category:
        sub_category = TileCategory.objects.filter(parent_id=p.id,is_tips=is_tips).all()
        category_list.append({'id':p.id,'name':p.name,'parent_id':p.parent_id})
        for s in sub_category:
            category_list.append({'id':s.id,'name':s.name,'parent_id':s.parent_id})
     
    return HttpResponse(json.dumps(category_list))

@staff_member_required
def cookbook_info(request,cid,template_name="admin/includes/cookbook_info.html"):
    """食谱访数据问统计"""

    cookbook = Cookbook.objects.get(id=cid)
    users = [s.user for s in cookbook.get_student()]
    user_num = len(users)
    cookbookreads = []
    read_num,send_num = 0,0
    
    cookbookreads = CookbookRead.objects.filter(cookbook=cookbook,date=cookbook.date)
    if cookbookreads:
        read_num = cookbookreads.filter(is_read=True).count()
        send_num = cookbookreads.filter(is_send=True).count()
    
    ctx = {"cookbook":cookbook,"user_num":user_num,"cookbookreads":cookbookreads,"read_num":read_num,"send_num":send_num}
    return render(request, template_name, ctx)

@staff_member_required
def not_logged_in_sms(request,template_name="admin/includes/not_logged_in_sms.html"):
    """已发送的未登录短信列表"""

    msgs = Sms.objects.filter(type_id=98,is_send=True)
    ctx = {"msgs":msgs}
    return render(request, template_name, ctx)


#发送未读导师及客服提醒
def send_staff_unread(request): 
    unread_mentors = unread_mentor()
    unread_waiters = unread_waiter()
    if not unread_mentors and not unread_mentors:
        return HttpResponse('')
    
    staffs = RelevantStaff.objects.exclude(send_mentor=False,send_waiter=False)
    
    for s in staffs:
        #发送短信,已有队列
        if s.send_mentor and unread_mentors and s.mobile:
            msg = "<" + SITE_INFO.name + ">导师留言后台有" + str(unread_mentors) + "条新客户留言. 请及时登录回复. 登录地址: " + SITE_INFO.domain + reverse('aq')
            helpers.send_staff_mobile(s.mobile,msg)
        if s.send_waiter and unread_waiters and s.mobile:
            msg = "<" + SITE_INFO.name + ">客服后台有" + str(unread_waiters) + "条新客服留言. 请及时登录回复. 登录地址: " + SITE_INFO.domain + reverse('waiter')
            helpers.send_staff_mobile(s.mobile,msg)
    
    for s in staffs:
        #发送邮件队列
        data = {"staff_id":s.id,"unread_mentors":unread_mentors,"unread_waiters":unread_waiters}
        payload = urllib.urlencode(data)
        #执行转换
        try:
            queue = TaskQueue('notice2staff')
            queue.add(Task("/backend/taskqueue/notice2staff",payload))
        except:
            st = helpers.StaffTrans()
            st.memory_notice_to_staff(s.id,unread_mentors,unread_waiters)
  
    return HttpResponse('')