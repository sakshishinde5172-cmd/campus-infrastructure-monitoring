import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
 
load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, redirect, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from email_utils import send_status_email, send_admin_new_complaint
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
 
app = Flask(__name__, static_folder=FRONTEND_DIR, template_folder=FRONTEND_DIR)
app.secret_key = 'campus_monitoring_secret_key'
CORS(app)
 
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
 
# SQLite Database Setup
DB_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DB_DIR, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(DB_DIR, 'campus.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
 
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db = SQLAlchemy(app)

USERNAME_REGEX = re.compile(r'^[A-Za-z]{3,30}$')
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
CONSONANT_CLUSTER_REGEX = re.compile(r'[^aeiouAEIOU]{4,}')

def is_realistic_username(username):
    if CONSONANT_CLUSTER_REGEX.search(username):
        return False
    return True
 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
 
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
 
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Pending')
    photo_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
 
    def to_dict(self):
        owner = User.query.get(self.owner_id) if self.owner_id else None
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'priority': self.priority,
            'status': self.status,
            'photo_url': f'/uploads/{self.photo_filename}' if self.photo_filename else None,
            'created_at': (self.created_at.isoformat() + 'Z') if self.created_at else None,
            'owner_id': self.owner_id,
            'resolved_at': (self.resolved_at.isoformat() + 'Z') if self.resolved_at else None,
            'owner_username': owner.username if owner else 'System/Pre-migrated'
        }
 
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        head_user = User(username='admin', is_admin=True)
        head_user.set_password('admin123')
        db.session.add(head_user)
        db.session.commit()
        print(">>> Default Head Admin account created: admin / admin123")
 
@app.route('/')
def home():
    return send_from_directory(FRONTEND_DIR, 'home.html')
 
@app.route('/login')
def login_page():
    return send_from_directory(FRONTEND_DIR, 'login.html')
 
@app.route('/register')
def register_page():
    return send_from_directory(FRONTEND_DIR, 'register.html')
 
@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect('/login')
    return send_from_directory(FRONTEND_DIR, 'index.html')
 
@app.route('/dashboard/report')
def dashboard_report_page():
    if 'user_id' not in session:
        return redirect('/login?next=/dashboard/report')
    return send_from_directory(FRONTEND_DIR, 'report.html')
 
@app.route('/dashboard/complaints')
def dashboard_complaints_page():
    if 'user_id' not in session:
        return redirect('/login?next=/dashboard/complaints')
    return send_from_directory(FRONTEND_DIR, 'complaints.html')
 
@app.route('/dashboard/analytics')
def dashboard_analytics_page():
    if 'user_id' not in session:
        return redirect('/login?next=/dashboard/analytics')
    return send_from_directory(FRONTEND_DIR, 'analytics.html')
  
@app.route('/admin')
def admin_page():
    if 'user_id' not in session:
        return redirect('/login?next=/admin')
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return redirect('/dashboard')
    return send_from_directory(FRONTEND_DIR, 'admin.html')
 
@app.route('/report')
def report_route():
    location = request.args.get('location', '')
    if 'user_id' not in session:
        return redirect(f'/login?next=/report?location={location}')
    return redirect(f'/dashboard/report?location={location}')
 
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)
 
@app.route('/logo.png')
def serve_logo():
    return send_from_directory(FRONTEND_DIR, 'logo.png')
 
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
 
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email and password are required.'}), 400

    if not USERNAME_REGEX.match(username):
        return jsonify({'error': 'Username must contain only letters (3-30 characters), no numbers or symbols.'}), 400

    if not is_realistic_username(username):
        return jsonify({'error': 'Please enter a valid, realistic username.'}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long.'}), 400

    if confirm_password and password != confirm_password:
        return jsonify({'error': 'Passwords do not match.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'This username is already taken.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists.'}), 400

    new_user = User(username=username, email=email, is_admin=False)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration successful'}), 201
 
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Invalid username/email or password.'}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({'message': 'Login successful', 'is_admin': user.is_admin})
    return jsonify({'error': 'Invalid username/email or password.'}), 401
 
@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})
 
@app.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'username': user.username, 'is_admin': user.is_admin})
 
