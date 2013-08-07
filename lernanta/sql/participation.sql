/* show new courses with more than one participant */
select cohort_id, count(*) from courses_cohortsignup group by cohort_id having count(*) > 1;

/* show old courses with more than one participant */
select project_id, count(*) from projects_participation group by project_id having count(*) > 1;

/* show number of page edits per author */
select author_uri, count(*) from content2_contentversion group by author_uri;

select courses_course.title, count(*) 
from 
    courses_course, courses_cohort, courses_cohortsignup 
where 
    courses_cohortsignup.cohort_id = courses_cohort.id and courses_cohort.course_id = courses_course.id 
group by 
    cohort_id 
having 
    count(cohort_id) > 1;
