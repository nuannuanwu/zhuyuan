# -*- coding: utf-8 -*-
#from django.http import HttpResponse
from django.conf import settings
from django.utils.translation import ugettext as _
from django.shortcuts import redirect, render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from memory.helpers import get_redir_url,media_path
# from django.shortcuts import render_to_response,render
# from django.template import RequestContext
from django.dispatch import receiver
from django.contrib import messages
from django.contrib.comments import Comment
from django.contrib.comments.views.moderation import perform_delete
from django.contrib.comments.signals import comment_was_posted
from django.contrib import comments
from django.contrib.auth.decorators import login_required, permission_required
# from django.views.decorators.http import require_POST, require_GET

from memory.models import Tile, TileTag, TileType, Student,Sms, VerifySms,TileCategory,Mentor,\
Cookbook,CookbookType,Access_log,Comment_relation,Activity,TileVisitor,DailyRecordVisitor,CookbookRead
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from memory import helpers
import calendar
import datetime
import time
from django.http import Http404
from django.http import HttpResponse

from memory import helpers
from django.contrib.auth.models import User
from django.core.cache import cache
from memory.settings import STATIC_URL,CTX_CONFIG
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from memory.forms import MobileForm, PwdResetForm, PwdMobileForm
from memory.profiles.models import Profile
from notifications import notify
from django.contrib.auth import views as auth_views
from django.contrib.sites.models import get_current_site
from django.db import connection
from django.http import Http404
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.sites.models import Site
try:
    import simplejson as json
except ImportError:
    import json

import random
from django.db.models import Max

import logging
logger = logging.getLogger(__name__)

def index(request, template_name="memory/tile_index.html"):
    """
    家长页面首页, 选择分类使会用 ``request.session`` 记录 `channel` 分类.用于详情页查询.

    :param channel:
        ``string``, 分别是 *Baby* 默认项, *推荐 - tips*, *所有 - all* 分类.

    :param tag_q:
        ``string``, 数据格式如: *1,3,4*. 服务于 *tips* 分类，根据标签 ``id`` 过滤

    :params type_id:
        ``int``, 单个 id. 服务于 *baby* 分类。
    """
    profile = Profile.objects.get(pk=1)
    channel_ctx = {}
    channel = request.GET.get("channel",'all')
    user = request.user
    category = TileCategory.objects.all()
    
    if request.user.is_authenticated():
        #用户登录日志
        log = Access_log()
        log.type = 2
        log.user = user
        log.url = request.get_full_path()
        log.save()
        
        tags = []
        types = []
          
        if channel == "baby":
            current_time = datetime.datetime.now()  
            category = category.filter(is_tips=False) 
            parent_category = category.filter(parent__pk=0).exclude(pk=10)     
            tiles = Tile.objects.get_tiles_baby(user).filter(category__parent__in=parent_category)
            record_tiles = Tile.objects.get_tiles_baby(user).filter(category__parent__id=10)
            today_daily_tiles = get_daily_category_tiles(record_tiles, category, current_time)   
            #today_daily_tiles = get_daily_category_tiles(tiles, category, current_time)   
           
            latest_active = get_daily_activitie_tiles(user)
            latest_cookbook = get_daily_cook_books(user,current_time)
            is_read = 1 if CookbookRead.objects.filter(user=user,cookbook=latest_cookbook,is_read=True) else 0

            # 根据页面上得到category过滤返回的瓦片分类
            scat_id = request.GET.get("scat_id", '')
            scat_pks = [int(x) for x in filter(None, scat_id.split(","))]
     
            if scat_pks:
                category_list = TileCategory.objects.filter(pk__in=scat_pks)
                q_category = Tile.objects.get_q_category(category_list)
                tiles =  tiles.filter(q_category)
            
            book_item = cook_book_item(latest_cookbook)
            
            template_name = "memory/tile_index_baby.html"
            channel_ctx = {"scat_id":scat_id, "parent_category":parent_category, "book_item":book_item, "current_time":current_time,\
                           "today_daily_tiles":today_daily_tiles,"latest_active":latest_active,"latest_cookbook":latest_cookbook,"is_read":is_read}
            
        elif channel == "tips":
            category = category.filter(is_tips=True) 
            parent_category = category.filter(parent__pk=0).exclude(pk=10)
            tiles = Tile.objects.get_tiles_edu(user).filter(category__parent__in=parent_category)
            
            # 根据页面上得到category过滤返回的瓦片分类  
            scat_id = request.GET.get("scat_id", '31')      
            scat_pks = [int(x) for x in filter(None, scat_id.split(","))]
            
            if scat_pks:
                category_list = TileCategory.objects.filter(pk__in=scat_pks)
                q_category = Tile.objects.get_q_category(category_list)
                tiles =  tiles.filter(q_category)
        
            channel_ctx = {"scat_id":scat_id, "parent_category":parent_category}
        else:
            # 个人的以及推荐的            
            tiles = Tile.objects.get_tiles_all_login(user)
            daily_category = get_daily_category()
            if daily_category:
                tiles = tiles.exclude(category__parent=daily_category)
              
    else:       
        # 公开推荐的
        channel = "all"
        tiles = Tile.objects.get_tiles_all_unlogin()
        
    ctx = {}
    content_type = ContentType.objects.get_for_model(Tile)
    ctx.update({"tiles": tiles, "content_type": content_type, "channel": channel,"category":category})
    ctx.update(channel_ctx)
    request.session['memory_channel'] = channel
    if request.is_ajax():
        page = int(request.GET.get("page",'1'))
        start = (page - 1) * 15
        end = page * 15
        tiles = tiles[start:end]
        ctx['tiles'] = tiles
        template_name = "memory/tile_index_container.html"
        return render(request, template_name, ctx)
    return render(request, template_name, ctx)


