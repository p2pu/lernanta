select project_id, name, count(*) as new_signups 
from projects_project, projects_participation 
where
    projects_project.id = project_id 
    and
    projects_participation.left_on is Null
    and
    projects_project.slug in 
        (
            'get-cc-savvy', 
            'teach-someone-something-with-open-content',
            'teach-someone-something-with-open-content-part-2',
            'open-detective',
            'contributing-to-wikimedia-commons',
            'open-glam',
            'a-look-at-open-video',
            'make-something-with-the-daily-create',
            'dscribe-peer-produced-open-educational-resources',
            'open-access-wikipedia-challenge'
        )
group by 
    project_id 
order by 
    new_signups;
