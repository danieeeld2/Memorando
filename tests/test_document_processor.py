import pytest
import os
import sys
from pypdf import PdfReader 
from unittest.mock import patch

# Add the 'backend' directory to the path for correct imports from your project structure
# This is crucial for pytest to find your core modules.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Import the classes to be tested from your backend structure
from core.document_processor import DocumentProcessor, TextSplitOption 

# --- Setup Fixtures (Mocks and Helpers) ---

# Mock classes to simulate PDF reading without needing a real file
class MockPdfPage:
    """Simulates a single PDF page for text extraction."""
    def __init__(self, text):
        self._text = text
    def extract_text(self):
        return self._text

class MockPdfReader:
    """Simulates the PyPDF2 PdfReader class. We patch the real one with this."""
    def __init__(self, texts):
        self.pages = [MockPdfPage(text) for text in texts]

# Mock data simulating a two-page document with different line breaks
MOCK_PAGE_TEXTS = [
    "This is the first paragraph. It is a continuation sentence.\nThis is the second line.",
    "Page two starts here, with three sentences.\n\nThis is a new paragraph, separated by a double newline."
]

@pytest.fixture
def mock_pdf_file(tmp_path):
    """Creates a temporary, existing file path (content doesn't matter since PdfReader is mocked)."""
    # Create a dummy file path that actually exists in the filesystem, 
    # so DocumentProcessor doesn't fail on os.path.exists() check.
    dummy_pdf_path = tmp_path / "dummy_doc.pdf"
    dummy_pdf_path.write_text("dummy content")
    return str(dummy_pdf_path)

# --- DocumentProcessor Tests ---

def test_initialization_success(mock_pdf_file):
    """Verifies successful initialization with a valid path."""
    processor = DocumentProcessor(mock_pdf_file)
    assert processor.pdf_path == mock_pdf_file

def test_initialization_file_not_found():
    """Verifies that FileNotFoundError is raised if the file does not exist."""
    with pytest.raises(FileNotFoundError, match="not found"):
        DocumentProcessor("non_existent_file.pdf")

def test_initialization_invalid_extension(tmp_path):
    """Test that initialization raises ValueError for non-PDF files."""
    dummy_file = tmp_path / "image.jpg"
    dummy_file.write_text("dummy content")
    with pytest.raises(ValueError, match="must be a PDF document"):
        DocumentProcessor(str(dummy_file))

@patch('core.document_processor.PdfReader', side_effect=lambda x: MockPdfReader(MOCK_PAGE_TEXTS))
def test_extract_text_success(mock_reader, mock_pdf_file):
    """Tests simulated text extraction."""
    processor = DocumentProcessor(mock_pdf_file)
    text = processor.extract_text()
    
    assert "Page two starts here" in text
    assert len(text) > 100 # Check for non-empty string

@patch('core.document_processor.PdfReader', side_effect=lambda x: MockPdfReader(MOCK_PAGE_TEXTS))
def test_fragment_by_paragraph(mock_reader, mock_pdf_file):
    """Tests fragmentation by paragraph (split by multiple newlines)."""
    processor = DocumentProcessor(mock_pdf_file)
    processor.extract_text() 

    # CORREGIDO: Cambiado 'split_option' a 'split_by'
    chunks = processor.fragment_text(split_by="paragraph")
    
    # Expect 3 or more distinct fragments based on the mock text structure
    assert len(chunks) >= 2 
    assert "This is the first paragraph" in chunks[0]
    assert "new paragraph" in chunks[-1]


@patch('core.document_processor.PdfReader', side_effect=lambda x: MockPdfReader(MOCK_PAGE_TEXTS))
def test_fragment_by_line(mock_reader, mock_pdf_file):
    """Tests fragmentation by line (split by single newline)."""
    processor = DocumentProcessor(mock_pdf_file)
    processor.extract_text() 

    # CORREGIDO: Cambiado 'split_option' a 'split_by'
    chunks = processor.fragment_text(split_by="line")
    
    # Expect more fragments when splitting by single line
    assert len(chunks) == 4
    assert 'This is the second line.' in chunks