def daily_record(request, template_name="memory/daily_record.html"):
    """日常记录详情页 """
    if not is_vip(request.user):  
        return render(request, "403.html")
    current_time = datetime.datetime.now() 
    tiles = Tile.objects.get_tiles_baby(request.user)
    category = TileCategory.objects.filter(is_tips=False, parent__pk=10).exclude(pk=9)
    group_date = get_group_date(request)
    page = int(request.GET.get("page", '1'))
    start = (page - 1) * 7
    end = page * 7 
    
    is_first = {"year":0,"month":0}
    record_list = []
    for day in group_date[start:end]:
        record_dict = {}
        record_dict['day'] = day[0]
        record_dict['is_first'] = False
        #判断当年当月的首条记录
        if is_first['year'] != day[0].year or is_first['month'] != day[0].month:
            record_dict['is_first'] = True
            is_first['year'] = day[0].year
            is_first['month'] = day[0].month 

        daily_record = get_daily_category_tiles(tiles, category, day[0])
        record_dict['data'] = daily_record
        record_list.append(record_dict)
    
    ctx = {"channel":"baby", "record_list":record_list,"group_date":group_date}
    return render(request, template_name, ctx)


def get_group_date(request):
    """获得日期分组数据"""
    now = datetime.datetime.now()
    sql_where = "start_time <= '" + str(now) + "' AND is_tips = 0 AND is_delete=0"
    user = request.user
    try:
        group = user.student.group
        if group:
            sql_where = sql_where + " AND (group_id = " + str(group.id) + " OR user_id = " + str(user.id) +")"
        else:
            sql_where = sql_where + " AND user_id = " + str(user.id)
    except ObjectDoesNotExist:
        sql_where = sql_where + " AND user_id = " + str(user.id)
    
    category = TileCategory.objects.filter(is_tips=False, parent__pk=10).exclude(pk=9)
    category_id = [str(x.id) for x in category]
    if category_id:
        tag_id = "(" + ",".join(category_id) + ")"
        sql_where = sql_where + " AND category_id IN " + tag_id
    
    sql = "SELECT start_time AS days FROM`memory_tile` WHERE " + sql_where + " GROUP BY TO_DAYS(start_time) ORDER BY start_time DESC"
    cursor = connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()


