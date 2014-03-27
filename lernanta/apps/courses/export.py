from apps.courses import db
import unicodecsv

def export_signup_csv(filename):
    with open(filename, 'w') as fout:
        writer = unicodecsv.writer(fout)
        writer.writerow(['signup_date', 'leave_date', 'role', 'user', 'course'])
        for signup in db.CohortSignup.objects.all():
            writer.writerow([
                signup.signup_date.isoformat(),
                signup.leave_date.isoformat() if signup.leave_date else '',
                signup.role,
                signup.user_uri,
                signup.cohort.course.id
            ])
