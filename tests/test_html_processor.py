"""
Test HTML processing functionality
"""
import os
from app.indexer.html_processor import process_html_file, extract_entries_from_html, clean_text

def test_clean_text():
    """Test text cleaning functionality"""
    # Test basic whitespace cleaning
    assert clean_text("  test   string  ") == "test string"
    # Test newline handling
    assert clean_text("test\nstring") == "test string"
    # Test multiple whitespace
    assert clean_text("test    string") == "test string"

def test_extract_entries():
    """Test extraction of entries from HTML content"""
    html_content = """
    <html>
    <body>
        <p><b>Term1</b> - Definition1</p>
        <p><b>Term2</b> - Definition2</p>
    </body>
    </html>
    """
    
    entries = extract_entries_from_html(html_content, "test_source.html")
    
    # Check that we got 2 entries
    assert len(entries) == 2
    
    # Check content of entries
    assert entries[0]["term"] == "Term1"
    assert "Definition1" in entries[0]["definition"]
    assert entries[0]["source"] == "test_source.html"
    
    assert entries[1]["term"] == "Term2"
    assert "Definition2" in entries[1]["definition"]

def test_process_html_file():
    """Test processing of a sample HTML file"""
    # Path to our test sample HTML file
    test_file = os.path.join(os.path.dirname(__file__), "test_sample.html")
    
    # Process the file
    entries = process_html_file(test_file)
    
    # Check that we got 4 entries (Tree, Forest, Лес, Хъæд)
    assert len(entries) == 4
    
    # Check that we have both English and Russian terms
    terms = [entry["term"] for entry in entries]
    assert "Tree" in terms
    assert "Forest" in terms
    assert "Лес" in terms
    assert "Хъæд" in terms
    
    # Check term and definition pairs
    for entry in entries:
        if entry["term"] == "Tree":
            assert "perennial plant" in entry["definition"]
        elif entry["term"] == "Forest":
            assert "dominated by trees" in entry["definition"]
        elif entry["term"] == "Лес":
            assert "заросший деревьями" in entry["definition"]
        elif entry["term"] == "Хъæд":
            assert "бæласæй" in entry["definition"]

if __name__ == "__main__":
    test_clean_text()
    test_extract_entries()
    test_process_html_file()
    print("All HTML processor tests passed!") 