def get_daily_category_tiles(tiles, category, date):
    """返回当天的日常记录"""
    current_time = date
    today_tiles = Tile.objects.get_tiles_date(date=current_time, tiles=tiles)
    daily_category = category.filter(parent__pk=10).exclude(pk=9)
    #q_daily_category = Tile.objects.get_q_category(daily_category)
    today_tiles =  today_tiles.filter(category__in=daily_category).order_by('start_time')
    #today_tiles =  today_tiles.filter(q_daily_category).order_by('start_time')
    daily_list = []
    for d in daily_category:
        daily_dict = {}
        daily_dict['id'] = d.id
        daily_dict['name'] = d.name
        daily_dict['tiles'] = []
        daily_dict['is_activitie'] = 0
        for t in today_tiles:
            if t.category_id == d.id:
                daily_dict['tiles'].append(t)
        if daily_dict['tiles']:
            daily_dict['num'] = len(daily_dict['tiles'])
            daily_dict['top'] = daily_dict['tiles'][0]  
        daily_list.append(daily_dict)
    return daily_list


@login_required
def daily_activity(request, active_id, template_name="memory/daily_activity.html"):
    """日常活动详情页"""
    user = request.user
    if not is_vip(request.user):  
        return render(request, "403.html")
    
    if active_id == '0':
        active =None
    else:
        active = get_object_or_404(Activity, pk=active_id)
        is_empty = is_empty_active(active.description)
        if is_empty:
            return render(request, "404.html")
        
    q = get_q_user(user)
    actives = Activity.objects.filter(q)
    
    mentors = Mentor.objects.all()         
    # 禁止访问其它用户的记录
    if active:
        try:
            actives.get(pk=active_id)
        except ObjectDoesNotExist:
            return render(request, "403.html")
        
        add_daily_record_visitor(user,active)#添加访问记录
   
    today = active.start_time if active else datetime.datetime.now()
    effective_date = [str(x.start_time.date()) for x in actives]
    current_date = datetime.datetime.now().date()
    effective_date.append(str(current_date))
 
    try:
        active_list = actives.filter(microsecond__gt=active.microsecond) if active else actives
        next_day = active_list.filter(start_time__gte=today).order_by("start_time","microsecond")[0]
    except:
        next_day = None
    try:
        active_list = actives.filter(microsecond__lt=active.microsecond) if active else actives
        yesterday = active_list.filter(start_time__lte=today).order_by("-start_time","-microsecond")[0]
    except:
        yesterday = None
        
    today_active = get_daily_activitie_tiles(user)
    if not next_day and not today_active and active:
        next_day = {"id":0}
    
    today = today.date()    
    ctx = {}
    ctx.update({"tile": active, "effective_date":effective_date,"yesterday": yesterday,\
                "next_day": next_day,"mentors":mentors,"ty":"events","today":today,"current_date":current_date})
    return render(request, template_name, ctx)


def get_daily_by_date(request):
    
    date = request.GET.get('date','')
    ty = request.GET.get('ty','')
    user = request.user
    try:
        group = user.student.group
        q = Q(group=group) | Q(user=user)
    except:
        q = Q(user=user)
    actives = Activity.objects.filter(q)
    
    requested_redirect = request.GET.get('next','/')
    today = datetime.datetime.now().date()
    if not date:
        return redirect(requested_redirect)
    if ty == 'events':   
        actives = actives.filter(start_time__startswith=date)
        id = actives[0].id if actives else None
        if id:
            return redirect(reverse('memory_daily_activity',kwargs={'active_id':id}))
        else:
            if date == str(today):
                return redirect(reverse('memory_daily_activity',kwargs={'active_id':0}))
            else:
                return redirect(requested_redirect)
    else:
        try:
            group = user.student.group
        except:
            return render(request, "404.html")
        school = group.school
        q = Q(group=group) | Q(school=school)
        tommory = datetime.datetime.strptime(date,"%Y-%m-%d") + datetime.timedelta(days = 1)
        q_date = Q(date__startswith=tommory.date())
        cookbooks = Cookbook.objects.filter(q & q_date).order_by('-date')
        id = cookbooks[0].id if cookbooks else None
        if id:
            return redirect(reverse('memory_daily_cookbook',kwargs={'cid':id}))
        else:
            if date == str(today):
                return redirect(reverse('memory_daily_cookbook',kwargs={'cid':0}))
            else:
                return redirect(requested_redirect)
        

