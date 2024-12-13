import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re

def setup_directories():
    """Create directories for storing HTML papers"""
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def extract_metadata_from_html(html_content):
    """Extract metadata from HTML paper"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        metadata = {}

        # Try to find title (usually in h1 or title)
        title = soup.find('h1')
        if not title:
            title = soup.find('title')
        if title:
            metadata['title'] = title.text.strip()

        # Try to find authors (usually in a byline or author section)
        authors = soup.find(class_=re.compile(r'author|byline', re.I))
        if authors:
            metadata['authors'] = authors.text.strip()

        # Try to find abstract
        abstract = soup.find(class_=re.compile(r'abstract|summary', re.I))
        if abstract:
            metadata['abstract'] = abstract.text.strip()

        # Try to find year
        year_pattern = r'\b(19|20)\d{2}\b'
        text = soup.get_text()
        years = re.findall(year_pattern, text)
        if years:
            metadata['year'] = int(years[0])
        else:
            metadata['year'] = datetime.now().year

        return metadata
    except Exception as e:
        st.error(f"Error extracting metadata: {str(e)}")
        return {}

def get_stored_papers():
    """Get list of stored HTML papers by category"""
    papers = {
        "red_teaming": [],
        "blue_teaming": []
    }
    
    for category in papers:
        path = f"papers_storage/{category}"
        if os.path.exists(path):
            papers[category] = [f for f in os.listdir(path) if f.endswith('.html')]
    
    return papers

def save_uploaded_html(uploaded_file, category):
    """Save uploaded HTML file and extract metadata"""
    if uploaded_file is None:
        return None
    
    # Read content and extract metadata
    content = uploaded_file.read().decode('utf-8')
    metadata = extract_metadata_from_html(content)
    
    # Create filename with timestamp
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    save_path = f"papers_storage/{category}/{filename}"
    
    # Save the file
    with open(save_path, "w", encoding='utf-8') as f:
        f.write(content)
    
    return filename, metadata

def create_streamlit_app():
    setup_directories()
    st.set_page_config(page_title="AI Security Papers", layout="wide")
    
    st.title("AI Security Papers")
    
    # Create tabs
    tabs = st.tabs(["Upload Papers", "View Papers"])
    
    # Upload tab
    with tabs[0]:
        st.header("Upload HTML Papers")
        
        category = st.selectbox(
            "Select Category",
            ["red_teaming", "blue_teaming"],
            format_func=lambda x: "Red Teaming" if x == "red_teaming" else "Blue Teaming"
        )
        
        uploaded_file = st.file_uploader(
            "Upload HTML paper",
            type="html",
            accept_multiple_files=False
        )
        
        if uploaded_file:
            filename, metadata = save_uploaded_html(uploaded_file, category)
            if metadata:
                st.success("Paper uploaded successfully!")
                st.write("Extracted metadata:")
                st.json(metadata)
            else:
                st.warning("Uploaded successfully, but couldn't extract metadata.")
    
    # View tab
    with tabs[1]:
        st.header("View Papers")
        
        papers = get_stored_papers()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Red Teaming Papers")
            for idx, paper in enumerate(papers["red_teaming"]):
                with st.expander(paper):
                    paper_path = f"papers_storage/red_teaming/{paper}"
                    with open(paper_path, "r", encoding='utf-8') as f:
                        content = f.read()
                        metadata = extract_metadata_from_html(content)
                        if metadata:
                            st.write("Title:", metadata.get('title', 'N/A'))
                            st.write("Authors:", metadata.get('authors', 'N/A'))
                            st.write("Year:", metadata.get('year', 'N/A'))
                            if 'abstract' in metadata:
                                with st.expander("Abstract"):
                                    st.write(metadata['abstract'])
                        
                        # View HTML button
                        st.download_button(
                            label="Download HTML",
                            data=content,
                            file_name=paper,
                            mime="text/html",
                            key=f"red_teaming_{idx}"
                        )
        
        with col2:
            st.subheader("Blue Teaming Papers")
            for idx, paper in enumerate(papers["blue_teaming"]):
                with st.expander(paper):
                    paper_path = f"papers_storage/blue_teaming/{paper}"
                    with open(paper_path, "r", encoding='utf-8') as f:
                        content = f.read()
                        metadata = extract_metadata_from_html(content)
                        if metadata:
                            st.write("Title:", metadata.get('title', 'N/A'))
                            st.write("Authors:", metadata.get('authors', 'N/A'))
                            st.write("Year:", metadata.get('year', 'N/A'))
                            if 'abstract' in metadata:
                                with st.expander("Abstract"):
                                    st.write(metadata['abstract'])
                        
                        # View HTML button
                        st.download_button(
                            label="Download HTML",
                            data=content,
                            file_name=paper,
                            mime="text/html",
                            key=f"blue_teaming_{idx}"
                        )

if __name__ == "__main__":
    create_streamlit_app()
