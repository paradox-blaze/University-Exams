from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # Import the db instance from app

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # 🔐 hashed password
    role = db.Column(db.String(10))  # 'admin' or 'student'

    # 🔒 Set password using hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # 🔓 Verify password against hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Event Model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))


# RSVP Model
class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))


# Share Model
class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))


# Request Model (This model represents a request made by a user)
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ✅ this is correct

    status = db.Column(db.String(10), default='pending')  # 'approved', 'denied', 'pending'
    admin_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
