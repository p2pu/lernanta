from projects.models import Project

import unicodecsv

def export():
    stats = []

    with open('old-comments.csv', 'w') as f:
        writer = unicodecsv.writer(f, encoding='utf-8')
        writer.writerow(['date', 'link', 'page_title', 'author', 'comment'])

        for project in Project.objects.filter(deleted=False):
            for page in project.pages.filter(deleted=False, listed=True):
                stats += [ ('https://p2pu.org/en/groups/{0}/'.format(project.slug), page.title, page.comments.count()) ]
                for comment in page.comments.all():
                    print(u'https://p2pu.org/en/groups/{0}/, "{1}", "{2}"'.format(project.slug, page.title, comment.author.username))
                    writer.writerow([
                        str(comment.created_on),
                        u'https://p2pu.org/en/groups/{0}/'.format(project.slug),
                        page.title,
                        comment.author.username,
                        comment.content
                    ])

    return stats

