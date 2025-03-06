import os
import re
import uuid
import hashlib
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: The raw text to clean
        
    Returns:
        str: Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def extract_entries_from_html(html_content: str, source_file: str) -> List[Dict[str, Any]]:
    """
    Extract dictionary entries from HTML content.
    
    Since the dictionaries have different structures, we'll try to identify 
    entries by common patterns, but won't attempt to fully parse them.
    
    Args:
        html_content: Raw HTML content of the dictionary
        source_file: Filename of the source dictionary
        
    Returns:
        List of dictionaries, each representing an entry
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Remove script and style elements
    for script in soup(['script', 'style']):
        script.decompose()
    
    entries = []
    entry_id = 1
    
    # Generate a short hash for the source file to use as prefix
    # This preserves some information about the source while ensuring uniqueness
    source_hash = hashlib.md5(source_file.encode('utf-8')).hexdigest()[:8]
    
    # Try to find dictionary entries using common patterns
    # Look for paragraph elements which might contain entries
    paragraphs = soup.find_all(['p', 'div'])
    
    # Store all text paragraphs for context extraction
    all_paragraph_texts = [clean_text(p.text) for p in paragraphs if p.text.strip() and len(p.text.strip()) >= 10]
    
    for idx, p in enumerate(paragraphs):
        # Skip empty paragraphs
        if not p.text.strip():
            continue
            
        # Clean the text
        text = clean_text(p.text)
        
        # Skip very short texts (likely not entries)
        if len(text) < 10:
            continue
            
        # Try to identify a term (headword) 
        # Often headwords are in bold or emphasized
        term = None
        bold = p.find(['b', 'strong'])
        if bold:
            term = clean_text(bold.text)
            
        # If we couldn't find a bold term, try to extract from the beginning
        if not term or len(term) < 1:
            # Try to extract first few words as the term
            words = text.split()
            if words:
                # Take the first 3 words or the first sentence, whichever is shorter
                term_end = min(3, len(words))
                term = " ".join(words[:term_end])
                if '.' in term:
                    term = term.split('.')[0].strip()
        
        # Extract surrounding context
        # Find the current paragraph's index in the all_paragraph_texts list
        try:
            current_idx = all_paragraph_texts.index(text)
            
            # Extract expanded context (2 paragraphs before and after if available)
            context_start = max(0, current_idx - 2)
            context_end = min(len(all_paragraph_texts), current_idx + 3)
            
            expanded_context = "\n\n".join(all_paragraph_texts[context_start:context_end])
            
            # Extract full context (5 paragraphs before and after if available)
            full_context_start = max(0, current_idx - 5)
            full_context_end = min(len(all_paragraph_texts), current_idx + 6)
            
            full_context = "\n\n".join(all_paragraph_texts[full_context_start:full_context_end])
        except ValueError:
            # If we can't find the current paragraph in the list, use default contexts
            expanded_context = text
            full_context = text
        
        # Create document ID using hash prefix and a sequential number
        # This ensures uniqueness and compliance with Meilisearch requirements
        document_id = f"{source_hash}_{entry_id}"
        
        # Create entry document with a valid ID
        entry = {
            "id": document_id,
            "term": term or "Unknown Term",
            "definition": text,
            "expanded_context": expanded_context,
            "full_context": full_context,
            "source": source_file
        }
        
        entries.append(entry)
        entry_id += 1
    
    return entries

def process_html_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Process a single HTML dictionary file.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        List of extracted entries as dictionaries
    """
    source_file = os.path.basename(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return extract_entries_from_html(html_content, source_file)
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return [] 