@login_required
def daily_cookbook(request, cid, template_name="memory/daily_activity.html"):
    """明日食谱详情页"""
    tommorrow = datetime.datetime.now() + datetime.timedelta(days = 1)
    user = request.user
    if not is_vip(user):  
        return render(request, "403.html")
    if cid == '0':
        cookbook =None
        today = tommorrow.date()
    else:
        cookbook = get_object_or_404(Cookbook, pk=cid)
        today = cookbook.date
   
    today_book = cookbook
    try:
        group = user.student.group
    except:
        return render(request, "403.html")
    school = group.school
    mentors = Mentor.objects.all() 
    q = Q(group=group) | Q(school=school)       
    cookbooks = Cookbook.objects.filter(q).exclude(breakfast='',light_breakfast='',
                lunch='',light_lunch='',dinner='',light_dinner='').order_by('-date')
    #禁止访问其他用户数据
    if today_book:
        try:
            cookbooks.get(pk=cid)
        except ObjectDoesNotExist:
            return render(request, "403.html")
    
        helpers.mark_cookbook_as_read(request,today_book)#标记当前用户食谱数据为已读
        add_daily_record_visitor(user,today_book)#增加用户访问记录
        
    effective_date = [str(x.date + datetime.timedelta(days = -1) ) for x in cookbooks]
    current_date = datetime.datetime.now().date()
    effective_date.append(str(current_date))
    
    try:
        lastday_book =cookbooks.filter(date__lt=today)[0]
    except:
        lastday_book = None
        
    tommory = datetime.datetime.now() + datetime.timedelta(days = 1)
    tommory_date = tommory.date()
    try:
        nextday_book =cookbooks.filter(date__gt=today,date__lte=tommory_date).reverse()[0]
    except:
        nextday_book = None
        
    current_book = get_daily_cook_books(user,datetime.datetime.now())
    if not nextday_book and not current_book and today_book:
        nextday_book = {"id":0}
    
    book_item = cook_book_item(today_book)
    today = today + datetime.timedelta(days = -1)
    ctx = {}
    ctx.update({"effective_date":effective_date,"book_item":book_item,"cookbooks": cookbooks, "today_book": today_book,"tommorrow":tommorrow, \
                "yesterday": lastday_book, "next_day": nextday_book,"mentors":mentors, "ty":"cookbook","today":today,"current_date":current_date})
    return render(request, template_name, ctx)
    

def cook_book_item(book):
    """返回指定的食谱详系数据"""
    book_item = []
    if not book:
        return book_item
    book_type = CookbookType.objects.all()
    book_content = {"breakfast":book.breakfast,"light_breakfast":book.light_breakfast,"lunch":book.lunch, \
                    "light_lunch":book.light_lunch,"dinner":book.dinner,"light_dinner":book.light_dinner}
    
    for t in book_type:
        item = {}
        item['name'] = t.name
        a = item['name']
        item['cname'] = t.cname
        item['img'] = t.img
        item['content'] = book_content[t.name]
        book_item.append(item)
    return book_item
    
    
def get_daily_activitie_tiles(user):
    """判断并返回当天是否有学习生活记录"""
    current_time = datetime.datetime.now()
    date = current_time.date()
    q = get_q_user(user)
    q = q & Q(start_time__startswith=date)       
    actives = Activity.objects.filter(q)
    if actives:
        last_active = actives[0]
    else:
        last_active = None
    return last_active


def get_daily_cook_books(user,now):
    """查询明日食谱，若没有则返回None"""
    tommorrow = now + datetime.timedelta(days = 1)
    date = tommorrow.date()
    try:
        group = user.student.group
        if group:
            tomorrow_recipes = Cookbook.objects.filter(group=group,date=date).exclude(breakfast='',light_breakfast='',
                lunch='',light_lunch='',dinner='',light_dinner='').order_by('-date')
            if not tomorrow_recipes:
                school = group.school
                tomorrow_recipes = Cookbook.objects.filter(school=school,date=date).exclude(breakfast='',light_breakfast='',
                lunch='',light_lunch='',dinner='',light_dinner='').order_by('-date')    
        else:
            tomorrow_recipes = None
    except ObjectDoesNotExist:
        tomorrow_recipes = None
    if tomorrow_recipes:
        last_book = tomorrow_recipes[0]
        return last_book
    else:
        return None

    
