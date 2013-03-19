# -*- coding: utf-8 -*-
from functools import wraps
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.views import login
from django.contrib.auth import REDIRECT_FIELD_NAME
from memory.models import Teacher
from django.contrib.auth.views import redirect_to_login


def school_admin_required(view_func):
    """
        检查是否具有学校管理员
    """
    @wraps(view_func)
    def check_perms(request, *args, **kwargs):
        user = request.user
        path = request.build_absolute_uri()
        if user.has_perm('memory.can_manage_school'):       
            return view_func(request, *args, **kwargs)
        elif user.is_authenticated():
            messages.error(request, '你不是学校管理员，无权访问。请用学校管理员账号登录。')           
            return redirect_to_login(path)
        else:
            messages.info(request, '访问学校管理后台，请用学校管理员账号登录')  
            return redirect_to_login(path)
    return check_perms

# def school_admin_required(view_func):
#     """
#     Decorator for views that checks that the user is logged in and is a staff
#     member, displaying the login page if necessary.
#     """
#     @wraps(view_func)
#     def _checklogin(request, *args, **kwargs):
#         user = request.user
#         if user.has_perm("memory.can_manage_school"):
#             # The user is valid. Continue to the admin page.
#             return view_func(request, *args, **kwargs)

#         assert hasattr(request, 'session'), "The Django admin requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
#         defaults = {
#             'template_name': 'admin/login.html',
#             'authentication_form': AdminAuthenticationForm,
#             'extra_context': {
#                 'title': _('Log in'),
#                 'app_path': request.get_full_path(),
#                 REDIRECT_FIELD_NAME: request.get_full_path(),
#             },
#         }
#         return login(request, **defaults)
#     return _checklogin

def school_teacher_required(view_func):
    """
        检查是否为老师用户
    """
    @wraps(view_func)
    def check_perms(request, *args, **kwargs):
        user = request.user
        path = request.build_absolute_uri()
        if is_teacher(user):       
            return view_func(request, *args, **kwargs)
        elif user.is_authenticated():
            messages.error(request, '你不是老师用户，无权访问。请用老师账号登录。')           
            return redirect_to_login(path)
        else:
            #messages.info(request, '')  
            return redirect_to_login(path)
    return check_perms


def is_teacher(user):
    """是否为老师用户"""
    try:
        d = isinstance(user.teacher,Teacher)
        if d:
            return True
        else:
            return False
    except Exception:
        return False