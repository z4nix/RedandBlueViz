def extract_arxiv_id(url):
    """Extract arXiv ID from URL with better cleaning"""
    # Remove any whitespace
    url = url.strip()
    
    # Handle full URLs
    if 'arxiv.org/abs/' in url:
        id_part = url.split('arxiv.org/abs/')[-1]
    elif 'arxiv.org/pdf/' in url:
        id_part = url.split('arxiv.org/pdf/')[-1].replace('.pdf', '')
    else:
        # Assume it's just the ID
        id_part = url
    
    # Clean the ID
    id_part = id_part.split('v')[0]  # Remove version number if present
    id_part = id_part.strip('/')     # Remove trailing slashes
    id_part = id_part.split('#')[0]  # Remove any anchors
    id_part = id_part.split('?')[0]  # Remove any query parameters
    
    return id_part.strip()

def get_paper_metadata(arxiv_url):
    """Get paper metadata from arXiv with better error handling"""
    try:
        arxiv_id = extract_arxiv_id(arxiv_url)
        
        # Validate arxiv ID format
        if not arxiv_id:
            raise ValueError("Could not extract valid arXiv ID")
        
        st.write(f"Fetching metadata for arXiv ID: {arxiv_id}")  # Debug info
        
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
    except StopIteration:
        st.error("Paper not found. Please check the arXiv ID/URL.")
        return None
    except Exception as e:
        st.error(f"Error fetching paper metadata: {str(e)}")
        return None
