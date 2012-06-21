import datetime

from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site

from drumbeat.models import ModelBase
from content.models import Page
from projects.models import Project
from activity.schema import verbs
from activity.models import Activity
from replies.models import PageComment
from users.models import UserProfile

from tracker.utils import force_date


def get_google_tracking_context(instance=None):
    codes_key = 'google_analytics_tracking_codes'
    if instance:
        instance_ct = ContentType.objects.get_for_model(
            instance)
        site_ct = ContentType.objects.get_for_model(Site)
        codes_ids = []
        if instance_ct != site_ct:
            site = Site.objects.get_current()
            codes_ids.extend(get_google_tracking_context(
                site)[codes_key].values_list(
                'id', flat=True))
        codes_ids.extend(GoogleAnalyticsTracking.objects.filter(
            target_content_type=instance_ct, target_id=instance.pk).values_list(
            'tracking_code_id', flat=True))
        codes = GoogleAnalyticsTrackingCode.objects.filter(
            id__in=codes_ids)
    else:
        codes = GoogleAnalyticsTrackingCode.objects.all()
    return {codes_key: codes}


class GoogleAnalyticsTrackingCode(ModelBase):
    key = models.SlugField(unique=True)
    code = models.SlugField(unique=True)
    # extra tracking options
    logged_in_status = models.BooleanField(default=False)
    registration_event = models.BooleanField(default=False)
    # warning: not tested with multiple conversion trackings
    adwords_conversion_id = models.SlugField(blank=True, null=True)
    adwords_conversion_label = models.SlugField(blank=True, null=True)
    chartbeat_uid = models.SlugField(blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.key, self.code)


class GoogleAnalyticsTracking(ModelBase):
    """Associates a google analytics tracking code with a project, school, ..."""
    tracking_code = models.ForeignKey('tracker.GoogleAnalyticsTrackingCode',
        related_name="trackings")
    target_content_type = models.ForeignKey(ContentType, null=True)
    target_id = models.PositiveIntegerField(null=True)
    target_object = generic.GenericForeignKey('target_content_type',
        'target_id')


class PageView(ModelBase):
    session_key = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True)
    access_time = models.DateTimeField(auto_now_add=True, db_index=True)
    request_url = models.CharField(max_length=755, db_index=True)
    referrer_url = models.URLField(
                         verify_exists=False,
                         db_index=True,
                         blank=True, null=True)
    ip_address = models.IPAddressField(
                         blank=True, null=True)
    time_on_page = models.IntegerField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)

    def __repr__(self):
        msg = '<session %s, date %s, url %s, length %s, user %s>'
        return msg % (self.session_key, self.access_time, self.request_url,
            self.time_on_page, self.user)


class PageViewMetrics(ModelBase):
    """ Store consolidated PageViews for a given access_date
        per project -> page_path,
        per user or ip_address,
        per page_path        
    """
    project = models.ForeignKey('projects.Project',
        related_name='pageview_metrics')
    user = models.ForeignKey(User, null=True, blank=True)
    ip_address = models.IPAddressField(blank=True, null=True)
    access_date = models.DateField()
    page_path = models.CharField(max_length=755)
    non_zero_length_time_on_page = models.PositiveIntegerField(
        null=True, blank=True)
    non_zero_length_pageviews = models.IntegerField(null=True, blank=True)
    zero_length_pageviews = models.IntegerField(null=True, blank=True)


