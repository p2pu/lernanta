# Determine the command used to start Python.  This will be the
# shell's Python unless the variable ${PYTHON} is set.
ifndef PYTHON
	PYTHON=python
endif

# Command for running management tool.
MANAGE=${PYTHON} manage.py

# List all installed applications
APPS=$(notdir $(shell find apps -mindepth 1 -maxdepth 1 -type d -print))

# Clean up.
clean : tidy
	@rm -f lernanta.db lernanta.log

# Prepares existing .po for localizations and compiles them
# Public domain
# To make first time localization (for example for de_DE) run
# $ python manage.py makemessages -e ".html,.txt" -l de_DE
int :
	${MANAGE} makemessages -e ".html,.txt,.py" --all
	${MANAGE} compilemessages

# Handle schema migration for all applications.
schemamigration :
	@for i in ${APPS}; do ${MANAGE} schemamigration $$i --auto; done

# Display the settings.
settings :
	@echo "PYTHON:" ${PYTHON}
	@echo "APPS:" ${APPS}

# Synchronize the database.
syncdb :
	@${PYTHON} manage.py syncdb --noinput
	@for i in ${APPS}; do ${MANAGE} migrate $$i; done

# Run tests.
test :
	@FORCE_DB=1 ${MANAGE} test

# Run tests with coverage.
test_coverage :
	@rm -rf htmlcov
	@FORCE_DB=1 coverage run --include ${PWD}'/*.py' manage.py test || true
	@coverage html
	@${PYTHON} -c '__import__("webbrowser").open_new("file://$(PWD)/htmlcov/index.html")' > /dev/null

# Tidy up by removing .pyc files.
tidy :
	@rm -rf htmlcov `find . -name '*.pyc'` `find . -name '*~'`
