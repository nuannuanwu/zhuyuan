# -*- coding: utf-8 -*-

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from memory.profiles.models import Profile
from easy_thumbnails.fields import ThumbnailerImageField
from memory.mixins import *
from memory.utils import upload_to_mugshot
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.comments import Comment
from manage.managers import SchoolUserManager, TileManager, SmsManager, CookbookManager, CookbookSetManager, VerifySmsManager, \
TileCategoryManager,CharManager,CookbookreadManager

from memory.validators import validate_not_spaces,user_is_exist
from memory import helpers

from djangoratings.fields import RatingField
#喜欢按钮
from likeable.models import Likeable
import datetime,time
from decimal import Decimal as D
from django.contrib.auth.forms import SetPasswordForm
from userena import signals as userena_signals
from django.contrib.sites.models import Site
from django.contrib.comments import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

##########
# Models #
##########

SITE_INFO = Site.objects.get_current()

class BaseModel(models.Model):
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Teacher(BaseModel, ActiveMixin, SoftDeleteMixin):
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    user = models.OneToOneField(User,verbose_name = _('user'),validators=[user_is_exist])
    school = models.ForeignKey("School", null=True, blank=True,verbose_name = _('school'))

    name = models.CharField(_('Teacher name'), max_length=60,  validators=[validate_not_spaces])
    appellation = models.CharField(_('Appellation'), max_length=60, blank=True)
    description = models.TextField(_('Description'), max_length=765, blank=True)

    pinyin = models.CharField(_('pinyin'), max_length=100, blank=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pinyin = Char.objects.trans(self.name)

        profile = self.user.get_profile()
        profile.realname = self.name
        profile.save()

        super(Teacher, self).save(*args, **kwargs)
        
    def getAvatar(self):
        profile = self.user.get_profile()
        return profile.mugshot

    def getMobile(self):
        mobile = ''
        try:
            profile = self.user.get_profile()
            mobile = profile.mobile
        except ObjectDoesNotExist:
            pass
        return mobile

    def resetPasswordAndSendSms(self, pass_form=SetPasswordForm, sender=None):
        #
        try:
            user = self.user
        except ObjectDoesNotExist:
            return False

        new_password = User.objects.make_random_password(length=6,allowed_chars='0123456789')
        data = {'new_password1': new_password, 'new_password2': new_password}
        form = pass_form(user=user, data=data)

        if form.is_valid():
            form.save()
            mobile = self.getMobile()
            content = False
            if mobile:
                username = user.username                
                content = u"尊敬的用户，您的登录帐号是:" + username + u",密码是:" + new_password+u"【" + SITE_INFO.name + "】"
                content = u"尊敬的用户您好，欢迎使用【" + SITE_INFO.name + "】家园沟通应用，您的账号：" + username + u" 密码：" + new_password + u" 登入" + SITE_INFO.domain + "即刻体验！"
                userena_signals.password_complete.send(sender=None, user=user)
                # 记录到 sms表
                #sender = self.user
                receiver = self.user

                Sms.objects.create_send_account_sms(sender=sender, receiver=receiver, mobile=mobile, content=content)

        return content

    class Meta:
        verbose_name = _('teacher')
        verbose_name_plural = _('teachers')
        ordering = ['pinyin','name']

class Group(BaseModel, ActiveMixin, SoftDeleteMixin):

    SN_CHOICES = [[str(x).zfill(2) for i in range(0,2)] for x in range(1,21)]
    year = datetime.datetime.now().year
    YEAR_CHOICES = [[str(x) for i in range(0,2)] for x in range(year - 10,year + 10)]
    
    creator = models.ForeignKey(User,verbose_name = _('creator'))
    school = models.ForeignKey("School",verbose_name = _('school'))
    teachers = models.ManyToManyField(Teacher, related_name="groups", null=True,verbose_name = _('teacher'))

    name = models.CharField(_('Name'),max_length=120, validators=[validate_not_spaces])
    logo = ThumbnailerImageField(_('Logo'),
            blank=True,
            upload_to=upload_to_mugshot,
            )
    year = models.CharField(_('Year'),max_length=36, choices=YEAR_CHOICES,blank=True, null=True)
    sn = models.CharField(_('Sn'),max_length=36, choices=SN_CHOICES,blank=True, null=True)
    announcement = models.CharField(_('Announcement'),max_length=765, blank=True)
    description = models.TextField(_('Description'), max_length=765, blank=True)


    class Meta:
        verbose_name = _('school class')
        verbose_name_plural = _('school classes')
        ordering = ['name']
        
    def __unicode__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.logo:
            self.logo = 'group/African_Pets_003.png' 
        super(Group, self).save(*args, **kwargs)


class School(BaseModel, ActiveMixin, SoftDeleteMixin):
    AREA_CHOICES = (
        (u'罗湖区', u'罗湖区'),
        (u'南山区', u'南山区'),
        (u'福田区', u'福田区'),
        (u'龙岗区', u'龙岗区'),
        (u'盐田区', u'盐田区'),
        (u'宝安区', u'宝安区'),        
        )
    CITY_CHOICES = (
        (u'深圳市', u'深圳市'),
        )
    creator = models.ForeignKey(User,verbose_name = _('creator'))
    admins = models.ManyToManyField(User, related_name="manageSchools", null=True,verbose_name = _('school admins'))

    name = models.CharField(_('Name'),max_length=60, blank=True)

    area = models.CharField(_('Area'),max_length=60, blank=True,choices=AREA_CHOICES,)
    city = models.CharField(_('City'),max_length=60, blank=True,choices=CITY_CHOICES,)
    province = models.CharField(_('Province'),max_length=60, blank=True)
    sys = models.CharField(_('Sys'),max_length=9, null=True, blank=True)

    type = models.IntegerField(_('Type'),null=True, blank=True)
    description = models.TextField(_('Description'),max_length=765, blank=True)

    userObjects = SchoolUserManager()

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (
            ('can_manage_school', '管理学校权限'),
        )
        verbose_name = _('school')
        verbose_name_plural = _('schools')
        ordering = ['name']


class SmsType(BaseModel, SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120)
    description = models.TextField(_('Description'),max_length=765, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('sms type')
        verbose_name_plural = _('sms types')
        db_table = 'memory_sms_type'
        ordering = ('id',)
        
        
class Sms(BaseModel, ActiveMixin, SoftDeleteMixin):
    """
    type = 0   普通短信
    type = 2   消息转换
    type = 100 系统发送账号重置密码短信 
    type = 101 发送验证码短信
    """
    GROUP_TYPE = (
        (0, _('System')),
        (1, _('Notice')),
        )
    sender = models.ForeignKey(User, related_name="sender", null=True,verbose_name = _('sender'))
    receiver = models.ForeignKey(User, related_name="receiver",verbose_name = _('receiver'))
    mobile = models.CharField(_('Mobile'),max_length=20, blank=True)
    send_time = models.DateTimeField(auto_now_add=True)
    is_send = models.BooleanField(_('is send'),default=False)
    type = models.ForeignKey(SmsType,verbose_name = _('sms type'),null=True, blank=True)
    #type = models.IntegerField(null=True, blank=True,help_text="type =2时，短信从 消息转换过来 ")
    content = models.CharField(max_length=765, blank=True,verbose_name = _('content'))

    objects = SmsManager()

    def __unicode__(self):
        return self.content

    def getMobile(self):
        profile = self.user.get_profile()
        return profile.mobile

    class Meta:
        ordering = ['-ctime']
        verbose_name = _('sms')
        verbose_name_plural = _('sms')

        
        
class Student(BaseModel, ActiveMixin, SoftDeleteMixin):

    GENDER_CHOICES = (
        (1, _('Male')),
        (2, _('Female')),
        )

    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    user = models.OneToOneField(User,verbose_name = _('user'))
    school = models.ForeignKey(School,verbose_name = _('school'))
    group = models.ForeignKey(Group, null=True, blank=True, related_name="students",verbose_name = _('school class'))

    name = models.CharField(_('Name'),max_length=90, validators=[validate_not_spaces])
    gender = models.PositiveSmallIntegerField(_('Gender'),
                                              choices=GENDER_CHOICES,
                                              blank=True,
                                              null=True)

    birth_date = models.DateField(_('Birth date'), blank=True, null=True,\
        help_text=_("Date format: YYYY-MM-DD"))
    sn = models.CharField(max_length=36, blank=True)
    description = models.TextField(_('Description'), max_length=765, blank=True)

    pinyin = models.CharField(_('pinyin'), max_length=100, blank=True)

    class Meta:
        verbose_name = _('student')
        verbose_name_plural = _('students')
        ordering = ['pinyin', 'name']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):      
        self.pinyin = Char.objects.trans(self.name)

        profile = self.user.get_profile()
        profile.realname = self.name
        profile.save()

        super(Student, self).save(*args, **kwargs)

    @property
    def age(self):
        return helpers.calculate_age(self.birth_date)

    def getMobile(self):
        mobile = ''
        try:
            profile = self.user.get_profile()
            mobile = profile.mobile
        except ObjectDoesNotExist:
            pass
        return mobile

    def getAvatar(self):
        avatar = ''
        try:
            profile = self.user.get_profile()
            avatar = profile.mugshot
        except ObjectDoesNotExist:
            pass
        return avatar

    def resetPasswordAndSendSms(self, pass_form=SetPasswordForm, sender=None):
        #
        try:
            user = self.user
        except ObjectDoesNotExist:
            return False

        new_password = User.objects.make_random_password(length=6,allowed_chars='0123456789')
        data = {'new_password1': new_password, 'new_password2': new_password}
        form = pass_form(user=user, data=data)

        if form.is_valid():
            form.save()
            mobile = self.getMobile()
            content = False
            if mobile:
                username = user.username
                content = u"尊敬的用户，您的登录帐号是:" + username + u",密码是:" + new_password+u"【"+ SITE_INFO.name + "】"
                content = u"尊敬的用户您好，欢迎使用【" + SITE_INFO.name + "】家园沟通应用，您的账号：" + username + u" 密码：" + new_password+u" 登入" + SITE_INFO.domain + "即刻体验！"
                userena_signals.password_complete.send(sender=None, user=user)
                # 记录到 sms表
                #sender = self.user
                receiver = self.user

                Sms.objects.create_send_account_sms(sender=sender, receiver=receiver, mobile=mobile, content=content)

        return content


##########
# 订阅功能 #
##########

# tile标签表
class TileTag(BaseModel,SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120, null=True, blank=False, unique=True)
    description = models.TextField(_('Description'),max_length=765, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('tile tag')
        verbose_name_plural = _('tile tags')


##########
# 瓦片功能 #
##########
class TileType(BaseModel, SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120)
    description = models.TextField(_('Description'),max_length=765, blank=True)
    img = ThumbnailerImageField(_('tiletype.img'),
            blank=True,
            upload_to="tiletype",
            )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('tile type')
        verbose_name_plural = _('tile types')
        db_table = 'memory_tile_type'
        ordering = ('id',)
        #unique_together = (('app_label', 'model'),)

class TileCategory(BaseModel, SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120)
    description = models.TextField(_('Description'),max_length=765, blank=True)
    img = ThumbnailerImageField(_('TileCategory.img'),
            blank=True,
            upload_to="TileCategory",
            )
    parent = models.ForeignKey('self',null=True,blank=True,verbose_name = _('tile category parent'))

    LOOKUP_CHOICES = (
        (0, u'教师发布'),
        (1, u'后台推广'),
    )
    is_tips = models.IntegerField(_('is_tips'),default=0,choices=LOOKUP_CHOICES)
    sort = models.IntegerField(_('sort'),default=0)

    objects = TileCategoryManager()

    @property
    def is_parent(self):
        return self.parent_id == 0

    def __unicode__(self):
        return self.name

    def picture(self):
        url = helpers.media_path(self.img)
        if url:
            return '<img src='+url +' style="max-height: 100px; max-width:100px;">'
        else:
            return ''
    picture.allow_tags = True
    
    class Meta:
        verbose_name = _('tile category')
        verbose_name_plural = _('tile categorys')
        db_table = 'memory_tile_category'
        ordering = ('sort','id',)
        #unique_together = (('app_label', 'model'),)


class Tile(BaseModel,Likeable, SoftDeleteMixin):
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    user = models.ForeignKey(User, related_name="tiles",verbose_name = _('user'), null=True, blank=True, help_text='瓦片所属用户（跟班级一起为空表示所有用户，不可两者同时存在，适用于baby，推荐的瓦片范围控制）')
    group = models.ForeignKey(Group,null=True, blank=True,verbose_name = _('school class'), help_text='瓦片所属班级')
    rating = RatingField(range=5) # 5 possible rating values, 1-5
    type = models.ForeignKey(TileType,verbose_name = _('tile type'))
    category = models.ForeignKey(TileCategory,verbose_name = _('tile category'), default=0, blank=True, null=True)

    title = models.CharField(_('title'),max_length=120)

    img = ThumbnailerImageField(_('tile.img'),
            blank=True,
            upload_to=upload_to_mugshot,
            )

    n_comments = models.IntegerField(_('n_comments'),default=0, blank=True,null=True)
    n_likers = models.IntegerField(_('n_likers'),default=0, blank=True)
    view_count = models.IntegerField(_('view_count'),default=0,blank=True,null=True)
    api_count = models.IntegerField(_('api_count'),default=0,blank=True,null=True)
    is_public = models.BooleanField(_('is_public'),default=False,help_text='公开则所有用户可见（包括未收费），非公开则家长用户的身份可见。')

    LOOKUP_CHOICES = (
        (0, u'教师发布'),
        (1, u'后台推广'),
        )
    is_tips = models.IntegerField(_('is_tips'),default=0,null=True,choices=LOOKUP_CHOICES)
   # is_tips = models.BooleanField(_('is_tips'),default=False)


    video = models.CharField(_('video'),max_length=255, blank=True)
    # 一个tile属于的chanle
    tags = models.ManyToManyField(TileTag, related_name="tiles", blank=True, null=True,verbose_name = _('tile tag'))

    description = models.TextField(_('Description'),max_length=765, blank=True)
    content = models.TextField(_('Content'),max_length=765, blank=True)
    url = models.CharField(_('Url'),max_length=255, blank=True)
    
    start_time = models.DateTimeField(null=True,blank=True, help_text='瓦片的开始时间，小于将不显示。为空默认保存为当前时间')
    end_time = models.DateTimeField(null=True,blank=True, help_text='瓦片的结束时间，大于将不显示。为空默认9999年')
    microsecond = models.DecimalField(_('Microsecond'),default=0.00, blank=True,null=True,max_digits=17,decimal_places=6)
    
    objects = TileManager()

    class Meta:
        permissions = (
            ('can_public_tiles', '发布推广内容'),
        )
        ordering = ['-start_time']
        verbose_name = _('tile')
        verbose_name_plural = _('tiles')

    def __unicode__(self):
        return unicode(self.title)

    def save(self, *args, **kwargs):
        
        if not self.start_time:
            self.start_time = datetime.datetime.now()
            
        if not self.microsecond:
            timetuple = time.mktime(self.start_time.timetuple())
            self.microsecond = D(str(int(timetuple)) + '.' + str(datetime.datetime.now().microsecond))
        
        if not self.end_time:
            self.end_time = datetime.date(9999,12,31)

        if not self.category_id:
            self.category_id = self.type_id

        super(Tile, self).save(*args, **kwargs)

    @property
    def pub_time(self):
        return self.start_time or self.ctime
    
    def picture(self):
        url = helpers.media_path(self.img)
        if url:
            return '<img src='+url +' style="max-height: 100px; max-width:100px;">'
        else:
            return ''
    picture.allow_tags = True
    
    def decade_create_time(self):
        return self.ctime.strftime('%Y-%m-%d %H:%M:%S')
    decade_create_time.short_description = '创建时间'
    decade_create_time.admin_order_field = 'ctime'

    def after_add_comments(self):
        ct = ContentType.objects.get_by_natural_key("memory", "tile")
        n_comments = Comment.objects.filter(object_pk=self.id, content_type=ct) \
            .filter(is_removed=False, is_public=True).count()
        self.n_comments = n_comments
        
        # 或者 直接 count comments 表 where content_type = tile and object_pk = self.id and is_removed = 0
        #if self.n_comments < 0:
            #self.n_comments = 0
        #else:
            #self.n_comments = self.n_comments + 1
        self.save()

    def after_del_comments(self):
        ct = ContentType.objects.get_by_natural_key("memory", "tile")
        n_comments = Comment.objects.filter(object_pk=self.id, content_type=ct) \
            .filter(is_removed=False, is_public=True).count()
        self.n_comments = n_comments
        #if self.n_comments > 0:
            #self.n_comments = self.n_comments - 1
        #else:
            #self.n_comments = 0
        self.save()

    def comments(self, limit=3):
        if self.n_comments > 0:
            return Comment.objects.for_model(self) \
                .filter(is_public=True).filter(is_removed=False) \
                .order_by("-id")[0:limit]
        else:
            return None

    def is_report(self):
        return self.type_id > 2

    def is_daily(self):
        return self.type_id == 9
    
    def is_content(self):
        if self.is_tips and self.content:
            return True
        else:
            return False
    
    def creat_user_last_tile(self, uid, tile_id):
        num = UserLastTile.objects.filter(user_id=uid).count()
        if not num:
            p = UserLastTile(user_id=uid,last_tile_id=tile_id)
            p.save()    



#瓦片访问者历史表
class TileVisitor(BaseModel,SoftDeleteMixin):
    visitor = models.ForeignKey(User, verbose_name = _('visitor'), null=True, blank=True)
    tile = models.ForeignKey(Tile,verbose_name = _('tile'), default=0, blank=True, null=True)
    visit_time = models.DateTimeField(null=True,blank=True)
    microsecond = models.DecimalField(_('Microsecond'),default=0.00, blank=True,null=True,max_digits=17,decimal_places=6)

    def __unicode__(self):
        return unicode(self.visitor)
    
    def save(self, *args, **kwargs):
        if not self.visit_time:
            self.visit_time = datetime.datetime.now()
        if not self.microsecond:
            timetuple = time.mktime(self.visit_time.timetuple())
            self.microsecond = D(str(int(timetuple)) + '.' + str(datetime.datetime.now().microsecond))
        super(TileVisitor, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('tile visitor')
        verbose_name_plural = _('tile visitors')
        db_table = 'memory_tile_visitor'
        
                     
##########
# 预设内容 #
##########
# 读取活动食谱预设配置 ps：与 http://192.168.1.222/wiki/doku.php?id=api_tiles_get_event_setting 接口相关

class EventType(BaseModel, SoftDeleteMixin):
    GROUP_TYPE = (
        (0, _('Event')),
        (1, _('Cookbook')),
        )

    name = models.CharField(_('Name'),max_length=120)
    img = ThumbnailerImageField(_('event_setting.img'),
            blank=True,
            upload_to="event_setting",
            )
    # 属于活动或者食谱
    group = models.IntegerField(null=True, blank=True, choices=GROUP_TYPE,verbose_name = _('type'))
    _content = ""

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('event type')
        verbose_name_plural = _('event types')

class EventSetting(BaseModel, SoftDeleteMixin):
    # 早餐，午餐，早点等等类型
    type = models.ForeignKey(EventType, related_name='settings',verbose_name = _('type'))
    content = models.TextField(_('Content'),max_length=765, null=False,)#blank=True,
    # 如果所在学校没有默认设置时，则读取school_id = 0 的设置
    school = models.ForeignKey(School, null=True, blank=True,verbose_name = _('school'))

    def __unicode__(self):
        return self.content

    class Meta:
        verbose_name = _('event setting')
        verbose_name_plural = _('event settings')

##########
# comment templater #
##########

class CommentTemplaterType(BaseModel, SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120)
    description = models.CharField(_('Description'),max_length=765, blank=True)

    def __unicode__(self):
        return self.name
    class Meta:
        db_table = "memory_comment_templatertype"
        verbose_name = _('comment templater type')
        verbose_name_plural = _('comment templater types')

class CommentTemplater(BaseModel, SoftDeleteMixin):
    # 早餐，午餐，早点等等类型
    type = models.ForeignKey(CommentTemplaterType, related_name='templaters')
    content = models.TextField(max_length=765, blank=True)
    #
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))

    def __unicode__(self):
        return self.content
    class Meta:
        db_table = "memory_comment_templater"
        verbose_name = _('comment templater')
        verbose_name_plural = _('comment templaters')


##########
# 导师相关 #
##########
class Mentor(BaseModel, ActiveMixin, SoftDeleteMixin):
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    user = models.OneToOneField(User,verbose_name = _('user'),related_name="mentor")

    name = models.CharField(_('Teacher name'),max_length=60)
    nationality = models.CharField(_('Nationality'),max_length=60,blank=True)
    appellation = models.TextField(_('Appellation'),max_length=60,blank=True)
    description = models.TextField(_('Description'),max_length=765, blank=True)


    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):

        profile = self.user.get_profile()
        profile.realname = self.name
        profile.is_mentor = True
        profile.save()

        super(Mentor, self).save(*args, **kwargs)

    def getAvatar(self):
        profile = self.user.get_profile()
        return profile.mugshot

    def getMobile(self):
        mobile = ''
        try:
            profile = self.user.get_profile()
            mobile = profile.mobile
        except ObjectDoesNotExist:
            pass
        return mobile

    class Meta:
        verbose_name = _('mentor')
        verbose_name_plural = _('mentors')
        ordering = ['name']

