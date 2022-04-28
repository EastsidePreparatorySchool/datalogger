
from asyncio.windows_events import NULL
from src import db

class Data(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(255))
  key = db.Column(db.String(255))
  device_id = db.Column(db.String(255))
  area = db.Column(db.String(255))
  battery = db.Column(db.Float)
  light = db.Column(db.Float)
  water_level = db.Column(db.Float)
  humidity = db.Column(db.Float)
  temperature = db.Column(db.Float)
  motion = db.Column(db.Integer)
  sound = db.Column(db.Integer)
  vibration = db.Column(db.Integer)
  tilt = db.Column(db.Integer)
  string1  = db.Column(db.String(255))
  string2  = db.Column(db.String(255))
  float1 = db.Column(db.Float)
  float2 = db.Column(db.Float)
  int1 = db.Column(db.Integer)
  int2 = db.Column(db.Integer)
  
  def __init__(self, attrs):
    self.username = find_or_null(attrs, "username")
    self.key = find_or_null(attrs, "key")
    self.device_id = find_or_null(attrs, "device_id")
    self.area = find_or_null(attrs, "area")
    self.battery = find_or_null(attrs, "battery")
    self.light = find_or_null(attrs, "light")
    self.water_level = find_or_null(attrs, "water_level")
    self.humidity = find_or_null(attrs, "humidity")
    self.temperature = find_or_null(attrs, "temperature")
    self.motion = find_or_null(attrs, "motion")
    self.sound = find_or_null(attrs, "sound")
    self.vibration = find_or_null(attrs, "vibration")
    self.tilt = find_or_null(attrs, "tilt")
    self.string1 = find_or_null(attrs, "string1")
    self.string2 = find_or_null(attrs, "string2")
    self.float1 = find_or_null(attrs, "float1")
    self.float2 = find_or_null(attrs, "float2")
    self.int1 = find_or_null(attrs, "int1")
    self.int2 = find_or_null(attrs, "int2")

  def as_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}

  def columns():
    return [c.name for c in Data.__table__.columns]

def find_or_null(attrs, key):
  if key in attrs:
    return attrs[key]
  else:
    return None


#adding records
#rec = Data(attrs)
#db.session.add(rec)
#db.session.commit()

#retrieve
# Data.query.with_entities(Data.id,Data.device_id).all()