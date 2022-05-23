from asyncio.subprocess import STDOUT
from flask import Blueprint, render_template, request
from src.models.data import Data
from src import db
import json

#return render_template('users.html', users=users)

bp = Blueprint('data', __name__)

@bp.route("/")
def home():
  return "helloflask";

@bp.route("/test/<reflect>")
def test(reflect):
    return "hello" + reflect;

@bp.route("/api/data/<username>/add", methods = ['POST'])
def data_add(username):
    # name = request.form
    # https://python-adv-web-apps.readthedocs.io/en/latest/flask_db3.html#:~:text=To%20add%20a%20new%20record%20to%20the%20database,were%20introduced%20in%20the%20chapter%20Flask%3A%20Web%20Forms.
    # Below handles form insert or falls back to param style insert
    params = form_or_args(request)
    record = Data(params)
    record.username = username #force username
    db.session.add(record)
    db.session.commit()
    return json.dumps(record.as_dict())  #({"status": "ok", "record_id": record.id})

@bp.route("/api/data/<username>/<device>")
def device_data(username,device):
    records = Data.query.filter_by(username=username, device_id=device, key=None).all()
    
    return json.dumps([r.as_dict() for r in records])

@bp.route("/api/data/<username>/<device>/<key>")
def device_data_and_key(username, device, key):
    records = Data.query.filter_by(username=username, device_id=device, key=key).all()
    return json.dumps([r.as_dict() for r in records])

@bp.route("/auth/callback")
def auth_callback():
    params = form_or_args(request)
    print(params)
    return json.dumps(params)
    
def form_or_args(request):
    if request.form:
        params = request.form
    elif request.data:
        params = request.data
    else:
        params = request.args
    return params


    # http_post('https://eps-datalogger.herokuapp.com', [('device_id', 'huzzah1')])