# Viana e Moura - Recrutamento Inteligente

## Overview

This is a professional web application for automated resume analysis using artificial intelligence. The system allows recruiters to create job postings, upload candidate resumes, and get AI-powered compatibility scores and analysis to streamline the recruitment process.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (July 2025)

- **Removed word limit restrictions**: Eliminated "máximo 100 palavras" from all AI analysis processors
- **Enhanced AI analysis prompts**: Updated to generate detailed technical summaries instead of limited responses
- **Improved analysis structure**: Removed formatting marks (---, ##, ###) from analysis output
- **Increased token limits**: Enhanced to 900 tokens for more comprehensive analysis
- **Specific analysis requirements**: AI now cites specific companies, technologies, and experiences instead of generic responses
- **Better resume processing**: Increased text extraction to 3000-5000 characters for fuller context
- **Detailed error handling**: Added comprehensive error description system for failed analyses
- **Improved error display**: Updated HTML templates to show specific error messages instead of generic failures
- **Reprocessing functionality**: Added "Try Again" button and API endpoint for failed candidate reprocessing
- **Outdated analysis detection**: Replaced generic template analysis with reprocessing prompts for better AI output

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL (configurable via DATABASE_URL)
- **Authentication**: Flask-Login for session management
- **AI Integration**: OpenAI GPT-4o for resume analysis
- **File Processing**: Support for PDF, DOCX, and TXT resume formats

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **CSS Framework**: Bootstrap 5.3.0 with custom styling
- **JavaScript**: Vanilla JS with Chart.js for analytics
- **Icons**: Font Awesome 6.0.0
- **Responsive Design**: Mobile-first approach

### Database Schema
- **Users**: Authentication, roles (recruiter/admin)
- **Jobs**: Job postings with descriptions, requirements, and DCF content
- **Candidates**: Resume data with AI analysis results
- **Comments**: Candidate evaluation comments (referenced but not fully implemented)

## Key Components

### Authentication System
- User registration and login
- Role-based access control (recruiter/admin)
- Session management with Flask-Login

### Job Management
- Create, edit, and manage job postings
- Support for detailed job descriptions and requirements
- DCF (Documento de Conteúdo Funcional) integration

### File Processing
- Multi-format resume upload (PDF, DOCX, TXT)
- Text extraction from various file formats
- Secure file storage in uploads directory

### AI Analysis Engine
- OpenAI GPT-4o integration for resume analysis
- Scoring system (0-10 scale, 0.5 increments)
- Detailed analysis including strengths, weaknesses, and recommendations
- Skills extraction and experience level assessment

### Dashboard and Analytics
- Real-time statistics and metrics
- Visual charts and graphs
- Candidate ranking and filtering

## Data Flow

1. **Job Creation**: Recruiters create job postings with detailed requirements
2. **Resume Upload**: Multiple resumes can be uploaded per job
3. **Text Extraction**: System extracts text from various file formats
4. **AI Analysis**: OpenAI processes resume against job requirements
5. **Scoring**: AI generates compatibility scores and detailed analysis
6. **Review**: Recruiters review ranked candidates and make decisions

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o model for resume analysis
- **API Key**: Required via OPENAI_API_KEY environment variable

### File Processing Libraries
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX document processing
- **Built-in**: TXT file handling

### Frontend Libraries
- **Bootstrap 5.3.0**: UI framework
- **Font Awesome 6.0.0**: Icon library
- **Chart.js**: Data visualization

## Deployment Strategy

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API authentication
- `SESSION_SECRET`: Flask session encryption key

### Configuration
- Database connection pooling with recycle and pre-ping
- 16MB file upload limit
- Uploads directory auto-creation
- ProxyFix for proper HTTPS handling

### Security Features
- Password hashing with Werkzeug
- File type validation
- Secure filename handling
- Role-based access control

## Key Features

### Multi-language Support
- Portuguese-language interface
- Localized error messages and UI text

### Professional Design
- Clean, modern interface with custom branding
- Responsive layout for all devices
- Professional color scheme (blues, grays, whites)

### Analytics and Reporting
- Dashboard with key metrics
- Candidate ranking by AI scores
- Status tracking and filtering
- Visual data representation

### File Management
- Support for multiple file formats
- Secure file storage and retrieval
- File metadata tracking

The application follows a traditional MVC pattern with Flask, using SQLAlchemy for data persistence and integrating modern AI capabilities for intelligent recruitment processing.