from django import template

from schools.models import School


register = template.Library()


def schools_menu(context):
    schools = School.objects.all()
    context.update({'schools': schools})
    return context


register.inclusion_tag('schools/menu.html', takes_context=True)(schools_menu)


def schools_footer(context):
    schools = School.objects.all().order_by('id')[:5]
    context.update({'schools': schools})
    return context


register.inclusion_tag('schools/footer.html', takes_context=True)(schools_footer)