def update_metrics_cache(project):
    # Only computes metrics for dates before today or yesterday
    # (depending on how early it is in the day).
    # These metrics are cacheable because they will not change
    # due to future pageviews.
    # Does not recompute cached metrics (i.e. also restricts
    # how recent the dates to process should be based on what
    # we already have cached in the db).
    now = datetime.datetime.now()
    not_included_upper_bound = now.date()
    delta = datetime.timedelta(days=1)
    if now.hour < 2:
        not_included_upper_bound = not_included_upper_bound - delta
    try:
        last_cached_day = PageViewMetrics.objects.filter(
            project=project).order_by('-access_date')[0].access_date
    except IndexError:
        last_cached_day = project.created_on - delta
    visits = PageView.objects.filter(access_time__gt=last_cached_day,
        access_time__lt=not_included_upper_bound)
    # Computes metrics for each page.
    pages = Page.objects.filter(project=project)
    for page in pages:
        page_path = 'groups/%s/content/%s/' % (project.slug, page.slug)
        # Filter page views to this page (does not include visits to subpages
        # like history/ and visits to older versions of this page).
        # Also adds the date for the visits as a separate field.
        pageviews = visits.filter(request_url__endswith=page_path).extra(
            select={'access_time_date': "date(access_time)"})
        # Computes time on page on for each date for each authenticated
        # user not considering zero length visits.
        # Excludes visits with unknow/NULL time_on_page so the sum does
        # not become None.
        # Computes number of non-zero length visits.
        user_timeonpage_metrics = pageviews.exclude(
            user=None).exclude(time_on_page__isnull=True).values(
            'user_id', 'access_time_date').annotate(
            models.Sum('time_on_page'), models.Count('id'))
        for metric in user_timeonpage_metrics:
            on_db_metric, created = PageViewMetrics.objects.get_or_create(
                project=project, user_id=metric['user_id'],
                access_date=metric['access_time_date'], page_path=page_path)
            on_db_metric.non_zero_length_time_on_page = metric[
                'time_on_page__sum']
            on_db_metric.non_zero_length_pageviews = metric['id__count']
            if on_db_metric.zero_length_pageviews == None:
                on_db_metric.zero_length_pageviews = 0
            on_db_metric.save()
        # Computes number of zero-length visits for authenticated users
        # (allows people processing these metrics to add this count * a contant
        # to the time on page counts to give some weight to the
        # zero-length visits).
        user_zero_length_visits_metrics = pageviews.exclude(user=None).filter(
            time_on_page__isnull=True).values('user_id',
            'access_time_date').annotate(models.Count('id'))
        for metric in user_zero_length_visits_metrics:
            on_db_metric, created = PageViewMetrics.objects.get_or_create(
                project=project, user_id=metric['user_id'],
                access_date=metric['access_time_date'], page_path=page_path)
            on_db_metric.zero_length_pageviews = metric['id__count']
            if on_db_metric.non_zero_length_time_on_page == None:
                on_db_metric.non_zero_length_time_on_page = 0
            if on_db_metric.non_zero_length_pageviews == None:
                on_db_metric.non_zero_length_pageviews = 0
            on_db_metric.save()
        # Computes time on page on for each date for each unauthenticated
        # visitor not considering zero length visits.
        # Excludes visits with unknow/NULL time_on_page so the sum does
        # not become None.
        # Computes number of non-zero length visits.
        unauth_visitor_timeonpage_metrics = pageviews.filter(
            user=None).exclude(time_on_page__isnull=True).values(
            'ip_address', 'access_time_date').annotate(
            models.Sum('time_on_page'), models.Count('id'))
        for metric in unauth_visitor_timeonpage_metrics:
            on_db_metric, created = PageViewMetrics.objects.get_or_create(
                project=project, ip_address=metric['ip_address'],
                access_date=metric['access_time_date'], page_path=page_path)
            on_db_metric.non_zero_length_time_on_page = metric[
                'time_on_page__sum']
            on_db_metric.non_zero_length_pageviews = metric['id__count']
            if on_db_metric.zero_length_pageviews == None:
                on_db_metric.zero_length_pageviews = 0
            on_db_metric.save()
        # Computes number of zero-length visits for unauthenticated visitors
        # (allows people processing these metrics to add this count * a contant
        # to the time on page counts to give some weight to the zero-length
        # visits).
        unauth_visitor_zero_length_visits_metrics = pageviews.filter(
            user=None).filter(time_on_page__isnull=True).values(
            'ip_address', 'access_time_date').annotate(models.Count('id'))
        for metric in unauth_visitor_zero_length_visits_metrics:
            on_db_metric, created = PageViewMetrics.objects.get_or_create(
                project=project, ip_address=metric['ip_address'],
                access_date=metric['access_time_date'], page_path=page_path)
            on_db_metric.zero_length_pageviews = metric['id__count']
            if on_db_metric.non_zero_length_time_on_page == None:
                on_db_metric.non_zero_length_time_on_page = 0
            if on_db_metric.non_zero_length_pageviews == None:
                on_db_metric.non_zero_length_pageviews = 0
            on_db_metric.save()


