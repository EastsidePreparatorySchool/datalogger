# datalogger
A web API to ingest and report back IoT data for the Topics in CS course


TO activate the virtual environment run Scripts\activate from the root

Requirement: install flask
pip install flask

if your venv is missing pip, install it first:
python -m ensurepip --default-pip

then (cmd works best)
.\Script\activate #activates the virtualenv
pip install -r requirements.txt

you will also need postges as a database to work with locally
You can set environment variables in a .env file in the root of the directory
/.env

`
export APP_SETTING="config.DevelopmentConfig"
export DATABASE_URL="postgresql://user:pass@localhost:5432/sensor"
export FLASK_APP="app"
`

add a new pyenv.cfg file to the datalogger folder with path and version info of your python interpreter
example below

`
home = C:\Users\msudo\AppData\Local\Microsoft\WindowsApps
include-system-site-packages = false
version = 3.10.9
`

Then create a database with the same name in pgAdmin owned by the user in the environment variable string
then

`flask run` or `python -m flask run`

should bring up the app, running the required database migrations

postman https://www.postman.com/downloads/ is a great way to test your local functionality
[POST] http://localhost:5000/api/data/jbriggs/add?string1=test&device_id=jb&key=1000&temperature=27.0
[GET]  http://localhost:5000/api/data/jbriggs/jb/test/1000

should create and then retrieve data

example, adding a column to the database
locally, adjust the model by adding to the table model, for example in
src/models/data.py

add some new columns
`
class Data(db.model):
  ...
  ...
  time_created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
  time_updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now(), server_default=db.func.now())
`

in cmd> `flask db migrate` #that will generate a migration file based on those changes in /migrations/version/<random#>/py

look at that file and edit it as necessary
in cmd> `flask db upgrade` applies your migrations to the local database

if you have the heroku-cli, upgrading the production database is
`heroku run flask db upgrade` provided you have permissions.

In general a best practice on db upgrades is
1 - migration to add new columns that don't affect existing code
2 - updates to code to not use the old columns anymore, instead using the new columns
3 - a migration to remove unused columns


To deploy changes to the EPS server, run the following:
1. install heroku and create a heroku account (you may need permissions to publish as well - see Mr. Briggs for this)
2. from command line run `heroku git:remote --app eps-datalogger`
3. then `git push heroku main`

output should look something like this:

`
C:\Users\msudo\GitHub\datalogger\src\data>git push heroku main
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 8 threads
Compressing objects: 100% (4/4), done.
Writing objects: 100% (5/5), 426 bytes | 106.00 KiB/s, done.
Total 5 (delta 3), reused 0 (delta 0), pack-reused 0
remote: Compressing source files... done.
remote: Building source:
remote:
remote: -----> Building on the Heroku-20 stack
remote: -----> Using buildpack: heroku/python
remote: -----> Python app detected
remote: -----> No Python version was specified. Using the same version as the last build: python-3.10.4
remote:        To use a different version, see: https://devcenter.heroku.com/articles/python-runtimes
remote: -----> No change in requirements detected, installing from cache
remote: -----> Using cached install of python-3.10.4
remote: -----> Installing pip 22.0.4, setuptools 60.10.0 and wheel 0.37.1
remote: -----> Installing SQLite3
remote: -----> Installing requirements with pip
remote: -----> Discovering process types
remote:        Procfile declares types -> web
remote:
remote: -----> Compressing...
remote:        Done: 65.9M
remote: -----> Launching...
remote:        Released v16
remote:        https://eps-datalogger.herokuapp.com/ deployed to Heroku
remote:
remote: Verifying deploy... done.
To https://git.heroku.com/eps-datalogger.git
   e9bf002..812ce7e  main -> main
`
