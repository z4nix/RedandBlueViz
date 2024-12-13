import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime
import os
from pathlib import Path
import pypdf
import pdfplumber
import re
from typing import Dict, Optional
import spacy

def extract_pdf_metadata(pdf_path: str) -> Dict[str, any]:
    """Extract metadata from a PDF file"""
    try:
        # Load spaCy model for better text processing
        try:
            nlp = spacy.load("en_core_web_sm")
        except:
            st.warning("Installing required language model (one-time setup)...")
            os.system("python -m spacy download en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        metadata = {}
        
        # Extract text from first few pages
        with pdfplumber.open(pdf_path) as pdf:
            # Get first page text for title and authors
            first_page = pdf.pages[0].extract_text()
            
            # Try to get abstract from first two pages
            abstract_text = ""
            for i in range(min(2, len(pdf.pages))):
                abstract_text += pdf.pages[i].extract_text()

        # Also use PyPDF2 for metadata
        with pypdf.PdfReader(pdf_path) as pdf:
            pdf_info = pdf.metadata
            if pdf_info:
                # Try to get title from PDF metadata
                if pdf_info.get('/Title'):
                    metadata['title'] = pdf_info['/Title']
                if pdf_info.get('/Author'):
                    metadata['authors'] = pdf_info['/Author']
                if pdf_info.get('/Subject'):
                    metadata['keywords'] = [k.strip() for k in pdf_info['/Subject'].split(',')]

        # If title not in metadata, try to extract from first page
        if 'title' not in metadata:
            # Usually the title is at the start and ends with a period or newline
            title_match = re.search(r'^[^\n.]+[.\n]', first_page)
            if title_match:
                metadata['title'] = title_match.group(0).strip('.\n')

        # Try to find abstract
        abstract_match = re.search(r'Abstract[:\s]+(.*?)(?=\n\n|\n[A-Z]{2,}|Introduction)', 
                                 abstract_text, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            metadata['abstract'] = abstract_match.group(1).strip()

        # Try to find authors if not in metadata
        if 'authors' not in metadata:
            # Look for lines between title and abstract that might be authors
            first_lines = first_page.split('\n')[:5]  # Check first few lines
            potential_authors = []
            for line in first_lines:
                # Authors lines often contain multiple names separated by commas
                # and might include affiliations
                if ',' in line and len(line.split(',')) > 1:
                    potential_authors.append(line)
            if potential_authors:
                metadata['authors'] = potential_authors[0]

        # Try to find DOI
        doi_match = re.search(r'doi:?\s*(10\.\d{4,}/[-._;()/:\w]+)', 
                            abstract_text, re.IGNORECASE)
        if doi_match:
            metadata['doi'] = doi_match.group(1)

        # Try to find year
        year_match = re.search(r'20\d{2}|19\d{2}', first_page)
        if year_match:
            metadata['year'] = int(year_match.group(0))

        # Clean up extracted text
        for key in metadata:
            if isinstance(metadata[key], str):
                metadata[key] = metadata[key].strip()
                # Remove multiple spaces and newlines
                metadata[key] = re.sub(r'\s+', ' ', metadata[key])

        return metadata

    except Exception as e:
        st.error(f"Error extracting metadata: {str(e)}")
        return {}

def create_streamlit_app():
    # [Previous setup code remains the same]

    with tab2:
        st.header("Add/Edit Papers")
        
        operation = st.radio("Select Operation", ["Add New Paper", "Edit Existing Paper"])
        
        # Add paper form
        with st.form("paper_form"):
            # PDF upload first
            uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
            
            # Auto-extract button
            if uploaded_pdf:
                auto_extract = st.checkbox("Auto-extract metadata from PDF")
            
            # If PDF uploaded and auto-extract checked, try to extract metadata
            extracted_metadata = {}
            if uploaded_pdf and auto_extract:
                # Save PDF temporarily
                temp_pdf_path = f"temp_{uploaded_pdf.name}"
                with open(temp_pdf_path, "wb") as f:
                    f.write(uploaded_pdf.getvalue())
                
                with st.spinner("Extracting metadata from PDF..."):
                    extracted_metadata = extract_pdf_metadata(temp_pdf_path)
                
                # Clean up temporary file
                os.remove(temp_pdf_path)
                
                st.success("Metadata extracted! Please verify the extracted information below.")
            
            # Form fields with extracted metadata as default values
            title = st.text_input("Paper Title*", 
                                value=extracted_metadata.get('title', '') if auto_extract else 
                                (paper_to_edit["title"] if paper_to_edit else ""))
            
            authors = st.text_input("Authors*", 
                                  value=extracted_metadata.get('authors', '') if auto_extract else 
                                  (paper_to_edit["authors"] if paper_to_edit else ""))
            
            year = st.number_input("Year*", 
                                 min_value=1900, 
                                 max_value=datetime.now().year,
                                 value=extracted_metadata.get('year', datetime.now().year) if auto_extract else 
                                 (paper_to_edit["year"] if paper_to_edit else datetime.now().year))
            
            abstract = st.text_area("Abstract*", 
                                  value=extracted_metadata.get('abstract', '') if auto_extract else 
                                  (paper_to_edit["abstract"] if paper_to_edit else ""))
            
            doi = st.text_input("DOI", 
                              value=extracted_metadata.get('doi', '') if auto_extract else 
                              (paper_to_edit.get("doi", "") if paper_to_edit else ""))
            
            # [Rest of the form fields and submission handling remains the same]

    # [Rest of the app code remains the same]

if __name__ == "__main__":
    create_streamlit_app()