def metrics_summary(project, users):
    """Metrics summary iterator.

    For each user, provides: username, last active date,
    total time on course pages (estimating a one minute length for visits
    of unknow/zero legth), total number of comments and
    total number of page edits."""
    project_ct = ContentType.objects.get_for_model(Project)
    page_ct = ContentType.objects.get_for_model(Page)
    comments = PageComment.objects.filter(scope_id=project.id,
        scope_content_type=project_ct)
    task_edits = Activity.objects.filter(scope_object=project,
        target_content_type=page_ct, verb=verbs['update'])
    pageviews = PageViewMetrics.objects.filter(project=project)
    index = 0
    last_username = None
    for user in users:
        if last_username != user.username:
            index += 1
            last_username = user.username
        user_pageviews = pageviews.filter(user=user)
        last_active = None
        if user_pageviews.exists():
            last_active = user_pageviews.order_by(
                '-access_date')[0].access_date
        row = [
            'anonymous%s' % index if user.deleted else user.username,
            last_active]
        metrics = user_pageviews.aggregate(
            models.Sum('non_zero_length_time_on_page'),
            models.Sum('zero_length_pageviews'))
        total_time_on_pages = (
            metrics['non_zero_length_time_on_page__sum'] or 0)
        total_time_on_pages += (
            (metrics['zero_length_pageviews__sum'] or 0) * 60)
        row.append("%.2f" % (total_time_on_pages / 60.0))
        row.append(comments.filter(author=user).count())
        row.append(task_edits.filter(actor=user).count())
        yield row


def user_total_metrics(project, users):
    """User's total metrics iterator.

    For each user, provides: username, totals for the time on course pages,
    number of non-zero length page views, number of zero-length
    page views, number of comments and number of page edits"""
    project_ct = ContentType.objects.get_for_model(Project)
    page_ct = ContentType.objects.get_for_model(Page)
    comments = PageComment.objects.filter(scope_id=project.id,
        scope_content_type=project_ct)
    task_edits = Activity.objects.filter(scope_object=project,
        target_content_type=page_ct, verb=verbs['update'])
    pageviews = PageViewMetrics.objects.filter(project=project)
    index = 0
    last_username = None
    for user in users:
        if last_username != user.username:
            index += 1
            last_username = user.username
        row = ['anonymous%s' % index if user.deleted else user.username]
        metrics = pageviews.filter(user=user).aggregate(
            models.Sum('non_zero_length_time_on_page'),
            models.Sum('non_zero_length_pageviews'),
            models.Sum('zero_length_pageviews'))
        row.append("%.2f" % (
            (metrics['non_zero_length_time_on_page__sum'] or 0) / 60.0))
        row.append(metrics['non_zero_length_pageviews__sum'] or 0)
        row.append(metrics['zero_length_pageviews__sum'] or 0)
        row.append(comments.filter(author=user).count())
        row.append(task_edits.filter(actor=user).count())
        yield row


def unauth_total_metrics(project):
    """Anonymized total metrics iterator for non-authenticated visitors.

    For each ip_address/visitor, provides: an anonym username, and totals for
    time on course pages, number of non-zero length page visits,
    and number of zero length page visits."""
    metrics = PageViewMetrics.objects.filter(
        user=None, project=project).values('ip_address').annotate(
        models.Sum('non_zero_length_time_on_page'),
        models.Sum('non_zero_length_pageviews'),
        models.Sum('zero_length_pageviews'))
    for index, metric in enumerate(metrics):
        row = ["Non-loggedin User %s" % (index + 1)]
        row.append("%.2f" % (
            (metric['non_zero_length_time_on_page__sum'] or 0) / 60.0))
        row.append(metric['non_zero_length_pageviews__sum'] or 0)
        row.append(metric['zero_length_pageviews__sum'] or 0)
        yield row


