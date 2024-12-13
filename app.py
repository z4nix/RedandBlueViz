import streamlit as st
import os
from pathlib import Path
from datetime import datetime

def setup_directories():
    """Create directories for storing PDFs"""
    Path("papers_storage/red_teaming").mkdir(parents=True, exist_ok=True)
    Path("papers_storage/blue_teaming").mkdir(parents=True, exist_ok=True)

def get_stored_pdfs():
    """Get list of stored PDFs by category"""
    pdfs = {
        "red_teaming": [],
        "blue_teaming": []
    }
    
    for category in pdfs:
        path = f"papers_storage/{category}"
        if os.path.exists(path):
            pdfs[category] = os.listdir(path)
    
    return pdfs

def save_uploaded_pdf(uploaded_file, category):
    """Save uploaded PDF to appropriate directory"""
    if uploaded_file is None:
        return
    
    # Create a filename with timestamp to avoid duplicates
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
    save_path = f"papers_storage/{category}/{filename}"
    
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return filename

def create_streamlit_app():
    setup_directories()
    st.set_page_config(page_title="AI Security Papers", layout="wide")
    
    st.title("AI Security Papers")
    
    # Create tabs
    tabs = st.tabs(["Upload Papers", "View Papers"])
    
    # Upload tab
    with tabs[0]:
        st.header("Upload Papers")
        
        category = st.selectbox(
            "Select Category",
            ["red_teaming", "blue_teaming"],
            format_func=lambda x: "Red Teaming" if x == "red_teaming" else "Blue Teaming"
        )
        
        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type="pdf",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                save_uploaded_pdf(uploaded_file, category)
                st.success(f"Saved: {uploaded_file.name}")
    
    # View tab
    with tabs[1]:
        st.header("View Papers")
        
        pdfs = get_stored_pdfs()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Red Teaming Papers")
            for idx, pdf in enumerate(pdfs["red_teaming"]):
                with st.expander(pdf):
                    pdf_path = f"papers_storage/red_teaming/{pdf}"
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download PDF",
                            data=f.read(),
                            file_name=pdf,
                            mime="application/pdf",
                            key=f"red_teaming_{idx}"  # Added unique key
                        )
        
        with col2:
            st.subheader("Blue Teaming Papers")
            for idx, pdf in enumerate(pdfs["blue_teaming"]):
                with st.expander(pdf):
                    pdf_path = f"papers_storage/blue_teaming/{pdf}"
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download PDF",
                            data=f.read(),
                            file_name=pdf,
                            mime="application/pdf",
                            key=f"blue_teaming_{idx}"  # Added unique key
                        )

if __name__ == "__main__":
    create_streamlit_app()
