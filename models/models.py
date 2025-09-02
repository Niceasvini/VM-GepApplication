from datetime import datetime
from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = {'schema': 'appcurriculos'}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='recruiter')  # 'recruiter' or 'admin'
    is_active = db.Column(db.Boolean, default=True)  # Usuário ativo/inativo
    last_login = db.Column(db.DateTime)  # Último login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Permissões granulares
    can_create_jobs = db.Column(db.Boolean, default=True)
    can_edit_jobs = db.Column(db.Boolean, default=True)
    can_delete_jobs = db.Column(db.Boolean, default=True)
    can_upload_candidates = db.Column(db.Boolean, default=True)
    can_process_ai = db.Column(db.Boolean, default=True)
    can_edit_candidates = db.Column(db.Boolean, default=True)
    can_view_statistics = db.Column(db.Boolean, default=True)
    can_create_users = db.Column(db.Boolean, default=False)  # Apenas admins
    
    # Relationships
    created_jobs = db.relationship('Job', backref='creator', lazy=True)
    activities = db.relationship('UserActivity', backref='user_ref', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def has_permission(self, permission):
        """Verifica se o usuário tem uma permissão específica"""
        if self.role == 'admin':
            return True
        return getattr(self, permission, False)
    
    def can_access_feature(self, feature):
        """Verifica se o usuário pode acessar uma funcionalidade"""
        permission_map = {
            'create_jobs': 'can_create_jobs',
            'edit_jobs': 'can_edit_jobs',
            'delete_jobs': 'can_delete_jobs',
            'upload_candidates': 'can_upload_candidates',
            'process_ai': 'can_process_ai',
            'edit_candidates': 'can_edit_candidates',
            'view_statistics': 'can_view_statistics',
            'create_users': 'can_create_users'
        }
        return self.has_permission(permission_map.get(feature, False))
    
    def update_last_login(self):
        """Atualiza o timestamp do último login"""
        from datetime import datetime
        self.last_login = datetime.utcnow()
        db.session.commit()

class Job(db.Model):
    __tablename__ = 'job'
    __table_args__ = {'schema': 'appcurriculos'}
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'closed', 'draft'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    created_by = db.Column(db.Integer, db.ForeignKey('appcurriculos.user.id'), nullable=False)
    
    # Relationships
    candidates = db.relationship('Candidate', backref='job', lazy=True, cascade='all, delete-orphan')

class Candidate(db.Model):
    __tablename__ = 'candidate'
    __table_args__ = {'schema': 'appcurriculos'}
    
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
    
    # Extracted Information
    extracted_metadata = db.Column(db.Text)  # JSON string with additional extracted info
    
    # Status Management
    status = db.Column(db.String(20), default='pending')  # 'pending', 'analyzing', 'analyzed', 'interested', 'rejected'
    analysis_status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyzed_at = db.Column(db.DateTime)
    
    # Foreign Keys
    job_id = db.Column(db.Integer, db.ForeignKey('appcurriculos.job.id'), nullable=False)
    
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
    __tablename__ = 'candidate_comment'
    __table_args__ = {'schema': 'appcurriculos'}
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    candidate_id = db.Column(db.Integer, db.ForeignKey('appcurriculos.candidate.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('appcurriculos.user.id'), nullable=False)
    
    # Relationships
    candidate = db.relationship('Candidate', backref='comments')
    user = db.relationship('User', backref='comments')


class UserActivity(db.Model):
    __tablename__ = 'user_activity'
    __table_args__ = {'schema': 'appcurriculos'}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('appcurriculos.user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'login', 'create_job', 'upload_candidate', etc.
    details = db.Column(db.Text)  # Detalhes adicionais da ação
    ip_address = db.Column(db.String(45))  # Endereço IP do usuário
    user_agent = db.Column(db.String(500))  # User agent do navegador
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')
    
    def __repr__(self):
        return f'<UserActivity {self.user.username}: {self.action}>'
