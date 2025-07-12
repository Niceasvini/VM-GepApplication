# Viana e Moura - Recruitment System

## Overview

This is a Flask-based recruitment platform that uses AI to automatically analyze resumes and match candidates to job positions. The system provides intelligent candidate scoring, automated analysis, and streamlined recruitment workflow management.

## User Preferences

Preferred communication style: Simple, everyday language.

## Security & Access Control

**User Account Isolation System (Implemented July 2025)**
- Each user account has complete data isolation
- Users can only see and interact with their own jobs and candidates
- Admin users have access to all data across the platform
- All routes protected with proper access control checks
- Multi-tenancy architecture prevents data leakage between accounts

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL via Supabase
- **ORM**: SQLAlchemy with Flask-SQLAlchemy
- **Authentication**: Flask-Login for session management
- **File Processing**: PyPDF2 for PDFs, python-docx for Word documents

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5.3.0
- **JavaScript**: Vanilla JavaScript with Chart.js for visualizations
- **Icons**: Font Awesome 6.0
- **Styling**: Custom CSS with modern design variables

### AI Integration
- **AI Provider**: DeepSeek API (OpenAI-compatible)
- **Analysis Engine**: Custom AI service for resume analysis and scoring
- **Caching**: File-based caching system to prevent redundant AI calls

## Key Components

### Models (Database Schema)
- **User**: Authentication and role management (admin/recruiter) with account isolation
- **Job**: Job postings with descriptions, requirements, and DCF content (linked to creator)
- **Candidate**: Resume storage with AI analysis results (access controlled by job owner)
- **CandidateComment**: Comments and notes on candidates (access controlled by job owner)

### Services
- **AI Service**: Handles resume analysis, scoring, and candidate matching
- **File Processor**: Extracts text from PDF, DOCX, and TXT files
- **Cache Service**: Prevents duplicate AI analysis calls

### Processing Systems
- **Parallel Processing**: Multiple concurrent AI analysis processors
- **Batch Upload**: Handles bulk resume uploads
- **Background Processing**: Asynchronous candidate analysis

## Data Flow

1. **Job Creation**: Recruiters create job postings with requirements
2. **Resume Upload**: Individual or bulk upload of candidate resumes
3. **Text Extraction**: System extracts text from various file formats
4. **AI Analysis**: DeepSeek API analyzes resumes against job requirements
5. **Scoring**: AI generates numerical scores (0-10) and detailed analysis
6. **Caching**: Results are cached to avoid redundant API calls
7. **Review**: Recruiters review candidates and make decisions

## External Dependencies

### Database
- **Supabase**: PostgreSQL hosting with connection pooling
- **Connection**: Direct PostgreSQL connection string

### AI Services
- **DeepSeek API**: Primary AI provider for resume analysis
- **OpenAI SDK**: Used for API communication (compatible with DeepSeek)

### File Processing
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing
- **Werkzeug**: File upload handling and security

### Frontend Libraries
- **Bootstrap 5.3.0**: UI framework
- **Font Awesome 6.0**: Icon library
- **Chart.js**: Data visualization

## Deployment Strategy

### Environment Configuration
- Environment variables for database URL and API keys
- Session secrets for Flask security
- File upload limits and directory configuration

### Database Setup
- Automated table creation via SQLAlchemy
- Default admin user creation
- Connection pooling for performance

### File Storage
- Local file system storage in 'uploads' directory
- Secure filename handling
- File type validation (PDF, DOCX, TXT)

### Processing Architecture
- Multiple processor implementations for scalability
- Error handling and retry mechanisms
- Real-time progress monitoring

### Security Features
- CORS headers configuration
- Secure file upload handling
- Password hashing with Werkzeug
- User role-based access control
- **Complete data isolation between user accounts**
- **Admin-only access to all data**
- **Protected API endpoints with access control**
- **Multi-tenant architecture with security checks**

## Notes

- The system uses a custom design with Viana e Moura branding
- AI analysis includes detailed scoring with explanations
- Caching system prevents redundant API calls and reduces costs
- Multiple processing strategies available for different performance needs
- The platform supports both individual and bulk candidate processing

## Documentation

### README.md
A comprehensive README file has been created with complete project documentation including:
- **Project Overview**: Detailed description of features and capabilities
- **Technology Stack**: Complete list of technologies and their versions
- **Installation Guide**: Step-by-step setup instructions
- **Usage Instructions**: How to use all features
- **API Documentation**: Format of AI analysis responses
- **Deployment Guide**: Instructions for various platforms
- **Contributing Guidelines**: How to contribute to the project
- **Security Information**: Authentication and data protection details