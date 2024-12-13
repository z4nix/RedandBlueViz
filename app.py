import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
from datetime import datetime
import os
import base64
from pathlib import Path
import shutil

# Create directories for storing PDFs
def setup_directories():
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def get_pdf_path(category, filename):
    """Get the path for storing a PDF file"""
    folder = "red_teaming" if category == "redTeaming" else "blue_teaming"
    return f"papers_storage/{folder}/{filename}"

def save_uploaded_pdf(uploaded_file, category):
    """Save an uploaded PDF file and return the filename"""
    if uploaded_file is None:
        return None
    
    # Create a safe filename
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    pdf_path = get_pdf_path(category, filename)
    
    # Save the file
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return filename

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

def display_pdf(pdf_path):
    """Display a PDF file in Streamlit"""
    try:
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")

def create_streamlit_app():
    setup_directories()
    st.set_page_config(page_title="AI Security Papers Explorer", layout="wide")
    
    st.title("AI Security Papers Explorer")
    
    # Initialize session state
    if 'editing_paper_index' not in st.session_state:
        st.session_state.editing_paper_index = None
    if 'editing_category' not in st.session_state:
        st.session_state.editing_category = None
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["View Papers", "Add/Edit Papers", "Bulk Import", "PDF Viewer"])
    
    papers = load_papers_from_json()
    
    with tab1:
        # [Previous view tab code remains the same]
        with open('paper_explorer.html', 'r') as f:
            html_content = f.read()
        
        # Display stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Red Teaming Papers", len(papers["redTeaming"]))
        with col2:
            st.metric("Blue Teaming Papers", len(papers["blueTeaming"]))
        
        html_with_data = html_content.replace(
            'const papers = {',
            f'const papers = {json.dumps(papers, indent=2)}'
        )
        
        components.html(html_with_data, height=800)
    
    with tab2:
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
                
                # Show existing PDF if available
                if "pdf_filename" in paper_to_edit:
                    st.write("Current PDF:", paper_to_edit["pdf_filename"])
            else:
                st.warning(f"No papers in {category} category")
                paper_to_edit = None
        else:
            category = st.selectbox("Select Category", ["Red Teaming", "Blue Teaming"])
            category_key = "redTeaming" if category == "Red Teaming" else "blueTeaming"
            paper_to_edit = None
        
        with st.form("paper_form"):
            title = st.text_input("Paper Title*", value=paper_to_edit["title"] if paper_to_edit else "")
            authors = st.text_input("Authors*", value=paper_to_edit["authors"] if paper_to_edit else "")
            year = st.number_input("Year*", min_value=1900, max_value=datetime.now().year, 
                                 value=paper_to_edit["year"] if paper_to_edit else datetime.now().year)
            
            # PDF upload
            uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
            
            url = st.text_input("Paper URL", value=paper_to_edit.get("url", "") if paper_to_edit else "")
            doi = st.text_input("DOI", value=paper_to_edit.get("doi", "") if paper_to_edit else "")
            abstract = st.text_area("Abstract*", value=paper_to_edit["abstract"] if paper_to_edit else "")
            keywords = st.text_input("Keywords (comma-separated)", 
                                   value=",".join(paper_to_edit.get("keywords", [])) if paper_to_edit else "")
            
            col1, col2 = st.columns(2)
            with col1:
                impact = st.slider("Impact Score", 0, 100, 
                                 value=paper_to_edit["impact"] if paper_to_edit else 50)
            with col2:
                citations = st.number_input("Citations", min_value=0, 
                                          value=paper_to_edit["citations"] if paper_to_edit else 0)
            
            submitted = st.form_submit_button("Save Paper")
            
            if submitted:
                if not all([title, authors, abstract]):
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    # Handle PDF upload
                    pdf_filename = None
                    if uploaded_pdf:
                        pdf_filename = save_uploaded_pdf(uploaded_pdf, category_key)
                    elif paper_to_edit and "pdf_filename" in paper_to_edit:
                        pdf_filename = paper_to_edit["pdf_filename"]
                    
                    paper_data = {
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "abstract": abstract,
                        "impact": impact,
                        "citations": citations,
                        "url": url,
                        "doi": doi,
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
    
    with tab3:
        # [Previous bulk import code remains the same]
        st.header("Bulk Import Papers")
        # ... [rest of bulk import code]
    
    with tab4:
        st.header("PDF Viewer")
        
        # Paper selection for PDF viewing
        category = st.selectbox("Select Category", ["Red Teaming", "Blue Teaming"], key="pdf_category")
        category_key = "redTeaming" if category == "Red Teaming" else "blueTeaming"
        
        # Filter papers with PDFs
        papers_with_pdfs = [p for p in papers[category_key] if "pdf_filename" in p]
        
        if papers_with_pdfs:
            selected_paper = st.selectbox(
                "Select Paper to View",
                papers_with_pdfs,
                format_func=lambda x: x["title"]
            )
            
            if selected_paper:
                pdf_path = get_pdf_path(category_key, selected_paper["pdf_filename"])
                if os.path.exists(pdf_path):
                    display_pdf(pdf_path)
                else:
                    st.error("PDF file not found")
        else:
            st.warning(f"No papers with PDFs in {category} category")

if __name__ == "__main__":
    create_streamlit_app()