@login_required
def cal(request, template_name="memory/tile_board.html"):
    """
    | 以日历形式展示历史记录，按月显示.
    | 日历只展示 属于个人或者所在班级的记录, 即 *baby* 分类. 所以要清除 session

    :param month:
        当前月份.
    """
    try:
        request.session.pop('memory_channel')
    except KeyError:
        pass
    cal = calendar
    cur_month_date = datetime.datetime.today()
    try:
        month = request.GET.get("month")
        if month:
            cur_month_date = datetime.datetime.strptime(month, "%Y-%m")
    except Exception, e:
        logger.error(e)

    prev_month = helpers.move_month(cur_month_date, "-")
    next_month = helpers.move_month(cur_month_date, "+")

    month_cal = cal.monthcalendar(cur_month_date.year, cur_month_date.month)


    tiles = Tile.objects.get_tiles_baby(request.user)
   
    tiles = tiles.filter(start_time__year=cur_month_date.year,start_time__month=cur_month_date.month)
    daily_category = get_daily_category()
    if daily_category:
        tiles = tiles.exclude(category__parent=daily_category)
        
    ctx = {"month_cal": month_cal, "cur_month_date": cur_month_date, "is_cal": True}
    ctx.update({"prev_month": prev_month, "next_month": next_month, 'tiles':tiles })
    return render(request, template_name, ctx)

@login_required
def view(request, tile_id, template_name="memory/tile_view.html"):
    """ 瓦片详情页， 会显示与该瓦片相关的今日记录, 根据分类过滤"""
    tile = get_object_or_404(Tile, pk=tile_id)
    user = request.user
    tile.view_count += 1
    tile.save()
    add_tile_visitor(user,tile)
    
    channel = request.session.get("memory_channel")
    channel = request.GET.get("channel")
    type = request.GET.get("ty","")
    month = request.GET.get("month","")

    if channel == "tips":
        tiles = Tile.objects.get_tiles_edu(user)
        tiles = Tile.objects.filter(category__is_tips=True)

    elif channel == "all":
        tiles = Tile.objects.get_tiles_all_login(user)

    else:
        tiles = Tile.objects.get_tiles_baby(user)        
        # 禁止访问其它用户的记录
        if tile.creator != user:
            try:
                tiles.get(pk=tile_id)
            except ObjectDoesNotExist:
                if not tile.is_public:
                    return render(request, "403.html")

    today = tile.pub_time
    today_tiles = Tile.objects.get_tiles_date(date=today, tiles=tiles)
    daily_category = get_daily_category()
    if daily_category:
        today_tiles = today_tiles.exclude(category__parent=daily_category)
    today_tiles = today_tiles.order_by("-start_time","-microsecond")
    
    try:
        next_day = Tile.objects.get_tiles_date_grater(date=today, tiles=tiles.filter(microsecond__gt=tile.microsecond)).order_by("start_time","microsecond")
        next_day = next_day.exclude(category__parent=daily_category)[0] if daily_category else next_day[0]   
    except:
        next_day = None
    try:
        yesterday = Tile.objects.get_tiles_date_less(date=today, tiles=tiles.filter(microsecond__lt=tile.microsecond)).order_by("-start_time","-microsecond")
        yesterday = yesterday.exclude(category__parent=daily_category)[0] if daily_category else yesterday[0]       
    except:
        yesterday = None
        
    if tile.n_comments > 0:
        comments = Comment.objects.for_model(tile).select_related('user')\
            .order_by("-submit_date").filter(is_public=True).filter(is_removed=False)
    else:
        comments = None
        
    ctx = {}
    # content_type = ContentType.objects.get_for_model(Tile)

    # 单击分页
    #tile_pk_list = [t.pk for t in today_tiles]
    #p = Paginator(today_tiles,15)

    # 有可能来自不同频道，而没有找到
    #try:
        #p_index = tile_pk_list.index(tile.pk)//15 + 1
    #except:
        #messages.error(request, '请转换到全部')
       # p_index = 1

    #today_tiles = p.page(p_index)
    emo_config = helpers.emo_config()

    ctx.update({"tile": tile, "cur_tile": tile, "today_tiles": today_tiles, "ty":type, "comments": comments, \
        "yesterday": yesterday, "next_day": next_day,"month": month,"channel": channel,"emo_config":emo_config})
    return render(request, template_name, ctx)


