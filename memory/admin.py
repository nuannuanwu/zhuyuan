# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models

# from django.utils.translation import ugettext as _
from memory.models import Tile,TileCategory
from oauth2app.models import Client, AccessToken, Code

from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.admin import widgets, helpers
from django.contrib.admin.util import unquote

from memory.widgets import AdminImageWidget
from memory import settings
from django.contrib.comments import Comment
from django.core.urlresolvers import reverse  
      
admin.site.register(Tile)
admin.site.register(TileCategory)





