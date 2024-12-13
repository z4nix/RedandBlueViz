import streamlit as st
import streamlit.components.v1 as components
import json
from datetime import datetime
import os
from pathlib import Path
import pandas as pd
import pypdf
import pdfplumber
import re

# Create directories for storing PDFs
def setup_directories():
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def load_papers_from_json():
    """Load papers data from JSON file"""
    try:
        with open('papers_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"redTeaming": [], "blueTeaming": []}

def save_papers_to_json(papers_data):
    """Save papers data to a JSON file"""
    with open('papers_data.json', 'w') as f:
        json.dump(papers_data, f, indent=2)

def get_pdf_path(category, filename):
    """Get the path for storing a PDF file"""
    folder = "red_teaming" if category == "redTeaming" else "blue_teaming"
    return f"papers_storage/{folder}/{filename}"

def save_uploaded_pdf(uploaded_file, category):
    """Save an uploaded PDF file and return the filename"""
    if uploaded_file is None:
        return None
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    pdf_path = get_pdf_path(category, filename)
    
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return filename

def extract_pdf_metadata(pdf_path):
    """Extract metadata from a PDF file"""
    try:
        metadata = {}
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0].extract_text()
            
            # Basic title extraction (first line)
            lines = first_page.split('\n')
            if lines:
                metadata['title'] = lines[0].strip()
            
            # Try to find abstract
            abstract_match = re.search(r'Abstract[:\s]+(.*?)(?=\n\n|\n[A-Z]{2,}|Introduction)', 
                                     first_page, re.DOTALL | re.IGNORECASE)
            if abstract_match:
                metadata['abstract'] = abstract_match.group(1).strip()
        
        # Get PDF metadata
        with pypdf.PdfReader(pdf_path) as pdf:
            pdf_info = pdf.metadata
            if pdf_info:
                metadata['year'] = datetime.now().year  # Default to current year
                if '/Author' in pdf_info:
                    metadata['authors'] = pdf_info['/Author']

        return metadata
    except Exception as e:
        st.error(f"Error extracting metadata: {str(e)}")
        return {}

