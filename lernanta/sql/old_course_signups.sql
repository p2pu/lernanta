select project_id, name, count(*) as new_signups 
from projects_project, projects_participation 
where
    projects_project.id = project_id and
    projects_participation.left_on is Null
group by 
    project_id 
having count(*) > 5
order by 
    new_signups;
