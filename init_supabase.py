#!/usr/bin/env python3
"""
Initialize Supabase database with proper configuration
"""
import os
import sys
from dotenv import load_dotenv

# Force load environment variables
load_dotenv(override=True)

# Set DATABASE_URL explicitly
DATABASE_URL = "postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
os.environ['DATABASE_URL'] = DATABASE_URL

# Import after setting environment
from app import app, db
from models import User, Job, Candidate
from werkzeug.security import generate_password_hash

def init_supabase():
    """Initialize Supabase database"""
    try:
        with app.app_context():
            # Test connection
            print("Testing Supabase connection...")
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            print("✓ Supabase connection successful!")
            
            # Create tables
            print("Creating tables...")
            db.create_all()
            print("✓ Tables created successfully!")
            
            # Create admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@vianamoura.com',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Admin user created!")
            
            # Create test job
            test_job = Job.query.filter_by(title='Desenvolvedor Python').first()
            if not test_job:
                test_job = Job(
                    title='Desenvolvedor Python',
                    description='Desenvolvedor Python com experiência em Flask e análise de dados',
                    requirements='Python, Flask, SQL, Git, APIs REST',
                    dcf_content='Desenvolvimento de aplicações web e análise de dados',
                    created_by=admin_user.id
                )
                db.session.add(test_job)
                db.session.commit()
                print("✓ Test job created!")
            
            # Show stats
            user_count = User.query.count()
            job_count = Job.query.count()
            candidate_count = Candidate.query.count()
            
            print(f"\n✓ Database initialized successfully!")
            print(f"  - Users: {user_count}")
            print(f"  - Jobs: {job_count}")
            print(f"  - Candidates: {candidate_count}")
            
            return True
            
    except Exception as e:
        print(f"✗ Error initializing Supabase: {e}")
        return False

if __name__ == "__main__":
    success = init_supabase()
    sys.exit(0 if success else 1)