@login_required
#@require_POST
#@permission_required("comments.can_moderate")
def delete_comment(request, comment_id):
    """ 评论删除后，减少对应*瓦片*的评论数(冗余字段), 并跳转且作出提示 """

    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)
    if request.user == comment.user:
        perform_delete(request, comment)
        comment.content_object.after_del_comments()
        messages.success(request, _("Comment deleted success"))
    else:
        messages.error(request, _("You can't delete this comment"))

    # Flag the comment as deleted instead of actually deleting it.
    return redirect(get_redir_url(request))


@receiver(comment_was_posted, sender=Comment)
def comment_messages(sender, comment, request, **kwargs):
    """ 添加评论后，增加对应*瓦片*的评论数(冗余字段), 并跳转且作出提示 """
    
    cid = request.REQUEST.get('cid')
    try:
        comment.content_object.after_add_comments()
        #添加一条提醒
        actions = {'title':'新消息','href':request.REQUEST.get('next') + "#comment_div_" + str(comment.id)}
        tile = comment.content_object
        
        if tile.creator != request.user:
            notify.send(request.user, verb='新消息', action_object=tile, recipient=tile.creator, actions=actions)
        if cid:
            comment_obj = get_object_or_404(Comment, pk=cid)
            relation = Comment_relation()
            relation.target_object = comment_obj
            relation.action_object = comment
            relation.save()
            if comment_obj.user != request.user:
                notify.send(request.user, verb='新消息', action_object=comment_obj, recipient=comment_obj.user, actions=actions)
    except:
        pass

    if request.user.is_authenticated():
#        last_comment_time = Comment.objects.filter(user=request.user).exclude(id=comment.id).aggregate(Max('submit_date'))
#        end_time = last_comment_time['submit_date__max'] + datetime.timedelta(seconds = 10)
#        if comment.submit_date > end_time:
        comment._set_url("http://www." + str(time.mktime(datetime.datetime.now().timetuple())) + ".com")
        comment.save()
        
        messages.add_message(
            request,
            messages.SUCCESS,
            _('Thank you for your comment!')
        )
    else:
        messages.add_message(
            request,
            messages.INFO,
            _('Thank you for your comment! Your comment is awaiting moderation.')
        )

import binascii
try:
    from sae_extra.apns import Apns
except:
    pass
def test(request):

    body = {'alert':'message','badge':1,'sound' : 'in.caf'}
    cert_id = 482
    device_token = '10b916771c9d0041e9abdb14051eaf745b82a6d4d79e030ebcefb7b89a4adbf8'
    apns = Apns()
    result = apns.push( cert_id , body , device_token );
    return HttpResponse(result)

def is_vip(user):
    """是否为vip用户"""
    try:
        d = isinstance(user.student,Student)
        if d:
            return True
        else:
            return False
    except Exception:
        return False

@login_required
def get_user_info(request):
    """ 鼠标移动到头像，显示用户详情信息 """
    uid = request.GET.get('uid')
    if not uid:
        return helpers.ajax_error('失败')
    uid = int(uid)
    try:
        user = User.objects.get(pk=uid)
    except Exception, e:
        return helpers.ajax_error('失败')
    
    try:       
        pro = user.get_profile()       
        about_me = pro.about_me
        user_name = pro.chinese_name_or_username()       
        image = pro.mugshot
        if not pro.can_view_profile(request.user): about_me = ''
    except Exception, e:      
        image = ''
        about_me = ''
        user_name = user.username

    url = media_path(image)    
    # 消息对话链接    
    talk_link = reverse('user_umessages_history',kwargs={'uid':user.id})
    show_talk = True if user.id != request.user.id else False
    info = {
        "about_me":about_me,
        "user_name":user_name,
        "avatar":url,
        "talk_link":talk_link,
        "show_talk":show_talk
    }
    return helpers.ajax_ok('成功',con=info)

