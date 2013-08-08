select 
    course_id, courses_course.title, count(*) as edit_count
from 
    courses_coursecontent, courses_course, content2_contentversion where courses_coursecontent.course_id = courses_course.id and courses_coursecontent.content_uri = CONCAT('/uri/content/', content2_contentversion.container_id) 
group by course_id 
having count(*) > 10
order by edit_count;
