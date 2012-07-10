from celery.task.schedules import crontab
from celery.decorators import periodic_task

from celery.task import Task

from models import update_metrics_cache
from projects.models import get_active_projects

#TODO celery.decorators module is being deprecated
@periodic_task(name="tracker.tasks.update_metrics", run_every=crontab(hour=4, minute=30, day_of_week="*"))
def update_metrics():
    # This runs every morning at 4:30a.m
    log = update_metrics.get_logger()
    log.debug('updating project pageview metrics')
    for project in get_active_projects():
        update_metrics_cache(project)
        UpdateCourseMetrics.apply_async((project,))


class UpdateCourseMetrics(Task):
    """ Update metrics relevant to a specific project."""
    name = 'notifications.tasks.UpdateCourseMetrics'
    
    def run(self, project, **kwargs):
        log = self.get_logger(**kwargs)
        log.debug('updating pageview metrics for {0}'.format(project.name))
        update_metrics_cache(project)
