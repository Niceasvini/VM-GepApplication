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
        # Check if file exists and has content
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"File is empty: {file_path}")
        
        if file_type == 'pdf':
            text = extract_text_from_pdf(file_path)
        elif file_type == 'docx':
            text = extract_text_from_docx(file_path)
        elif file_type == 'txt':
            text = extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Validate extracted text
        if not text or len(text.strip()) < 10:
            raise ValueError(f"Extracted text is too short or empty: {len(text)} characters")
        
        # Log extraction details
        logging.info(f"Extracted text length: {len(text)}")
        logging.info(f"First 500 characters: {text[:500]}")
        
        return text
        
    except Exception as e:
        logging.error(f"Error extracting text from {file_path}: {e}")
        raise

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            
            # Check if PDF has pages
            if len(pdf_reader.pages) == 0:
                raise ValueError("PDF file has no pages")
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Check if any text was extracted
            if not text.strip():
                raise ValueError("No text could be extracted from PDF (possibly scanned document)")
                
    except Exception as e:
        logging.error(f"Error reading PDF {file_path}: {e}")
        raise
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = Document(file_path)
        
        # Check if document has paragraphs
        if len(doc.paragraphs) == 0:
            raise ValueError("DOCX file has no content")
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        # Check if any text was extracted
        if not text.strip():
            raise ValueError("No text could be extracted from DOCX file")
            
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
        
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        filename = os.path.basename(file_path)
        return filename.rsplit('.', 1)[0], None, None
        
    except ValueError as e:
        logging.error(f"File validation error for {file_path}: {e}")
        filename = os.path.basename(file_path)
        return filename.rsplit('.', 1)[0], None, None
        
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
