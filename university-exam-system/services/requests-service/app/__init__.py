from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Initialize the database instance
db = SQLAlchemy()

def create_app():
    # Create the Flask app instance
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    # Configure the app with the database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://request_user:requestpass@db/requests_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the db with the app
    db.init_app(app)

    # Import the models after initializing the app and db
    from app.models.models import User, Event, RSVP, Share
    from app.models.request import Request

    # Initialize routes here, if necessary
    # from app import routes
    
    return app
