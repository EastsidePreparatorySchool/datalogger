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


