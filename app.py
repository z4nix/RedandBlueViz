import streamlit as st
import arxiv
import os
from pathlib import Path
from datetime import datetime
import requests

def setup_directories():
    """Create directories for storing papers"""
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def extract_arxiv_id(url):
    """Extract arXiv ID from URL"""
    # Handle different arXiv URL formats
    if 'arxiv.org/abs/' in url:
        return url.split('arxiv.org/abs/')[-1].split('v')[0].strip()
    elif 'arxiv.org/pdf/' in url:
        return url.split('arxiv.org/pdf/')[-1].split('v')[0].strip().replace('.pdf', '')
    return url.strip()  # Assume it's just the ID

def get_paper_metadata(arxiv_url):
    """Get paper metadata from arXiv"""
    try:
        arxiv_id = extract_arxiv_id(arxiv_url)
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        
        return {
            'title': paper.title,
            'authors': ', '.join(author.name for author in paper.authors),
            'abstract': paper.summary,
            'year': paper.published.year,
            'pdf_url': paper.pdf_url,
            'arxiv_id': arxiv_id,
            'categories': paper.categories
        }
    except Exception as e:
        st.error(f"Error fetching paper metadata: {str(e)}")
        return None

def download_pdf(pdf_url, category, arxiv_id):
    """Download PDF from arXiv"""
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        filename = f"{arxiv_id}.pdf"
        save_path = f"papers_storage/{category}/{filename}"
        
        with open(save_path, "wb") as f:
            f.write(response.content)
        
        return filename
    except Exception as e:
        st.error(f"Error downloading PDF: {str(e)}")
        return None

def create_streamlit_app():
    setup_directories()
    st.set_page_config(page_title="arXiv Paper Organizer", layout="wide")
    
    st.title("arXiv Paper Organizer")
    
    # Create tabs
    tabs = st.tabs(["Add Papers", "View Collection"])
    
    # Add Papers tab
    with tabs[0]:
        st.header("Add Paper from arXiv")
        
        category = st.selectbox(
            "Select Category",
            ["red_teaming", "blue_teaming"],
            format_func=lambda x: "Red Teaming" if x == "red_teaming" else "Blue Teaming"
        )
        
        arxiv_url = st.text_input("Enter arXiv URL or ID")
        
        if arxiv_url:
            metadata = get_paper_metadata(arxiv_url)
            if metadata:
                st.success("Paper metadata retrieved successfully!")
                
                # Show metadata
                st.subheader("Paper Details")
                st.write("**Title:**", metadata['title'])
                st.write("**Authors:**", metadata['authors'])
                st.write("**Year:**", metadata['year'])
                with st.expander("Abstract"):
                    st.write(metadata['abstract'])
                st.write("**arXiv Categories:**", ', '.join(metadata['categories']))
                
                # Download button
                if st.button("Add to Collection"):
                    with st.spinner("Downloading PDF..."):
                        filename = download_pdf(metadata['pdf_url'], category, metadata['arxiv_id'])
                        if filename:
                            # Save metadata alongside PDF
                            metadata_path = f"papers_storage/{category}/{metadata['arxiv_id']}_metadata.json"
                            import json
                            with open(metadata_path, 'w') as f:
                                json.dump(metadata, f, indent=2)
                            st.success(f"Paper added to {category.replace('_', ' ')} collection!")
    
    # View Collection tab
    with tabs[1]:
        st.header("Paper Collection")
        
        # Display papers by category
        col1, col2 = st.columns(2)
        
        def display_papers(category, column):
            with column:
                st.subheader(category.replace('_', ' ').title())
                papers_path = f"papers_storage/{category}"
                metadata_files = [f for f in os.listdir(papers_path) if f.endswith('_metadata.json')]
                
                for metadata_file in metadata_files:
                    with open(os.path.join(papers_path, metadata_file)) as f:
                        metadata = json.load(f)
                    
                    with st.expander(metadata['title']):
                        st.write("**Authors:**", metadata['authors'])
                        st.write("**Year:**", metadata['year'])
                        with st.expander("Abstract"):
                            st.write(metadata['abstract'])
                        
                        # PDF download button
                        pdf_path = os.path.join(papers_path, f"{metadata['arxiv_id']}.pdf")
                        if os.path.exists(pdf_path):
                            with open(pdf_path, 'rb') as pdf_file:
                                st.download_button(
                                    label="Download PDF",
                                    data=pdf_file,
                                    file_name=f"{metadata['arxiv_id']}.pdf",
                                    mime="application/pdf",
                                    key=f"{category}_{metadata['arxiv_id']}"
                                )
                        
                        # Link to arXiv
                        st.markdown(f"[View on arXiv](https://arxiv.org/abs/{metadata['arxiv_id']})")
        
        display_papers("red_teaming", col1)
        display_papers("blue_teaming", col2)

if __name__ == "__main__":
    create_streamlit_app()
