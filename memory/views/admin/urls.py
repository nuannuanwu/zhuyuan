# -*- coding: utf-8 -*-
from django.conf.urls import patterns,  url


urlpatterns = patterns('',

)

urlpatterns += patterns("memory.views.admin.extend",
    url(r'^memory/sms/not_logged_in/$', "not_logged_in_sms", name="admin_not_logged_in_sms"),
    url(r'^memory/cookbook/(?P<cid>\d+)/status/$', "cookbook_info", name="admin_cookbook_info"),
    url(r'^memory/tile/tile_change/$', "tile_change_form", name="admin_tile_change_form"),
    url(r'^send_staff_unread/$', "send_staff_unread", name="admin_send_staff_unread"),
)