def user_total_per_page_metrics(project, user_ids):
    """User's page visit metrics iterator.

    For each page a user has visited, provides: total time on page,
    number of non-zero length visits, and number of zero-length visits.

    The information is sorted first by username and then by page path.
    """
    metrics = PageViewMetrics.objects.filter(project=project,
        user__in=user_ids).values(
        'user__username', 'page_path').order_by(
        'user__username', 'page_path').annotate(
        models.Sum('non_zero_length_time_on_page'),
        models.Sum('non_zero_length_pageviews'),
        models.Sum('zero_length_pageviews'))
    index = 0
    last_username = None
    for metric in metrics:
        username = metric['user__username']
        if username != last_username:
            index += 1
            last_username = username
        user_deleted = UserProfile.objects.filter(
            username=username,
            deleted=True).exists()
        row = [
            'anonymous%s' % index if user_deleted else username,
            metric['page_path']]
        row.append("%.2f" % (
            (metric['non_zero_length_time_on_page__sum'] or 0) / 60.0))
        row.append(metric['non_zero_length_pageviews__sum'] or 0)
        row.append(metric['zero_length_pageviews__sum'] or 0)
        yield row


def unauth_total_per_page_metrics(project):
    """Anonymized page visits metrics iterator for non-authenticated visitors.

    For each page a non-authenticated user has visited, provides:
    total time on page, number of non-zero length visits and number
    of zero-length visits.

    The information is sorted first by ip_address (anonymized)
    and then by page path.
    """
    metrics = PageViewMetrics.objects.filter(project=project,
        user=None).values('ip_address', 'page_path').order_by(
        'ip_address', 'page_path').annotate(
        models.Sum('non_zero_length_time_on_page'),
        models.Sum('non_zero_length_pageviews'),
        models.Sum('zero_length_pageviews'))
    index = 0
    last_ip_address = None
    for metric in metrics:
        ip_address = metric['ip_address']
        if last_ip_address != ip_address:
            index += 1
            last_ip_address = ip_address
        row = ["Non-loggedin User %s" % index, metric['page_path']]
        row.append("%.2f" % (
            (metric['non_zero_length_time_on_page__sum'] or 0) / 60.0))
        row.append(metric['non_zero_length_pageviews__sum'] or 0)
        row.append(metric['zero_length_pageviews__sum'] or 0)
        yield row


def chronological_user_metrics(project, users):
    """User's chronological metrics iterator.

    For each user, provides for each date in which the user was active:
    the total time on course pages, number of non-zero length page
    visits, number of zero-length visits, number of comments
    published, and number of page edits.

    The information is sorted first by username, and then by date."""
    project_ct = ContentType.objects.get_for_model(Project)
    page_ct = ContentType.objects.get_for_model(Page)
    comments = PageComment.objects.filter(scope_id=project.id,
        scope_content_type=project_ct)
    task_edits = Activity.objects.filter(scope_object=project,
        target_content_type=page_ct, verb=verbs['update'])
    pageviews = PageViewMetrics.objects.filter(project=project)
    index = 0
    last_username = None
    for user in users:
        user_pageviews = pageviews.filter(user=user)
        user_comments = comments.filter(author=user)
        user_task_edits = task_edits.filter(actor=user)
        # Compute dates for which the user either visited a course page,
        # posted a comment (can be on the wall), or edited a course page.
        dates = set(user_pageviews.distinct().values_list(
            'access_date', flat=True))
        dates.update(user_comments.extra(select={
            'created_on_date': "date(created_on)"}).distinct().values_list(
            'created_on_date', flat=True))
        dates.update(user_task_edits.extra(select={
            'created_on_date': "date(created_on)"}).distinct().values_list(
            'created_on_date', flat=True))
        dates = (force_date(d) for d in dates)
        dates = sorted(dates, reverse=True)
        username = user.username
        if last_username != username:
            index += 1
            last_username = username
        anonymized_username = 'anonymous%s' % index if user.deleted else username
        for date in dates:
            row = [anonymized_username, date.strftime("%Y-%m-%d")]
            metrics = user_pageviews.filter(access_date=date).aggregate(
                models.Sum('non_zero_length_time_on_page'),
                models.Sum('non_zero_length_pageviews'),
                models.Sum('zero_length_pageviews'))
            row.append("%.2f" % (
                (metrics['non_zero_length_time_on_page__sum'] or 0) / 60.0))
            row.append(metrics['non_zero_length_pageviews__sum'] or 0)
            row.append(metrics['zero_length_pageviews__sum'] or 0)
            comments_count = user_comments.filter(created_on__year=date.year,
                created_on__month=date.month, created_on__day=date.day).count()
            row.append(comments_count)
            task_edits_count = user_task_edits.filter(
                created_on__year=date.year, created_on__month=date.month,
                created_on__day=date.day).count()
            row.append(task_edits_count)
            yield row


