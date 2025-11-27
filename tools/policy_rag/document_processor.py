"""
Document ingestion module for HR Policy RAG Agent.
Handles PDF/text conversion, chunking, and metadata extraction.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
import pdfplumber
import PyPDF2
from sentence_transformers import SentenceTransformer
import tiktoken

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes HR documents and prepares them for embedding."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file with page metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict containing text content and metadata
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        try:
            # Try pdfplumber first (better for complex layouts)
            with pdfplumber.open(pdf_path) as pdf:
                pages = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append({
                            'page_number': page_num,
                            'text': text.strip()
                        })
                
                if pages:
                    return {
                        'filename': Path(pdf_path).name,
                        'pages': pages,
                        'total_pages': len(pages)
                    }
        
        except Exception as e:
            logger.warning(f"pdfplumber failed for {pdf_path}: {e}. Trying PyPDF2...")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pages = []
                    
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text = page.extract_text()
                        if text and text.strip():
                            pages.append({
                                'page_number': page_num,
                                'text': text.strip()
                            })
                    
                    return {
                        'filename': Path(pdf_path).name,
                        'pages': pages,
                        'total_pages': len(pages)
                    }
            
            except Exception as e:
                logger.error(f"Failed to extract text from {pdf_path}: {e}")
                return None
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]+', ' ', text)
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def split_into_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Document metadata
            
        Returns:
            List of text chunks with metadata
        """
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        
        chunks = []
        start_idx = 0
        chunk_id = 0
        
        while start_idx < len(tokens):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(tokens))
            
            # Extract chunk tokens and decode to text
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Create chunk metadata
            chunk_metadata = {
                **metadata,
                'chunk_id': chunk_id,
                'start_token': start_idx,
                'end_token': end_idx,
                'token_count': len(chunk_tokens),
                'text': chunk_text
            }
            
            chunks.append(chunk_metadata)
            
            # Move start index for next chunk (with overlap)
            start_idx = end_idx - self.chunk_overlap
            chunk_id += 1
            
            # Break if we've covered all tokens
            if end_idx >= len(tokens):
                break
        
        logger.info(f"Created {len(chunks)} chunks from text ({len(tokens)} tokens)")
        return chunks
    
    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a single document file (PDF or text).
        
        Args:
            file_path: Path to document file
            
        Returns:
            List of processed chunks with metadata
        """
        logger.info(f"Processing document: {file_path}")
        
        file_path = Path(file_path)
        all_chunks = []
        
        if file_path.suffix.lower() == '.pdf':
            # Process PDF
            pdf_data = self.extract_text_from_pdf(str(file_path))
            if not pdf_data:
                logger.error(f"Failed to extract text from PDF: {file_path}")
                return []
            
            # Process each page
            for page_data in pdf_data['pages']:
                page_text = self.clean_text(page_data['text'])
                
                if not page_text.strip():
                    continue
                
                page_metadata = {
                    'doc_id': file_path.stem,
                    'filename': pdf_data['filename'],
                    'page_number': page_data['page_number'],
                    'total_pages': pdf_data['total_pages'],
                    'doc_type': 'pdf'
                }
                
                # Split page into chunks
                page_chunks = self.split_into_chunks(page_text, page_metadata)
                all_chunks.extend(page_chunks)
        
        elif file_path.suffix.lower() == '.txt':
            # Process text file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                cleaned_text = self.clean_text(text)
                
                if not cleaned_text.strip():
                    logger.warning(f"Empty text file: {file_path}")
                    return []
                
                metadata = {
                    'doc_id': file_path.stem,
                    'filename': file_path.name,
                    'page_number': 1,
                    'total_pages': 1,
                    'doc_type': 'text'
                }
                
                # Split into chunks
                chunks = self.split_into_chunks(cleaned_text, metadata)
                all_chunks.extend(chunks)
                
            except Exception as e:
                logger.error(f"Failed to process text file {file_path}: {e}")
                return []
        
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return []
        
        logger.info(f"Processed {file_path}: {len(all_chunks)} chunks created")
        return all_chunks
    
    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        Process all documents in a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of all processed chunks from all documents
        """
        logger.info(f"Processing directory: {directory_path}")
        
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return []
        
        all_chunks = []
        supported_extensions = ['.pdf', '.txt']
        
        # Find all supported files
        files = []
        for ext in supported_extensions:
            files.extend(directory.glob(f'*{ext}'))
        
        if not files:
            logger.warning(f"No supported files found in {directory_path}")
            return []
        
        logger.info(f"Found {len(files)} files to process")
        
        # Process each file
        for file_path in files:
            try:
                file_chunks = self.process_document(str(file_path))
                all_chunks.extend(file_chunks)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue
        
        logger.info(f"Directory processing complete: {len(all_chunks)} total chunks")
        return all_chunks


# Example usage and testing
if __name__ == "__main__":
    # Create sample HR document for testing
    sample_doc_path = Path("../data/hr_documents/sample_policy.txt")
    sample_doc_path.parent.mkdir(parents=True, exist_ok=True)
    
    sample_content = """
    COMPANY HR POLICY HANDBOOK
    
    1. LEAVE POLICY
    All employees are entitled to 20 days of paid vacation per year.
    Vacation time must be requested at least 2 weeks in advance.
    Sick leave is available for up to 10 days per year.
    
    2. ATTENDANCE POLICY
    Regular attendance is required for all employees.
    Flexible working hours are available from 8 AM to 6 PM core hours.
    Remote work is permitted up to 2 days per week with manager approval.
    
    3. BENEFITS
    Health insurance is provided for all full-time employees.
    Dental and vision coverage is optional.
    Retirement benefits include 401(k) matching up to 4%.
    """
    
    with open(sample_doc_path, 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    # Test the processor
    processor = DocumentProcessor(chunk_size=200, chunk_overlap=20)
    chunks = processor.process_directory("../data/hr_documents")
    
    print(f"\nProcessed {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\nChunk {i+1}:")
        print(f"  Doc ID: {chunk['doc_id']}")
        print(f"  Page: {chunk['page_number']}")
        print(f"  Tokens: {chunk['token_count']}")
        print(f"  Text: {chunk['text'][:150]}...")