##########
# 客服人员 #
##########
class Waiter(BaseModel, ActiveMixin, SoftDeleteMixin):
    creator = models.ForeignKey(User, verbose_name = _('creator'),related_name="waiter_creator",)
    user = models.OneToOneField(User,verbose_name = _('user'),related_name="waiter")

    name = models.CharField(_('Waiter name'),max_length=60)
    appellation = models.TextField(_('Appellation'),max_length=60)
    description = models.TextField(_('Description'),max_length=765, blank=True)


    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):

        profile = self.user.get_profile()
        profile.realname = self.name
        profile.is_waiter = True
        profile.save()

        super(Waiter, self).save(*args, **kwargs)

    def getAvatar(self):
        profile = self.user.get_profile()
        return profile.mugshot

    def getMobile(self):
        mobile = ''
        try:
            profile = self.user.get_profile()
            mobile = profile.mobile
        except ObjectDoesNotExist:
            pass
        return mobile

    class Meta:
        verbose_name = _('waiter')
        verbose_name_plural = _('waiters')
        ordering = ['name']


class Device(BaseModel):
    user = models.ForeignKey(User, related_name='device',verbose_name = _('user'))
    token = models.CharField(unique=True, max_length=64)

    def __unicode__(self):
        return " %s's device" % self.user.username

    class Meta:
        verbose_name = _('device')
        verbose_name_plural = _('devices')

