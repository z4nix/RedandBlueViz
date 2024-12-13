import streamlit as st
import arxiv
import os
from pathlib import Path
from datetime import datetime
import requests
import json

def setup_directories():
    """Create directories for storing papers"""
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def extract_arxiv_id(url):
    """Extract arXiv ID from URL with better cleaning"""
    url = url.strip()
    
    if 'arxiv.org/abs/' in url:
        id_part = url.split('arxiv.org/abs/')[-1]
    elif 'arxiv.org/pdf/' in url:
        id_part = url.split('arxiv.org/pdf/')[-1].replace('.pdf', '')
    else:
        id_part = url
    
    id_part = id_part.split('v')[0]  # Remove version number
    id_part = id_part.strip('/')     # Remove trailing slashes
    id_part = id_part.split('#')[0]  # Remove anchors
    id_part = id_part.split('?')[0]  # Remove query parameters
    
    return id_part.strip()

def get_paper_metadata(arxiv_url):
    """Get paper metadata from arXiv with better error handling"""
    try:
        arxiv_id = extract_arxiv_id(arxiv_url)
        
        if not arxiv_id:
            raise ValueError("Could not extract valid arXiv ID")
        
        st.write(f"Fetching metadata for arXiv ID: {arxiv_id}")
        
        # Fixed: Using proper iteration for search results
        search = arxiv.Search(id_list=[arxiv_id])
        results = list(search.results())  # Convert iterator to list
        if not results:
            raise ValueError("No paper found with this ID")
        paper = results[0]  # Get first result
        
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
    
    tabs = st.tabs(["Add Papers", "View Collection"])
    
    # Add Papers tab
    with tabs[0]:
        st.header("Add Paper from arXiv")
        
        st.markdown("""
        Enter an arXiv URL (e.g., https://arxiv.org/abs/2202.12467) or just the ID (e.g., 2202.12467).
        """)
        
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
                            metadata_path = f"papers_storage/{category}/{metadata['arxiv_id']}_metadata.json"
                            with open(metadata_path, 'w') as f:
                                json.dump(metadata, f, indent=2)
                            st.success(f"Paper added to {category.replace('_', ' ')} collection!")
    
    # View Collection tab
    with tabs[1]:
        st.header("Paper Collection")
        
        col1, col2 = st.columns(2)
        
        def display_papers(category, column):
            with column:
                st.subheader(category.replace('_', ' ').title())
                papers_path = f"papers_storage/{category}"
                
                if not os.path.exists(papers_path):
                    st.info(f"No papers in {category.replace('_', ' ')} collection yet.")
                    return
                
                metadata_files = [f for f in os.listdir(papers_path) if f.endswith('_metadata.json')]
                
                if not metadata_files:
                    st.info(f"No papers in {category.replace('_', ' ')} collection yet.")
                    return
                
                for metadata_file in sorted(metadata_files, reverse=True):
                    with open(os.path.join(papers_path, metadata_file)) as f:
                        metadata = json.load(f)
                    
                    with st.expander(f"📄 {metadata['title']}"):
                        st.write("**Authors:**", metadata['authors'])
                        st.write("**Year:**", metadata['year'])
                        st.write("**Abstract:**")
                        st.write(metadata['abstract'])
                        
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_path = os.path.join(papers_path, f"{metadata['arxiv_id']}.pdf")
                            if os.path.exists(pdf_path):
                                with open(pdf_path, 'rb') as pdf_file:
                                    st.download_button(
                                        label="📥 Download PDF",
                                        data=pdf_file,
                                        file_name=f"{metadata['arxiv_id']}.pdf",
                                        mime="application/pdf",
                                        key=f"{category}_{metadata['arxiv_id']}"
                                    )
                        with col2:
                            st.markdown(f"[🔗 View on arXiv](https://arxiv.org/abs/{metadata['arxiv_id']})")

if __name__ == "__main__":
    create_streamlit_app()
