# datalogger
A web API to ingest and report back IoT data for the Topics in CS course


TO activate the virtual environment run Scripts\activate from the root

Requirement: install flask
pip install flask

to setup db
from python shell
>>> from datalogger import db
>>> db.create_all()