#!/usr/bin/env python3
"""
Setup all required tables in Supabase
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import User, Job, Candidate, CandidateComment
from werkzeug.security import generate_password_hash

def setup_tables():
    """Create all required tables"""
    with app.app_context():
        print("Setting up Supabase tables...")
        
        # Drop existing tables if they exist (clean start)
        db.drop_all()
        print("✓ Dropped existing tables")
        
        # Create all tables
        db.create_all()
        print("✓ Created all tables")
        
        # Check what tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Created tables: {tables}")
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@vianamoura.com',
            role='admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("✓ Created admin user (admin/admin123)")
        
        # Create test job
        test_job = Job(
            title='Desenvolvedor Python',
            description='Desenvolvedor Python com experiência em Flask e análise de dados',
            requirements='Python, Flask, SQL, Git, APIs REST',
            dcf_content='Desenvolvimento de aplicações web com foco em análise de dados',
            created_by=admin_user.id
        )
        db.session.add(test_job)
        db.session.commit()
        print("✓ Created test job")
        
        # Create another test job
        test_job2 = Job(
            title='Assistente de Dados',
            description='Assistente para análise de dados e relatórios',
            requirements='Python, SQL, Excel, Power BI',
            dcf_content='Análise de dados e criação de relatórios',
            created_by=admin_user.id
        )
        db.session.add(test_job2)
        db.session.commit()
        print("✓ Created second test job")
        
        print("\n=== TABELAS CONFIGURADAS COM SUCESSO ===")
        print(f"Users: {User.query.count()}")
        print(f"Jobs: {Job.query.count()}")
        print(f"Candidates: {Candidate.query.count()}")
        
        return True

if __name__ == "__main__":
    setup_tables()