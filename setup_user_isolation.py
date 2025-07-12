#!/usr/bin/env python3
"""
Setup script for user isolation system
Creates database tables and initial admin user
"""

import os
from app import app, db
from models import User, Job, Candidate, CandidateComment
from datetime import datetime

def create_tables():
    """Create all database tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully")

def create_admin_user():
    """Create default admin user"""
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("✓ Admin user already exists")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@vianaemoura.com',
            role='admin'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created (username: admin, password: admin123)")

def setup_user_isolation():
    """Complete setup for user isolation system"""
    print("=== Setting up User Isolation System ===")
    
    # Create tables
    create_tables()
    
    # Create admin user
    create_admin_user()
    
    print("\n=== Setup Complete ===")
    print("Your platform now has complete user account isolation:")
    print("• Each user can only see their own jobs and candidates")
    print("• Admin users can see all data across the platform")
    print("• All routes are protected with proper access control")
    print("\nLogin credentials:")
    print("• Admin: admin / admin123")
    print("\nCreate additional users through the registration page.")

if __name__ == '__main__':
    setup_user_isolation()