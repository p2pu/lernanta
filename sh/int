# Prepares existing .po for localizations and compiles them
# Public domain
# To make first time localization (for example for de_DE) run
#     python manage.py makemessages -e ".html,.txt" -l de_DE

l=`(cd locale; ls)`
for lang in $l; do
	python manage.py makemessages -e ".html,.txt,.py" -l $lang
done;
python manage.py compilemessages
