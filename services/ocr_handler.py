import io
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document
from PIL import Image
import pytesseract


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from PDF, DOCX, or TXT files.
    Falls back to OCR for scanned PDFs if needed.
    """
    extension = filename.lower().split('.')[-1]
    
    try:
        if extension == 'pdf':
            return extract_from_pdf(file_bytes)
        elif extension in ['docx', 'doc']:
            return extract_from_docx(file_bytes)
        elif extension == 'txt':
            return file_bytes.decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    except Exception as e:
        raise Exception(f"Error extracting text from {filename}: {str(e)}")


def extract_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfminer.six"""
    try:
        text = pdf_extract_text(io.BytesIO(file_bytes))
        
        # If extracted text is too short, it might be a scanned PDF
        if len(text.strip()) < 50:
            try:
                # Attempt OCR as fallback
                return extract_from_scanned_pdf(file_bytes)
            except:
                pass
        
        return text
    except Exception as e:
        # Try OCR as fallback
        try:
            return extract_from_scanned_pdf(file_bytes)
        except:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX files"""
    try:
        doc = Document(io.BytesIO(file_bytes))
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")


def extract_from_scanned_pdf(file_bytes: bytes) -> str:
    """
    Extract text from scanned PDF using OCR (optional feature).
    Requires pytesseract and tesseract-ocr installed.
    """
    try:
        # Convert PDF to images and run OCR
        # This is a simplified implementation
        # For production, use pdf2image library
        from pdf2image import convert_from_bytes
        
        images = convert_from_bytes(file_bytes)
        text = ""
        
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
        
        return text
    except ImportError:
        raise Exception("OCR support not available. Install pdf2image and pytesseract.")
    except Exception as e:
        raise Exception(f"OCR failed: {str(e)}")
