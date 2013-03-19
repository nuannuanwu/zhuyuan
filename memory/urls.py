# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from memory import settings
from memory.forms import KSignupForm, KChangeEmailForm, KEditProfileForm, KAuthenticationForm


# handler404 = "memory.views.errors.handler404"
handler500 = "memory.views.errors.handler500"

urlpatterns = patterns("memory.views.frontend",
        url('^index/$', "index", name="home"),
        url('^cal/$', "cal", name="memory_cal"),
        url('^test/$', "test", name="memory_test"),
        url(r'^$', "index", name='home'),
        url('^tile/(?P<tile_id>\d+)/$', "view", name='tile_view'),
        url('^tile/comment/(?P<comment_id>\d+)/delete/$', "delete_comment", name='tile_delete_comment'),
        url(r'^get_user_info/$', "get_user_info", name="memory_get_user_info"), 
        url(r'^vcar/$', "vcar", name="memory_vcar"),
        url(r'^unread_list/$', "unread_list", name="memory_unread_list"),
        url(r'^daily_record/$', "daily_record", name="memory_daily_record"),
        url(r'^daily_activity/(?P<active_id>\d+)/$', "daily_activity", name="memory_daily_activity"),
        url(r'^daily_cookbook/(?P<cid>\d+)/$', "daily_cookbook", name="memory_daily_cookbook"),
        url(r'^daily_date/$', "get_daily_by_date", name="get_daily_by_date"),
        url(r'^mark_cookbook_as_read/$', "mark_cookbook_as_read", name="memory_mark_cookbook_as_read"),
        url(r'^introduction/$', "introduction", name="memory_introduction"),
)
                       
# 找回密码各项
urlpatterns += patterns("memory.views.account",
    url(r'^accounts/pwd_back_mail/$', "pwd_back_mail", name="memory_pwd_back_mail"),
    url(r'^accounts/pwd_back_mail_done/$', "pwd_back_mail_done", name="memory_pwd_back_mail_done"),
    url(r'^accounts/pwd_back_mail_reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
     'pwd_back_mail_reset',
   name='memory_pwd_back_mail_reset'),


    url(r'^accounts/pwd_back_mobile/$', "pwd_back_mobile", name="memory_pwd_back_mobile"),
    url(r'^accounts/pwd_back_mobile_get_vcode/$', "pwd_back_mobile_get_vcode", name="memory_pwd_back_mobile_get_vcode"),

    url(r'^accounts/pwd_back_pwd_reset/$', "pwd_back_pwd_reset", name="memory_pwd_back_pwd_reset"),
    url(r'^accounts/pwd_back_success/$', "pwd_back_success", name="memory_pwd_back_success"),        
)

urlpatterns += patterns("memory.views.admin.advimage",
        url(r'^upload_image/$', "upload_image", name="upload_image"),
)

#urlpatterns += patterns("memory.views.admin.extend",
        #url(r'^cookbook_info/(?P<cid>\d+)/$', "cookbook_info", name="admin_cookbook_info"),
        #url(r'^tile_change/$', "tile_change_form", name="admin_tile_change_form"),
        #url(r'^not_logged_in_sms/$', "not_logged_in_sms", name="admin_not_logged_in_sms"),
#)

urlpatterns += patterns('',
                        
    url(r'^admin/', include('memory.views.admin.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
    # # Edit profile
    url(r'^accounts/(?P<username>[\.\w]+)/edit/$',
       "userena.views.profile_edit", {'edit_profile_form': KEditProfileForm},
       name='userena_profile_edit'),
    url(r'^account_setting/$', 'userena.views.account_setting', name="userena_account_setting"),
    url(r'^accounts/signup/$',
       "userena.views.signup", {'signup_form': KSignupForm},
       name='userena_signup'),
    # Change email and confirm it
    url(r'^accounts/(?P<username>[\.\w]+)/email/$',
       "userena.views.email_change", {"email_form": KChangeEmailForm},
       name='userena_email_change'),
    url(r'^accounts/signin/$',
       "userena.views.signin", {"auth_form": KAuthenticationForm},
       name='userena_signin'),
    (r'^accounts/', include('userena.urls')),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^manage/', include('manage.urls')),

    # 专家问答
    (r'^aq/', include('aq.urls')),

    # 客服问答
    (r'^waiter/', include('waiter.urls')),

    # 短信相关
    (r'^sms/', include('sms.urls')),

    # 站内提醒
    ('^notification/', include('notifications.urls',namespace='notifications')),

    (r'^photologue/', include('photologue.urls')),
    url(r'^like/', include('likeable.urls')),


    #(r'^messages/', include('userena.contrib.umessages.urls')),

    #url(r'^message/(?P<message_id>\d+)/delete/$',        "memory.views.message.message_delete",        name='userena_umessages_delete'),

    (r'^client/', include('memory.apps.client.urls')),
    (r'^oauth2/', include('memory.apps.oauth2.urls')),
    (r'^api/v1/', include('api.urls',app_name='api')),

    (r'^backend/', include('backend.urls')),

    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/_static/img/favicon.ico'}),

)

urlpatterns += patterns("memory.views.message",
    url(r'^messages/$',
        "message_list",
        name='userena_umessages_list'),
    
    url(r'^message/history/(?P<uid>\d+)/$',
        "user_message_history",
        name='user_umessages_history'),
    
    url(r'^message/history/(?P<username>[\.\w]+)/$',
        "message_history",
        name='userena_umessages_history'),
                        
    url(r'^message/quick_contact/$',
        "message_quick_contact",
        name='userena_umessages_quick_contact'),

    url(r'^message/remove/$',
        "message_remove",
        name='userena_umessages_remove'),

    url(r'^message/contact_remove/(?P<username>[\.\w]+)$',
        "contact_remove",
        name='userena_umessages_contact_remove'),
)

urlpatterns += patterns('',
    url(r'^captcha/', include('captcha.urls')),
)

urlpatterns += patterns('memory.views.test',
    url(r'^tests/', 'test'),
)

urlpatterns += patterns('',
    # media 目录
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
        'django.views.static.serve', {"document_root": settings.MEDIA_ROOT}),
)

urlpatterns += patterns('',
    # media 目录
    url(r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:],
        'django.views.static.serve', {"document_root": settings.STATIC_ROOT}),
)

if settings.DEBUG is False:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )
