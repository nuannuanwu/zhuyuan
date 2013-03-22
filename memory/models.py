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


class TileCategory(BaseModel, SoftDeleteMixin):
    name = models.CharField(_('Name'),max_length=120)
    description = models.TextField(_('Description'),max_length=765, blank=True)
    img = ThumbnailerImageField(_('TileCategory.img'),blank=True, upload_to="TileCategory",)
    parent = models.ForeignKey('self',null=True,blank=True,verbose_name = _('tile category parent'),default=0)
    sort = models.IntegerField(_('sort'),default=0)

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


class Tile(BaseModel,Likeable, SoftDeleteMixin):
    creator = models.ForeignKey(User, related_name="+",verbose_name = _('creator'))
    user = models.ForeignKey(User, related_name="tiles",verbose_name = _('user'), null=True, blank=True)
    category = models.ForeignKey(TileCategory,verbose_name = _('tile category'), default=0, blank=True, null=True)
    title = models.CharField(_('title'),max_length=120)
    img = ThumbnailerImageField(_('tile.img'), blank=True,upload_to='tiles')
    n_likers = models.IntegerField(_('n_likers'),default=0, blank=True)
    is_public = models.BooleanField(_('is_public'),default=False)
    video = models.CharField(_('video'),max_length=255, blank=True)
    description = models.TextField(_('Description'),max_length=765, blank=True)
    content = models.TextField(_('Content'),max_length=765, blank=True)
    url = models.CharField(_('Url'),max_length=255, blank=True)
    start_time = models.DateTimeField(null=True,blank=True, help_text='瓦片的开始时间，小于将不显示。为空默认保存为当前时间')
    end_time = models.DateTimeField(null=True,blank=True, help_text='瓦片的结束时间，大于将不显示。为空默认9999年')
    microsecond = models.DecimalField(_('Microsecond'),default=0.00, blank=True,null=True,max_digits=17,decimal_places=6)

    class Meta:
        ordering = ['-start_time']
        verbose_name = _('tile')
        verbose_name_plural = _('tiles')

    def __unicode__(self):
        return unicode(self.title)

    def picture(self):
        url = helpers.media_path(self.img)
        if url:
            return '<img src='+url +' style="max-height: 100px; max-width:100px;">'
        else:
            return ''
    picture.allow_tags = True

    def save(self, *args, **kwargs):
        
        if not self.start_time:
            self.start_time = datetime.datetime.now()
            
        if not self.microsecond:
            timetuple = time.mktime(self.start_time.timetuple())
            self.microsecond = D(str(int(timetuple)) + '.' + str(datetime.datetime.now().microsecond))
        
        if not self.end_time:
            self.end_time = datetime.date(9999,12,31)

        super(Tile, self).save(*args, **kwargs)

class ChangeUsername(models.Model):
    user = models.ForeignKey(User, related_name="user")
    name = models.CharField(_('Name'),max_length=30)
    edittime = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = _('ChangeUsername')
        verbose_name_plural = _('ChangeUsernames')

        ordering = ['-edittime']

        