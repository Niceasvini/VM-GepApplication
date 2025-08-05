from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='recruiter')  # 'recruiter' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    created_jobs = db.relationship('Job', backref='creator', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'closed', 'draft'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    candidates = db.relationship('Candidate', backref='job', lazy=True, cascade='all, delete-orphan')

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    
    # AI Analysis Results
    ai_score = db.Column(db.Float)  # 0.0 to 10.0
    ai_summary = db.Column(db.Text)
    ai_analysis = db.Column(db.Text)
    extracted_skills = db.Column(db.Text)  # JSON string of skills
    
    # Status Management
    status = db.Column(db.String(20), default='pending')  # 'pending', 'analyzing', 'analyzed', 'interested', 'rejected'
    analysis_status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyzed_at = db.Column(db.DateTime)
    
    # Foreign Keys
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    
    def get_skills_list(self):
        if self.extracted_skills:
            import json
            try:
                return json.loads(self.extracted_skills)
            except:
                return []
        return []
    
    def set_skills_list(self, skills_list):
        import json
        self.extracted_skills = json.dumps(skills_list)

class CandidateComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    candidate = db.relationship('Candidate', backref='comments')
    user = db.relationship('User', backref='comments')