@login_required
def vcar(request, template_name="memory/includes/vcar.html"):
    """ 鼠标移动到头像，显示用户详情信息 """
    uid = request.GET.get('uid')
    if not uid:
        return helpers.ajax_error('失败')
    uid = int(uid)
    try:
        user = User.objects.get(pk=uid)
    except Exception, e:
        return helpers.ajax_error('失败')
    
    is_mentor = False
    try:       
        pro = user.get_profile()
        is_mentor = pro.is_mentor
        if is_mentor:
            about_me = user.mentor.description
            appellation = user.mentor.appellation
        else:
            appellation = ''
            about_me = pro.about_me
        user_name = pro.chinese_name_or_username()       
        image = pro.mugshot
        if not pro.can_view_profile(request.user): about_me = ''
    except Exception, e: 
        appellation = ''     
        image = ''
        about_me = ''
        user_name = user.username
    
    url = media_path(image, size="avatar")   
    url = url if url else STATIC_URL + CTX_CONFIG['DEFAULT_AVATAR']
    
    # 消息对话链接    
    talk_link = reverse('user_umessages_history',kwargs={'uid':user.id})
    show_talk = True if user.id != request.user.id else False
    info = {
        "uid":uid,    
        "about_me":about_me,
        "user_name":user_name,
        "avatar":url,
        "user":user,
        "is_mentor":is_mentor,
        "talk_link":talk_link,
        "show_talk":show_talk,
        "appellation":appellation
    }
    data = render(request, template_name, info)
    con=data.content
    return helpers.ajax_ok('成功',con)


def get_category_relation():
    """瓦片分类，父类所包含子类的列表"""
    cursor = connection.cursor()
    cursor.execute(
        "SELECT parent_id AS pid , GROUP_CONCAT(id) AS sid FROM `memory_tile_category` WHERE parent_id != 0 GROUP BY parent_id "
        )
    desc = cursor.description
    rows = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
    return rows

def get_daily_category():
    """日常记录瓦片分类的父类"""
    try:
        daily_category = TileCategory.objects.get(pk=10)
    except:
        daily_category = None
    return daily_category
    
def is_empty_active(desc):
    """判断日常活动内容是否为空"""
    daily = {'events':''}
    try:
        daily = json.loads(desc)
    except:
        pass
    if not daily['events']:
        return True 
    else:
        i = 0
        for d in daily['events']:
            if not d['content']:
               i += 1 
        if i == len(daily['events']):
            return True
    return False

def remove_empty_active(tiles):
    """移除日常活动为空的记录"""
    if tiles:
        empty_tile = []
        for t in tiles:
            if is_empty_active(t.description):
                empty_tile.append(t.id)
        if empty_tile:
            tiles = tiles.exclude(id__in=empty_tile)
    return tiles
         
def add_tile_visitor(user,tile):
    """增加瓦片访问者"""
    tile_visitor = TileVisitor()
    tile_visitor.visitor = user
    tile_visitor.tile = tile
    tile_visitor.save()
    
def add_daily_record_visitor(user,obj):
    """增加对象访问者"""
    new_visitor = DailyRecordVisitor()
    new_visitor.visitor = user
    new_visitor.target = obj
    new_visitor.save()          
    
from api.handlers.message import MessageHandler
def unread_list(request):
    user = request.user
    if request.user.is_authenticated():
        con = MessageHandler().unread_count(request)
        return helpers.ajax_ok('成功',con)
    else:
        return helpers.ajax_error('失败','')

@login_required
def mark_cookbook_as_read(request):
    cid = request.POST.get('cookbook',0)
    try:
        cookbook = get_object_or_404(Cookbook, pk=cid)
    except:
        cookbook = None
    if cookbook:
        helpers.mark_cookbook_as_read(request,cookbook)
    return HttpResponse('')
        

def introduction(request, template_name="memory/introduction.html"):
    """成长介绍"""
    return render(request, template_name)
 
def get_q_user(user):
    """返回用户及用户所在班级的查询"""
    try:
       group = user.student.group
       q = Q(group=group) | Q(user=user)
    except:
        q = Q(user=user)
    return q