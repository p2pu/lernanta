select 
    course_id, courses_course.title, count(*) as number_signups
from 
    courses_course, courses_cohort, courses_cohortsignup
where 
    courses_cohortsignup.cohort_id = courses_cohort.id and courses_cohort.course_id = courses_course.id
    and courses_course.id in (632, 667, 620, 5, 77, 588, 140, 3)
group by 
    cohort_id
order by 
    number_signups;