from APNSWrapper import *
import binascii

class ApplePushNotification(BaseModel):
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    #user = models.OneToOneField(User,verbose_name = _('user'),related_name="pushto")

    alert = models.TextField(_('alert'))
    badge = models.IntegerField(_('badge'),max_length=30,blank=True,null=True,default=1)
    sound = models.CharField(_('sound'),max_length=30,blank=True)

    tile = models.OneToOneField(Tile,verbose_name = _('tile'),null=True,blank=True)

    is_send = models.BooleanField(_('is_send'),default=False)    
    send_time = models.DateTimeField(_('send time'),null=True,blank=True)
   
    def __unicode__(self):
        return self.alert

    class Meta:
        verbose_name = _('ApplePushNotification')
        verbose_name_plural = _('ApplePushNotifications')

        ordering = ['-ctime']


class CleanCharField(models.CharField):
        """Django's default form handling drives me nuts wrt trailing
        spaces.  http://code.djangoproject.com/attachment/ticket/6362
        """
        def clean(self, value, *args, **kwargs):
            if value is None:
                value = u''
            value = value.strip()
            value = super(models.CharField, self).clean(value, *args, **kwargs)
            return value

class UserLastTile(models.Model):
    user = models.OneToOneField(User, related_name='last_tile',verbose_name = _('user'))
    last_tile_id = models.IntegerField(max_length=11,blank=True)

