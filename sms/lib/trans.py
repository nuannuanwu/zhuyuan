# -*- coding: utf8 -*-
from memory.models import Sms
from sms.models import SmsSend,SmsSendAccount,SmsPort2mobile
import hashlib
from sms.lib.send import send
import datetime

class SmsTrans:
	"""
	处理业务短信转换到纯粹短信的类
	"""
	_msg = False
	
	def __init__(self):
		pass

	def run(self):
		pass

	def get_user_port(self, sender, receive_mobile):
		"""
		得到用户对应发送者的有效端口号。
		"""
		p = SmsPort2mobile.objects.filter(sender=sender, receive_mobile=receive_mobile)
		if p.count():
			p = p[0]
			try:
				ssa = SmsSendAccount.objects.get(uc=p.send_mobile,user_id=1)
				if SmsSendAccount.objects.is_valid_port(ssa.status):
					return p.send_mobile
				else:				
					p.delete()
			except:
				pass

		# 产生新的端口号，且在手机中是唯一的。
		p_set = SmsPort2mobile.objects.filter(receive_mobile=receive_mobile)
		exclude_list = [ p.send_mobile for p in p_set ]
		send_mobile = SmsSendAccount.objects.get_one_port(exclude_list=exclude_list)

		sms_port = SmsPort2mobile(sender=sender, send_mobile=send_mobile, receive_mobile=receive_mobile)
		sms_port.save()
		
		return send_mobile

	def memory_sms_to_sms(self,id):
		"""
		处理一条 memory_sms 到 sms表
		"""
		#得到数据				
		id = int(id)
		
		ksms = Sms.objects.get(pk=id)
		
		assert not ksms.is_send, 'exception, memory_sms has sended'
		
		sender = ksms.sender
		mobile = ksms.mobile
		content = ksms.content
		content_hash = hashlib.md5(content).hexdigest()
		
		send_mobile = self.get_user_port(sender=sender,receive_mobile=mobile)
		
		sms = SmsSend(tag_id=id, receive_mobile=mobile, send_mobile=send_mobile,content=content,content_hash=content_hash,send_date=ksms.send_time, \
					sender=sender)
		sms.save()
		
		self._msg = True
		ksms.is_send = True
		ksms.save()
		
		
class SmsSendTrans:
	"""
	发送短信到电信端口
	"""
	_msg = False
	
	def __init__(self):
		pass

	def run(self):
		pass
	
	def sms_send_to_gate(self,id):
		"""
		处理一条 sms_send
		"""
		sendclient = send()
		result = 0
		now = datetime.datetime.now()
		id = int(id)
		record = SmsSend.objects.get(pk=id)
		
		if not record.is_deal:
			sms_send_pk = record.id
			msgid=str(sms_send_pk)		  
			msgid = msgid[-6:]
			msgid = int(msgid)
	
			send_mobile = record.send_mobile
			pw = SmsSendAccount.objects.get(uc=send_mobile).pw
			msg = record.content.encode('GB18030')
			back='1'		
	
			callee=[record.receive_mobile]
			
			print send_mobile
			print "============="
			print msgid
			result = sendclient.send(send_mobile,pw,callee,back,msg,msgid)
			if result == '-7':
					# 直接重发
					result = sendclient.send(send_mobile,pw,callee,back,msg,msgid)

				
			if result == '-7':
				# 重发机制,
				record.is_deal = 0
				record.resend_times = record.resend_times + 1
			else:
				record.is_deal = 1

			record.deal_date = now
			record.receipt_status = result
			record.receipt_date = now
			record.save() 
			
			if result == '-7':
				try:
					p = SmsPort2mobile.objects.get(sender=record.sender, receive_mobile=record.receive_mobile)
					p.delete()
				except:
					pass
		else:
			self._msg = "该号码已发送过短信！"
		print self._msg
		return result

		
		 