def create_streamlit_app():
    setup_directories()
    st.set_page_config(page_title="AI Security Papers Explorer", layout="wide")
    
    st.title("AI Security Papers Explorer")
    
    # Initialize papers data
    papers = load_papers_from_json()
    
    # Create tabs
    tabs = st.tabs(["View Papers", "Add/Edit Papers", "Bulk Import"])
    
    # Tab 1: View Papers
    with tabs[0]:
        # Display stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Red Teaming Papers", len(papers["redTeaming"]))
        with col2:
            st.metric("Blue Teaming Papers", len(papers["blueTeaming"]))
        
        # Load and display the React component
        with open('paper_explorer.html', 'r') as f:
            html_content = f.read()
            
        html_with_data = html_content.replace(
            'const papers = {',
            f'const papers = {json.dumps(papers, indent=2)}'
        )
        
        components.html(html_with_data, height=800)
    
    # Tab 2: Add/Edit Papers
    with tabs[1]:
        st.header("Add/Edit Papers")
        
        operation = st.radio("Select Operation", ["Add New Paper", "Edit Existing Paper"])
        
        if operation == "Edit Existing Paper":
            category = st.selectbox("Select Category", ["Red Teaming", "Blue Teaming"])
            category_key = "redTeaming" if category == "Red Teaming" else "blueTeaming"
            
            if papers[category_key]:
                paper_titles = [p["title"] for p in papers[category_key]]
                selected_title = st.selectbox("Select Paper to Edit", paper_titles)
                paper_index = paper_titles.index(selected_title)
                paper_to_edit = papers[category_key][paper_index]
            else:
                st.warning(f"No papers in {category} category")
                paper_to_edit = None
        else:
            category = st.selectbox("Select Category", ["Red Teaming", "Blue Teaming"])
            category_key = "redTeaming" if category == "Red Teaming" else "blueTeaming"
            paper_to_edit = None
        
        with st.form("paper_form"):
            uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
            
            if uploaded_pdf:
                auto_extract = st.checkbox("Auto-extract metadata from PDF")
                
                if auto_extract:
                    temp_pdf_path = f"temp_{uploaded_pdf.name}"
                    with open(temp_pdf_path, "wb") as f:
                        f.write(uploaded_pdf.getvalue())
                    
                    with st.spinner("Extracting metadata from PDF..."):
                        extracted_metadata = extract_pdf_metadata(temp_pdf_path)
                    
                    os.remove(temp_pdf_path)
                    if extracted_metadata:
                        st.success("Metadata extracted! Please verify below.")
            
            title = st.text_input(
                "Paper Title*",
                value=(extracted_metadata.get('title', '') if 'extracted_metadata' in locals() else 
                      paper_to_edit["title"] if paper_to_edit else "")
            )
            
            authors = st.text_input(
                "Authors*",
                value=(extracted_metadata.get('authors', '') if 'extracted_metadata' in locals() else 
                      paper_to_edit["authors"] if paper_to_edit else "")
            )
            
            year = st.number_input(
                "Year*",
                min_value=1900,
                max_value=datetime.now().year,
                value=(extracted_metadata.get('year', datetime.now().year) if 'extracted_metadata' in locals() else 
                      paper_to_edit["year"] if paper_to_edit else datetime.now().year)
            )
            
            abstract = st.text_area(
                "Abstract*",
                value=(extracted_metadata.get('abstract', '') if 'extracted_metadata' in locals() else 
                      paper_to_edit["abstract"] if paper_to_edit else "")
            )
            
            keywords = st.text_input(
                "Keywords (comma-separated)",
                value=",".join(paper_to_edit.get("keywords", [])) if paper_to_edit else ""
            )
            
            impact = st.slider("Impact Score", 0, 100, 
                             value=paper_to_edit["impact"] if paper_to_edit else 50)
            
            citations = st.number_input("Citations", min_value=0,
                                      value=paper_to_edit["citations"] if paper_to_edit else 0)
            
            submitted = st.form_submit_button("Save Paper")
            
            if submitted:
                if not all([title, authors, abstract]):
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    pdf_filename = None
                    if uploaded_pdf:
                        pdf_filename = save_uploaded_pdf(uploaded_pdf, category_key)
                    
                    paper_data = {
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": abstract,
                        "impact": impact,
                        "citations": citations,
                        "keywords": [k.strip() for k in keywords.split(",") if k.strip()],
                        "dateAdded": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    if pdf_filename:
                        paper_data["pdf_filename"] = pdf_filename
                    
                    if operation == "Edit Existing Paper":
                        papers[category_key][paper_index] = paper_data
                        st.success("Paper updated successfully!")
                    else:
                        papers[category_key].append(paper_data)
                        st.success("Paper added successfully!")
                    
                    save_papers_to_json(papers)
                    st.rerun()
    
    # Tab 3: Bulk Import
    with tabs[2]:
        st.header("Bulk Import")
        st.write("Upload a CSV file with your papers.")
        uploaded_file = st.file_uploader("Choose CSV file", type="csv")
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if st.button("Import Papers"):
                    for _, row in df.iterrows():
                        category_key = "redTeaming" if row["category"].lower() == "red teaming" else "blueTeaming"
                        papers[category_key].append({
                            "title": row["title"],
                            "authors": row["authors"],
                            "year": int(row["year"]),
                            "abstract": row["abstract"],
                            "impact": int(row.get("impact", 50)),
                            "citations": int(row.get("citations", 0)),
                            "keywords": [k.strip() for k in str(row.get("keywords", "")).split(",") if k.strip()],
                            "dateAdded": datetime.now().strftime("%Y-%m-%d")
                        })
                    save_papers_to_json(papers)
                    st.success("Papers imported successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error importing papers: {str(e)}")

if __name__ == "__main__":
    create_streamlit_app()