class ChangeUsername(models.Model):
    user = models.ForeignKey(User, related_name="user")
    name = models.CharField(_('Name'),max_length=30)
    edittime = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('ChangeUsername')
        verbose_name_plural = _('ChangeUsernames')

        ordering = ['-edittime']

##########
# 食谱 #
##########

class Cookbook(BaseModel):
    # 食谱发布者
    creator = models.ForeignKey(User, verbose_name = _('creator'))

    # 食谱条目
    breakfast = models.CharField(_('breakfast'),max_length=100,blank=True)
    light_breakfast = models.CharField(_('light breakfast'),max_length=100,blank=True)

    lunch = models.CharField(_('lunch'),max_length=100,blank=True)
    light_lunch = models.CharField(_('light lunch'),max_length=100,blank=True)

    dinner = models.CharField(_('dinner'),max_length=100,blank=True)
    light_dinner = models.CharField(_('light dinner'),max_length=100,blank=True)

    # 食谱时间
    date = models.DateField(_('cookbook date'),)

    school = models.ForeignKey(School, verbose_name = _('school'),null=True,blank=True)
    group = models.ForeignKey(Group, verbose_name = _('group'),null=True,blank=True)
    is_send = models.BooleanField(default=False, blank=False)


    objects = CookbookManager()
    
    @classmethod
    def get_items(cls):
        item = [
            'breakfast',
            'light_breakfast',
            'lunch',
            'light_lunch',
            'dinner',
            'light_dinner'
        ]
        return item
    
    def get_student(self):
        if self.group:
            return self.group.students.all()
        if self.school:
            return self.school.student_set.all()
        
    def __unicode__(self):
        cookbook = self.breakfast or self.lunch or self.dinner
        return cookbook

    class Meta:
        unique_together = (('school','date'),('group','date'))
        verbose_name = _('cookbook')
        verbose_name_plural = _('cookbook')


