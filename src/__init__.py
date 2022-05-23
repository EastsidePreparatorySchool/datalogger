"""Initialize Flask app."""
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
# import json
# Database setup
#https://www.javatpoint.com/first-flask-application


db = SQLAlchemy()

def init_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    

    app.config.from_object('src.config.Config')  # configure app using the Config class defined in src/config.py

    db.init_app(app)  # initialise the database for the app

    with app.app_context():
        from src.models.data import Data  # this import allows us to create the table if it does not exist
        try:
          db.create_all()
        except Exception as error:
          print(f'tables likely already created {error}')  

        from src.data.routes import bp as routes
        app.register_blueprint(routes)

        return app