def chronological_unauth_metrics(project):
    """Anonymized chronological metrics iterator for non-authenticated users.

    For each non-authenticated visitor, provides for each date
    in which this visitor was active: the total time on course pages,
    number of non-zero length page visits, and number of zero-length
    page visits.

    The information is sorted first by ip_address (anonymized) and
    then by date."""
    metrics = PageViewMetrics.objects.filter(
        user=None, project=project).values('ip_address',
        'access_date').order_by('ip_address',
        'access_date').annotate(
        models.Sum('non_zero_length_time_on_page'),
        models.Sum('non_zero_length_pageviews'),
        models.Sum('zero_length_pageviews'))
    index = 0
    last_ip_address = None
    for metric in metrics:
        ip_address = metric['ip_address']
        if last_ip_address != ip_address:
            index += 1
            last_ip_address = ip_address
        row = ["Non-loggedin User %s" % index,
            metric['access_date'].strftime("%Y-%m-%d")]
        row.append("%.2f" % (
            (metric['non_zero_length_time_on_page__sum'] or 0) / 60.0))
        row.append(metric['non_zero_length_pageviews__sum'] or 0)
        row.append(metric['zero_length_pageviews__sum'] or 0)
        yield row


def chronological_user_per_page_metrics(project, user_ids):
    """User's chronological page visits metrics iterator.

    For each user, provides for each date in which the user was
    active, and each page the user visited that day: the total
    time on page, number of non-zero length visits, and number
    of zero-length visits.

    The information is sorted first by username, then by date,
    and finally by page path.
    """
    metrics = PageViewMetrics.objects.filter(project=project,
        user__in=user_ids).order_by('user__username',
        'access_date', 'page_path')
    index = 0
    last_username = None
    for metric in metrics:
        if last_username != metric.user.username:
            index += 1
            last_username = metric.user.username
        user_deleted = UserProfile.objects.filter(
            user=metric.user, deleted=True).exists()
        row = [
            'anonymous%s' % index if user_deleted else metric.user.username,
            metric.access_date.strftime("%Y-%m-%d"),
            metric.page_path]
        row.append("%.2f" % (metric.non_zero_length_time_on_page / 60.0))
        row.append(metric.non_zero_length_pageviews)
        row.append(metric.zero_length_pageviews)
        yield row


def chronological_unauth_per_page_metrics(project):
    """Anonymized chronological page visits metrics iterator for
    non-authenticated users.

    For each non-authenticated visitor, provides for each date in which
    this visitor was active, and each page (s)he visited that day: the total
    time on page, number of non-zero length visits, and number of
    zero-length visits.

    The information is sorted first by ip_address (anonymized), then by date,
    and finally by page path."""
    metrics = PageViewMetrics.objects.filter(project=project,
        user=None).order_by('ip_address', 'access_date', 'page_path')
    index = 0
    last_ip_address = None
    for metric in metrics:
        ip_address = metric.ip_address
        if last_ip_address != ip_address:
            index += 1
            last_ip_address = ip_address
        row = ["Non-loggedin User %s" % index,
            metric.access_date.strftime("%Y-%m-%d"),
            metric.page_path]
        row.append("%.2f" % (metric.non_zero_length_time_on_page / 60.0))
        row.append(metric.non_zero_length_pageviews)
        row.append(metric.zero_length_pageviews)
        yield row