##########
# 食谱种类 #
##########
class CookbookType(BaseModel, SoftDeleteMixin):

    name = models.CharField(_('Name'),max_length=120)
    cname = models.CharField(_('Cname'),max_length=120)
    img = ThumbnailerImageField(_('CookbookType.img'),
            blank=True,
            upload_to="CookbookType",
            )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('cook book type')
        verbose_name_plural = _('cook book types')


##############
# 食谱已读状态 #
##############
class CookbookRead(BaseModel):

    user = models.ForeignKey(User,verbose_name = _('user'))
    cookbook = models.ForeignKey(Cookbook,verbose_name = _('cookbook'))
    date = models.DateField(_('cookbook date'),)
    is_read = models.BooleanField(default=False, blank=False)
    read_at = models.DateTimeField(_("read at"),null=True,blank=True)
    is_send = models.BooleanField(default=False, blank=False)
    objects = CookbookreadManager()

    def __unicode__(self):
        return unicode(self.user)

    class Meta:
        verbose_name = _('cookbook read')
        verbose_name_plural = _('cookbook reads')
        db_table = 'memory_cookbook_read'
        
        ordering = ['-ctime']
        
        
##########
# 学校食谱设置 #
##########

class CookbookSet(BaseModel):
    school = models.OneToOneField(School, verbose_name = _('school'))

    # 食谱条目显示与否
    breakfast = models.BooleanField(default=True)
    light_breakfast = models.BooleanField(default=True)

    lunch = models.BooleanField(default=True)
    light_lunch = models.BooleanField(default=True)

    dinner = models.BooleanField(default=True)
    light_dinner = models.BooleanField(default=True)

    objects = CookbookSetManager()

    class Meta:
        verbose_name = _('cookbook set')
        verbose_name_plural = _('cookbook set')

