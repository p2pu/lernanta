select 
    course_id, courses_course.title, count(*) as number_signups
from 
    courses_course, courses_cohort, courses_cohortsignup
where 
    courses_cohortsignup.cohort_id = courses_cohort.id and courses_cohort.course_id = courses_course.id 
group by 
    cohort_id
having 
    count(cohort_id) > 5
order by 
    number_signups;
