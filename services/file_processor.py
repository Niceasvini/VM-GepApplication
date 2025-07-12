import os
import re
import logging
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_file(file_path, file_type):
    """
    Extract text content from uploaded files
    Supports PDF, DOCX, and TXT formats
    """
    try:
        if file_type == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_type == 'docx':
            return extract_text_from_docx(file_path)
        elif file_type == 'txt':
            return extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {e}")
        return ""

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        logging.error(f"Error reading PDF {file_path}: {e}")
        raise
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        logging.error(f"Error reading DOCX {file_path}: {e}")
        raise
    return text

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error reading TXT {file_path}: {e}")
        raise

def process_uploaded_file(file_path, file_type):
    """
    Process uploaded file and extract basic candidate information
    Returns: (name, email, phone)
    """
    try:
        text = extract_text_from_file(file_path, file_type)
        
        # Extract basic information using regex
        name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        
        return name, email, phone
        
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        # Return filename as name if processing fails
        filename = os.path.basename(file_path)
        return filename.rsplit('.', 1)[0], None, None

def extract_name(text):
    """Extract candidate name from resume text"""
    lines = text.split('\n')
    
    # Try to find name in first few lines
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if line and len(line) > 3:
            # Check if line looks like a name (contains only letters and spaces)
            if re.match(r'^[A-Za-zÀ-ÿ\s]+$', line) and len(line.split()) >= 2:
                return line.title()
    
    # If no name found, try to extract from common patterns
    name_patterns = [
        r'Nome:\s*([A-Za-zÀ-ÿ\s]+)',
        r'Name:\s*([A-Za-zÀ-ÿ\s]+)',
        r'^([A-Za-zÀ-ÿ\s]+)$'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip().title()
    
    return "Nome não identificado"

def extract_email(text):
    """Extract email from resume text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def extract_phone(text):
    """Extract phone number from resume text"""
    # Brazilian phone patterns
    phone_patterns = [
        r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',  # (11) 99999-9999 or 11 99999-9999
        r'\+55\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}',  # +55 (11) 99999-9999
        r'\d{10,11}',  # 11999999999
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    
    return None

def get_file_size(file_path):
    """Get file size in bytes"""
    return os.path.getsize(file_path)

def validate_file_type(filename):
    """Validate if file type is supported"""
    allowed_extensions = {'pdf', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
