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
    """Extract arXiv ID from URL"""
    url = url.strip()
    
    if 'arxiv.org/abs/' in url:
        id_part = url.split('arxiv.org/abs/')[-1]
    elif 'arxiv.org/pdf/' in url:
        id_part = url.split('arxiv.org/pdf/')[-1].replace('.pdf', '')
    else:
        id_part = url
    
    id_part = id_part.split('v')[0]
    id_part = id_part.strip('/')
    id_part = id_part.split('#')[0]
    id_part = id_part.split('?')[0]
    
    return id_part.strip()

def get_paper_metadata(arxiv_url):
    """Get paper metadata from arXiv"""
    try:
        arxiv_id = extract_arxiv_id(arxiv_url)
        
        if not arxiv_id:
            raise ValueError("Could not extract valid arXiv ID")
        
        search = arxiv.Search(id_list=[arxiv_id])
        results = list(search.results())
        if not results:
            raise ValueError("No paper found with this ID")
        paper = results[0]
        
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

def list_papers(category):
    """List all papers in a category"""
    papers_path = f"papers_storage/{category}"
    papers = []
    
    if os.path.exists(papers_path):
        for file in os.listdir(papers_path):
            if file.endswith('_metadata.json'):
                with open(os.path.join(papers_path, file)) as f:
                    metadata = json.load(f)
                    papers.append(metadata)
    
    return sorted(papers, key=lambda x: x['year'], reverse=True)

st.set_page_config(page_title="arXiv Paper Organizer", layout="wide")
setup_directories()

st.title("arXiv Paper Organizer")

# Create tabs with collection first
collection_tab, add_tab = st.tabs(["📚 Collection", "📥 Add Paper"])

# Collection Tab (First)
with collection_tab:
    st.header("Paper Collection")
    
    # Create two columns for the categories
    left_col, right_col = st.columns(2)
    
    # Red Teaming Papers
    with left_col:
        st.markdown("""
        <div style='background-color: rgba(255, 99, 71, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff6347;'>
            <h2 style='color: #ff6347; margin: 0;'>🔥 Red Teaming Papers</h2>
        </div>
        """, unsafe_allow_html=True)
        
        red_papers = list_papers("red_teaming")
        if not red_papers:
            st.info("🔍 No papers in Red Teaming collection yet.")
        else:
            for paper in red_papers:
                with st.expander(f"📑 {paper['title']}"):
                    st.markdown("""
                    <div style='background-color: rgba(255, 99, 71, 0.05); padding: 1rem; border-radius: 0.5rem;'>
                    """, unsafe_allow_html=True)
                    
                    st.write("👥 **Authors:**", paper['authors'])
                    st.write("📅 **Year:**", paper['year'])
                    st.write("📝 **Abstract:**")
                    st.write(paper['abstract'])
                    st.markdown("---")
                    
                    pdf_path = f"papers_storage/red_teaming/{paper['arxiv_id']}.pdf"
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as pdf_file:
                            st.download_button(
                                "📥 Download PDF",
                                pdf_file,
                                file_name=f"{paper['arxiv_id']}.pdf",
                                mime="application/pdf",
                                key=f"red_{paper['arxiv_id']}"
                            )
                    
                    st.markdown(f"[🔗 View on arXiv](https://arxiv.org/abs/{paper['arxiv_id']})")
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # Blue Teaming Papers
    with right_col:
        st.markdown("""
        <div style='background-color: rgba(0, 122, 255, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #007AFF;'>
            <h2 style='color: #007AFF; margin: 0;'>🛡️ Blue Teaming Papers</h2>
        </div>
        """, unsafe_allow_html=True)
        
        blue_papers = list_papers("blue_teaming")
        if not blue_papers:
            st.info("🔍 No papers in Blue Teaming collection yet.")
        else:
            for paper in blue_papers:
                with st.expander(f"📑 {paper['title']}"):
                    st.markdown("""
                    <div style='background-color: rgba(0, 122, 255, 0.05); padding: 1rem; border-radius: 0.5rem;'>
                    """, unsafe_allow_html=True)
                    
                    st.write("👥 **Authors:**", paper['authors'])
                    st.write("📅 **Year:**", paper['year'])
                    st.write("📝 **Abstract:**")
                    st.write(paper['abstract'])
                    st.markdown("---")
                    
                    pdf_path = f"papers_storage/blue_teaming/{paper['arxiv_id']}.pdf"
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as pdf_file:
                            st.download_button(
                                "📥 Download PDF",
                                pdf_file,
                                file_name=f"{paper['arxiv_id']}.pdf",
                                mime="application/pdf",
                                key=f"blue_{paper['arxiv_id']}"
                            )
                    
                    st.markdown(f"[🔗 View on arXiv](https://arxiv.org/abs/{paper['arxiv_id']})")
                    st.markdown("</div>", unsafe_allow_html=True)

# Add Papers Tab (Second)
with add_tab:
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
            
            st.subheader("Paper Details")
            st.write("**Title:**", metadata['title'])
            st.write("**Authors:**", metadata['authors'])
            st.write("**Year:**", metadata['year'])
            with st.expander("Show Abstract"):
                st.write(metadata['abstract'])
            st.write("**arXiv Categories:**", ', '.join(metadata['categories']))
            
            if st.button("Add to Collection"):
                with st.spinner("Downloading PDF..."):
                    filename = download_pdf(metadata['pdf_url'], category, metadata['arxiv_id'])
                    if filename:
                        metadata_path = f"papers_storage/{category}/{metadata['arxiv_id']}_metadata.json"
                        with open(metadata_path, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        st.success(f"Paper added to {category.replace('_', ' ')} collection!")
                        st.rerun()
