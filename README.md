# datalogger
A web API to ingest and report back IoT data for the Topics in CS course


TO activate the virtual environment run Scripts\activate from the root

Requirement: install flask
pip install flask

then
.\Script\activate #activates the virtualenv
pip install flask_sqlalchemy
pip install flask_migrate
pip install psycopg2

you will also need postges as a database to work with locally
set envi variable
cmd> set DATABASE_URL=postgresql://[user[:password]@][netloc][:port][/dbname]
ps> $env:DATABASE_URL="postgresql://[user[:password]@][netloc][:port][/dbname]"

Then create a database with the same name in pgAdmin owned by the user in the environment variable string
then

`flask run`

should bring up the app, running the required database migrations

postman https://www.postman.com/downloads/ is a great way to test your local functionality
[POST] http://localhost:5000/api/data/jbriggs/add?string1=test&device_id=jb&key=1000&temperature=27.0
[GET]  http://localhost:5000/api/data/jbriggs/jb/1000

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
