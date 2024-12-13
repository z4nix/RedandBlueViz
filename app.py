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

def setup_directories():
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def load_papers_from_json():
    try:
        with open('papers_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"redTeaming": [], "blueTeaming": []}

def save_papers_to_json(papers_data):
    with open('papers_data.json', 'w') as f:
        json.dump(papers_data, f, indent=2)

def get_pdf_path(category, filename):
    folder = "red_teaming" if category == "redTeaming" else "blue_teaming"
    return f"papers_storage/{folder}/{filename}"

def save_uploaded_pdf(uploaded_file, category):
    if uploaded_file is None:
        return None
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    pdf_path = get_pdf_path(category, filename)
    
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return filename

def extract_pdf_metadata(pdf_path):
    """Improved metadata extraction focusing on essential fields"""
    try:
        metadata = {}
        
        # Extract text from first two pages
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for i in range(min(2, len(pdf.pages))):
                text += pdf.pages[i].extract_text() + "\n"

        # Try to extract title (usually the first line before any authors)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            metadata['title'] = lines[0]

        # Try to extract authors (usually after title, before abstract)
        author_lines = []
        for line in lines[1:4]:  # Check next few lines after title
            # Authors lines typically contain multiple names and/or affiliations
            if ',' in line and not any(word in line.lower() for word in ['abstract', 'introduction', 'keywords']):
                author_lines.append(line)
        if author_lines:
            metadata['authors'] = author_lines[0]

        # Try to extract abstract
        abstract_pattern = r'(?:abstract|summary)[\s:]+([^introduction]*?)(?:(?:introduction|\d\.|keywords|index terms)|\n\n)'
        abstract_match = re.search(abstract_pattern, text.lower(), re.IGNORECASE | re.DOTALL)
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            # Clean up the abstract
            abstract_text = re.sub(r'\s+', ' ', abstract_text)
            metadata['abstract'] = abstract_text

        # Try to extract year
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)
        if years:
            # Take the first year found
            metadata['year'] = int(years[0])
        else:
            metadata['year'] = datetime.now().year

        return metadata

    except Exception as e:
        st.error(f"Error extracting metadata: {str(e)}")
        return {}

def create_streamlit_app():
    setup_directories()
    st.set_page_config(page_title="Red/Blue Teaming Papers Viewer", layout="wide")
    
    st.title("Red/Blue Teaming Papers Viewer")
    
    # Create tabs
    tabs = st.tabs(["View Papers", "Add/Edit Papers", "Bulk Import"])
    
    # Load papers
    papers = load_papers_from_json()
    
    # Tab 1: View Papers
    with tabs[0]:
        # Stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Red Teaming Papers", len(papers["redTeaming"]))
        with col2:
            st.metric("Blue Teaming Papers", len(papers["blueTeaming"]))
        
        # Load and render the component
        with open('paper_explorer.html', 'r') as f:
            html_content = f.read()
        
        # Inject the papers data
        papers_json = json.dumps(papers)
        html_with_data = html_content.replace(
            'const papers = {',
            f'const papers = {papers_json}'
        )
        
        # Render the component
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
                        "citations": citations,
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
                            "citations": int(row.get("citations", 0)),
                            "dateAdded": datetime.now().strftime("%Y-%m-%d")
                        })
                    save_papers_to_json(papers)
                    st.success("Papers imported successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error importing papers: {str(e)}")

if __name__ == "__main__":
    create_streamlit_app()