def get_ai_priority(title, description):
    try:
        model = genai.GenerativeModel('gemini-3.6-flash')
        prompt = f"""You are a campus facilities triage assistant. Based on the complaint title and description below, classify its priority as exactly one word: Low, Medium, or High.
 
High = safety hazards, electrical/fire risks, water leakage causing damage, broken security/access systems, anything urgent or dangerous.
Medium = functional issues that inconvenience people but aren't urgent (broken furniture, AC issues, minor equipment problems).
Low = cosmetic or non-urgent issues (cleaning, painting, minor cosmetic damage).
 
Title: {title}
Description: {description}
 
Respond with ONLY one word: Low, Medium, or High."""
        response = model.generate_content(prompt)
        result = response.text.strip()
        if result in ['Low', 'Medium', 'High']:
            return result
        return 'Medium'
    except Exception as e:
        print(f"AI priority error: {e}")
        return 'Medium'
 
@app.route('/api/complaints', methods=['GET', 'POST'])
def handle_complaints():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
 
    user = User.query.get(session['user_id'])
 
    if request.method == 'GET':
        if user.is_admin:
            complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
        else:
            complaints = Complaint.query.filter_by(owner_id=user.id).order_by(Complaint.created_at.desc()).all()
        return jsonify([c.to_dict() for c in complaints])
 
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        priority = get_ai_priority(title, description)
 
        if not title or not location:
            return jsonify({'error': 'Title and location are required'}), 400
 
        photo_filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '':
                ext = os.path.splitext(file.filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    filename = secure_filename(f"{int(datetime.utcnow().timestamp())}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    photo_filename = filename
 
        new_complaint = Complaint(
            title=title,
            description=description,
            location=location,
            priority=priority,
            photo_filename=photo_filename,
            owner_id=user.id
        )
        db.session.add(new_complaint)
        db.session.commit()
        send_admin_new_complaint(new_complaint.id, new_complaint.title, new_complaint.location, user.username)
        return jsonify(new_complaint.to_dict()), 201
 
@app.route('/api/analytics')
def api_analytics():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
 
    user = User.query.get(session['user_id'])
 
    if user.is_admin:
        complaints = Complaint.query.all()
    else:
        complaints = Complaint.query.filter_by(owner_id=user.id).all()
 
    by_priority = {}
    by_status = {}
    for c in complaints:
        by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
        by_status[c.status] = by_status.get(c.status, 0) + 1
 
    times = [(c.resolved_at - c.created_at).total_seconds() for c in complaints if c.status == 'Resolved' and c.resolved_at and c.created_at]
    avg_days = round(sum(times) / len(times) / 86400, 1) if times else None
    return jsonify({
        'avg_resolution_days': avg_days,
        'resolved_count': len(times),
        'total': len(complaints),
        'by_priority': by_priority,
                'by_status': by_status
    })
 
@app.route('/api/overdue-complaints')
def overdue_complaints():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 401
 
    cutoff = datetime.utcnow() - timedelta(days=6)
    overdue = Complaint.query.filter(
        Complaint.status != 'Resolved',
        Complaint.created_at <= cutoff
    ).order_by(Complaint.created_at.asc()).all()
 
    return jsonify({
        'count': len(overdue),
        'complaints': [c.to_dict() for c in overdue]
    })
 
@app.route('/api/complaints/<int:cid>', methods=['PUT', 'DELETE'])
def complaint_detail(cid):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
 
    user = User.query.get(session['user_id'])
    complaint = Complaint.query.get_or_404(cid)
 
    if request.method == 'PUT':
        if not user.is_admin and complaint.owner_id != user.id:
            return jsonify({'error': 'Permission denied'}), 403
 
        data = request.json or {}
        old_status = complaint.status
        if 'status' in data:
            complaint.status = data['status']
            if complaint.status == 'Resolved' and old_status != 'Resolved':
                complaint.resolved_at = datetime.utcnow()
            elif complaint.status != 'Resolved':
                complaint.resolved_at = None
        db.session.commit()
        if complaint.status != old_status:
            owner = User.query.get(complaint.owner_id)
            if owner and owner.email:
                send_status_email(owner.email, owner.username, complaint.id, complaint.title, complaint.status)
        return jsonify(complaint.to_dict())
 
    if request.method == 'DELETE':
        if not user.is_admin and complaint.owner_id != user.id:
            return jsonify({'error': 'Permission denied'}), 403
 
        if complaint.photo_filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], complaint.photo_filename)
            if os.path.exists(path):
                os.remove(path)
        db.session.delete(complaint)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'})
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