##########
# 验证短信 #
##########

class VerifySms(BaseModel, ActiveMixin, SoftDeleteMixin):
    """
    验证码有效期30分钟，重置成功后，成为未激活状态。
    """
    sms = models.OneToOneField(Sms, verbose_name = _('sms'))

    user = models.ForeignKey(User, verbose_name = _('user'))
    mobile = models.CharField(_('Mobile'),max_length=20)

    content = models.CharField(max_length=765, blank=True)
    vcode = models.CharField(_('vcode'),max_length=20)

    objects = VerifySmsManager()

    class Meta:
        verbose_name = _('verify sms')
        verbose_name_plural = _('verify sms')

#############
#发送班级消息  #
#############

class MessageToClass(BaseModel, SoftDeleteMixin):
    group = models.ForeignKey(Group, verbose_name = _('group'),null=True,blank=True)
    user = models.ForeignKey(User, verbose_name = _('user'), null=True, blank=True)
    content = models.CharField(max_length=765, blank=True)
    
    class Meta:
        verbose_name = _('message to calss')
        verbose_name_plural = _('message to calsses')
        db_table = 'memory_message_to_class'
        ordering = ['-ctime']


class RelevantStaff(BaseModel, SoftDeleteMixin):
    name = models.CharField(_('name'),max_length=60)
    mobile = models.CharField(_('Mobile'),max_length=20,blank=True)
    email = models.EmailField(_('e-mail address'), blank=True)
    send_mentor = models.BooleanField(_('send_mentor'),default=False)
    send_waiter = models.BooleanField(_('send_waiter'),default=False)
    
    def save(self, *args, **kwargs):
        if not self.mobile and self.email:
            send_mentor = False
            send_waiter = False
            
        super(RelevantStaff, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return str(self.name)
    
    class Meta:
        verbose_name = _('relevant staff')
        verbose_name_plural = _('relevant staffs')
        db_table = 'memory_relevant_staff'
    
    
############
# 拼音码表 #
############
class Char(models.Model):
    cn = models.CharField(max_length=60,blank=True)
    en =  models.CharField(max_length=60,blank=True,default='')

    objects = CharManager()

    class Meta:
        verbose_name = _('char')
        verbose_name_plural = _('char')
        

class Access_log(BaseModel):
    user = models.ForeignKey(User, verbose_name = _('user'), null=True, blank=True)   
    send_time = models.DateTimeField(_('send time'),auto_now_add=True)
    type = models.IntegerField(null=True, blank=True)
    url = models.CharField(_('Url'),max_length=255, blank=True)
   
    class Meta:
        verbose_name = _('access log')
        verbose_name_plural = _('access logs')

        ordering = ['-send_time']
        

class Comment_relation(BaseModel):
    target_object = models.ForeignKey(Comment, verbose_name = _('target object'), related_name='target_object')
    action_object = models.ForeignKey(Comment, verbose_name = _('action object'), related_name='action_object')
   
    class Meta:
        verbose_name = _('comment relation')
        verbose_name_plural = _('comment relations')
        
        ordering = ['-ctime']
        
        
class Activity(BaseModel,SoftDeleteMixin):
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    user = models.ForeignKey(User, verbose_name = _('user'), null=True, blank=True)
    group = models.ForeignKey(Group, verbose_name = _('group'),null=True,blank=True)
    start_time = models.DateTimeField(null=True,blank=True)
    description = models.TextField(_('Description'),max_length=765, blank=True)
    microsecond = models.DecimalField(_('Microsecond'),default=0.00, blank=True,null=True,max_digits=17,decimal_places=6)
    
    def save(self, *args, **kwargs):
        if not self.start_time:
            self.start_time = datetime.datetime.now()
        if not self.microsecond:
            timetuple = time.mktime(self.start_time.timetuple())
            self.microsecond = D(str(int(timetuple)) + '.' + str(datetime.datetime.now().microsecond))
        super(Activity, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return str(self.start_time)
    
    class Meta:
        verbose_name = _('activity')
        verbose_name_plural = _('activities')
        
        ordering = ['-start_time', '-microsecond']


class Schedule(BaseModel,SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120,null=True,blank=True)
    user = models.ForeignKey(User, related_name="schedules",verbose_name = _('user'))
    start_time = models.DateTimeField(null=True,blank=True)
    group = models.ForeignKey(Group, verbose_name = _('group'))
    src = models.FileField(upload_to='schedule')

    def __unicode__(self):
        return str(self.name)
    
    def save(self, *args, **kwargs):
        if not self.start_time:
            self.start_time = datetime.datetime.now()
        if not self.name:
            self.name = self.src.name
        super(Schedule, self).save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('schedule')
        verbose_name_plural = _('schedules')
        ordering = ['-start_time']



class TileToActivity(BaseModel):
    tile = models.ForeignKey(Tile, verbose_name = _('tile'),null=True,blank=True)
    active = models.ForeignKey(Activity, verbose_name = _('active'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('tile to activity')
        verbose_name_plural = _('tile to activities')
        db_table = 'memory_tile_to_activity'
        ordering = ['-ctime']
        

#日常记录访问者历史表
class DailyRecordVisitor(BaseModel,SoftDeleteMixin):
    visitor = models.ForeignKey(User, verbose_name = _('visitor'), null=True, blank=True)
    target_content_type = models.ForeignKey(ContentType, related_name='visitor_target')
    target_object_id = models.CharField(max_length=255)
    target = generic.GenericForeignKey('target_content_type', 'target_object_id')
    visit_time = models.DateTimeField(null=True,blank=True)
    microsecond = models.DecimalField(_('Microsecond'),default=0.00, blank=True,null=True,max_digits=17,decimal_places=6)

    def __unicode__(self):
        return unicode(self.visitor)
    
    def save(self, *args, **kwargs):
        if not self.visit_time:
            self.visit_time = datetime.datetime.now()
        if not self.microsecond:
            timetuple = time.mktime(self.visit_time.timetuple())
            self.microsecond = D(str(int(timetuple)) + '.' + str(datetime.datetime.now().microsecond))
        super(DailyRecordVisitor, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('daily record visitor')
        verbose_name_plural = _('daily record visitors')
        db_table = 'memory_daily_record_visitor'
        