import logging
import datetime
import calendar

from django.shortcuts import render_to_response
from django.template import RequestContext
from django import http
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.utils import simplejson

from users.models import UserProfile
from replies.models import PageComment
from projects.models import Participation, Project
from signups.models import SignupAnswer


log = logging.getLogger(__name__)


def get_time_details():
    stats_date = datetime.datetime.now()
    today = stats_date.date()
    number_days_month = calendar.monthrange(
        today.year, today.month)[1]
    prev_month = (today.month - 1) if today.month > 1 else 12
    prev_month_year = today.year if today.month > 1 \
        else (today.year - 1)
    return {
        'day': today.day,
        'month': today.month,
        'year': today.year,
        'number_days_month': number_days_month,
        'prev_month': prev_month,
        'prev_month_year': prev_month_year,
        'stats_date': stats_date,
    }


def get_stats(name, objects_list, date_field_name, time_details):
    todays_count = objects_list.filter(**{
        date_field_name + '__day': time_details['day'],
        date_field_name + '__month': time_details['month'],
        date_field_name + '__year': time_details['year']
        }).count()

    this_month_count = objects_list.filter(**{
        date_field_name + '__month': time_details['month'],
        date_field_name + '__year': time_details['year']
        }).count()

    pace = this_month_count * time_details['number_days_month'] / time_details['day']

    prev_month_count = objects_list.filter(**{
        date_field_name + '__month': time_details['prev_month'],
        date_field_name + '__year': time_details['prev_month_year']
        }).count()

    green_threshold = prev_month_count * 105 / 100
    red_threshold = prev_month_count * 95 / 100

    if pace > green_threshold:
        status_color = 'green'
    elif pace < red_threshold:
        status_color = 'red'
    else:
        status_color = 'white'

    return {
        'name': name,
        'today': todays_count,
        'this_month': this_month_count,
        'pace': pace,
        'prev_month': prev_month_count,
        'status_color': status_color,
    }


def scoreboard(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        raise http.Http404
    time_details = get_time_details()
    users_stats = get_stats('users', UserProfile.objects.all(),
        'user__date_joined', time_details)
    ct = ContentType.objects.get_for_model(SignupAnswer)
    comments = PageComment.objects.exclude(page_content_type=ct)
    comments_stats = get_stats('comments', comments, 'created_on', time_details)
    joins = Participation.objects.filter(
        project__test=False, left_on__isnull=True)
    joins_stats = get_stats('joins', joins,
        'joined_on', time_details)
    groups = Project.objects.filter(test=False)
    groups_stats = get_stats('groups', groups,
        'created_on', time_details)
    context = {
        'stats': [users_stats, comments_stats, joins_stats, groups_stats],
        'stats_date': time_details['stats_date'],
    }
    return render_to_response(
        'tracker/scoreboard.html', context,
        context_instance=RequestContext(request)
    )


def scoreboard_users(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        raise http.Http404
    stats_date = datetime.datetime.now()
    users = UserProfile.objects.filter(user__date_joined__month=stats_date.month,
        user__date_joined__year=stats_date.year)
    users_ids = users.values('id')
    ct = ContentType.objects.get_for_model(SignupAnswer)
    comments_count = dict(PageComment.objects.exclude(
        page_content_type=ct).filter(author__in=users_ids).values(
        'author_id').annotate(comments_count=Count('id')).values_list(
        'author_id', 'comments_count'))
    joins_count = dict(Participation.objects.filter(user__in=users_ids).values(
        'user_id').annotate(joins_count=Count('id')).values_list(
        'user_id', 'joins_count'))
    aaData = [[u.username, comments_count.get(u.id,0), joins_count.get(u.id, 0)] for u in users]
    data = {'aaData': aaData}
    json = simplejson.dumps(data)
    return http.HttpResponse(json, mimetype="application/json")


def scoreboard_top_groups_by_comments(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        raise http.Http404
    stats_date = datetime.datetime.now()
    ct = ContentType.objects.get_for_model(SignupAnswer)
    p_ct = ContentType.objects.get_for_model(Project)
    commented_projects = PageComment.objects.exclude(page_content_type=ct).filter(
        created_on__month=stats_date.month, created_on__year=stats_date.year,
        scope_content_type=p_ct).values('scope_id').annotate(
        comments_count=Count('id'))
    aaData = [[Project.objects.get(id=p['scope_id']).slug, p['comments_count']] for p in commented_projects]
    data = {'aaData': aaData}
    json = simplejson.dumps(data)
    return http.HttpResponse(json, mimetype="application/json")


def scoreboard_top_groups_by_joins(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        raise http.Http404
    stats_date = datetime.datetime.now()
    aaData = list(Participation.objects.filter(
        joined_on__month=stats_date.month,
        joined_on__year=stats_date.year,
        project__test=False,
        left_on__isnull=True
    ).values('project__slug').annotate(
        joins_count=Count('id')
    ).values_list('project__slug', 'joins_count'))
    data = {'aaData': aaData}
    json = simplejson.dumps(data)
    return http.HttpResponse(json, mimetype="application/json")


def scoreboard_groups(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        raise http.Http404
    stats_date = datetime.datetime.now()
    groups = Project.objects.filter(created_on__month=stats_date.month,
        created_on__year=stats_date.year, test=False)
    groups_ids = groups.values('id')
    ct = ContentType.objects.get_for_model(SignupAnswer)
    p_ct = ContentType.objects.get_for_model(Project)
    comments_count = dict(PageComment.objects.exclude(page_content_type=ct).filter(
        scope_id__in=groups_ids, scope_content_type=p_ct).values(
        'scope_id').annotate(comments_count=Count('id')).values_list(
        'scope_id', 'comments_count'))
    joins_count = dict(Participation.objects.filter(project__in=groups_ids).values(
        'project_id').annotate(joins_count=Count('id')).values_list(
        'project_id', 'joins_count'))
    aaData = [[p.slug, comments_count.get(p.id,0), joins_count.get(p.id, 0)] for p in groups]
    data = {'aaData': aaData}
    json = simplejson.dumps(data)
    return http.HttpResponse(json, mimetype="application/json")
