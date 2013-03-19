# -*- coding: utf-8 -*-
from django.http import HttpResponse
from APNSWrapper import *
import binascii
from django.views.decorators.csrf import csrf_exempt
from sms.lib.trans import SmsTrans, SmsSendTrans
from sms.lib import send
from sms.models import SmsSend, SmsSendAccount, SmsPort2mobile
from backend.helpers import StaffTrans
from backend import helpers
import sys 
reload(sys) 
sys.setdefaultencoding('utf8')

@csrf_exempt
def apns(request): 
    try:
        token = request.POST.get('token')
        alert = request.POST.get('alert')
        badge = request.POST.get('badge',0)
        sound = request.POST.get('sound','default')

        alert = alert.encode('utf-8')
        wrapper = APNSNotificationWrapper(helpers.get_pem_file())
        #deviceToken = binascii.unhexlify(token)
        message = APNSNotification()
        deviceToken = binascii.unhexlify(token)
        message.token(deviceToken)
        message.alert(alert)
        message.badge(int(badge))
        message.sound(sound)
        wrapper.append(message)
        rs = wrapper.notify()
    except Exception, e:
        print e

    return HttpResponse(alert)


@csrf_exempt
def sms2send(request):
    resust = False
    try:
        sms_id = request.REQUEST.get('sms_id')
        st = SmsTrans()
        st.memory_sms_to_sms(sms_id)
        result = st._msg

    except Exception, e:
        print e
        return HttpResponse(e)
    
    return HttpResponse(result)


@csrf_exempt
def notice2staff(request):
    resust = False
    try:
        staff_id = request.REQUEST.get('staff_id')
        unread_mentors = request.REQUEST.get('unread_mentors')
        unread_waiters = request.REQUEST.get('unread_waiters')
        st = StaffTrans()
        st.memory_notice_to_staff(staff_id,unread_mentors,unread_waiters)
        result = st._msg

    except Exception, e:
        print e
        return HttpResponse(e)
    
    return HttpResponse(result)

@csrf_exempt
def sms2gate(request):
    
    status = False
    now = datetime.datetime.now()
    result = 0
    try:
        id = request.REQUEST.get('id')
        st = SmsSendTrans()
        result = st.sms_send_to_gate(id)
        status = st._msg
    except Exception, e:
        print e
        return HttpResponse(e)
    
    return HttpResponse(status)

