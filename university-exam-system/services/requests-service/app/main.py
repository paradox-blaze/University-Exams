from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///requests.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# 📦 Request Model
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    requested_by = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="pending")
    admin_comment = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 🏠 Root Route
@app.route('/')
def index():
    return '📝 Simple Request System is running!'

# 📥 Submit a new request
@app.route('/requests', methods=['POST'])
def submit_request():
    data = request.get_json()

    required_fields = ['title', 'description', 'category', 'requested_by']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400

    new_request = Request(
        title=data['title'],
        description=data['description'],
        category=data['category'],
        requested_by=data['requested_by']
    )
    db.session.add(new_request)
    db.session.commit()
    return jsonify({'message': 'Request submitted successfully!'}), 201

# 📃 Get all requests
@app.route('/requests', methods=['GET'])
def get_all_requests():
    requests = Request.query.order_by(Request.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'category': r.category,
        'status': r.status,
        'admin_comment': r.admin_comment,
        'requested_by': r.requested_by,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for r in requests]), 200

# 📋 Get requests by user
@app.route('/requests/<requested_by>', methods=['GET'])
def get_requests_by_user(requested_by):
    user_requests = Request.query.filter_by(requested_by=requested_by).order_by(Request.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'category': r.category,
        'status': r.status,
        'admin_comment': r.admin_comment,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for r in user_requests]), 200

# ✅ Admin updates request status
@app.route('/requests/<int:request_id>', methods=['PUT'])
def update_request_status(request_id):
    data = request.get_json()
    status = data.get('status')
    comment = data.get('admin_comment')

    if status not in ['approved', 'denied']:
        return jsonify({'error': 'Status must be "approved" or "denied"'}), 400

    req = Request.query.get_or_404(request_id)
    req.status = status
    req.admin_comment = comment
    db.session.commit()

    return jsonify({'message': f'Request {status} successfully'}), 200

# 🧱 Create DB
with app.app_context():
    db.create_all()

    if not Request.query.first():
        dummy_requests = [
            Request(
                title="Leave for Family Function",
                description="Need 2 days leave for a family function.",
                category="Leave",
                requested_by="student1"
            ),
            Request(
                title="Participation in Hackathon",
                description="Permission to attend a 24hr hackathon.",
                category="Event",
                requested_by="student3"
            ),
            Request(
                title="Library Access Extension",
                description="Requesting access to the library till 10 PM.",
                category="Facility",
                requested_by="student4"
            ),
            Request(
                title="Medical Leave",
                description="Feeling unwell, requesting 3-day medical leave.",
                category="Leave",
                requested_by="student3"
            ),
            Request(
                title="Attend External Seminar",
                description="Request to attend an off-campus AI seminar.",
                category="Event",
                requested_by="student4"
            )
        ]

        db.session.add_all(dummy_requests)
        db.session.commit()

# 🚀 Start the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
