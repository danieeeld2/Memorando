import os
from typing import List, Literal, Tuple
from pypdf import PdfReader

# Type alias for the text splitting choice
TextSplitOption = Literal["paragraph", "line"]

class DocumentProcessor:
    """
    Class responsible for loading PDF documents and processing their text content.
    Uses PyPDF2 for text extraction.
    """

    def __init__(self, pdf_path: str):
        """
        Initializes the processor with the path to the PDF file.

        :param pdf_path: Path to the PDF file.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"❌ Error: The file was not found at path: {pdf_path}")
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("❌ Error: The file must be a PDF document (.pdf extension).")
            
        self.pdf_path = pdf_path
        self.raw_text: str | None = None
        print(f"📄 DocumentProcessor initialized for: {self.pdf_path}")


    def extract_text(self) -> str:
        """
        Extracts all text from all pages of the PDF.

        :return: A single string containing the entire content of the PDF.
        """
        if self.raw_text:
            return self.raw_text

        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PdfReader(file)
                text_content = []
                
                # Iterate through all pages and extract text
                for page in reader.pages:
                    text_content.append(page.extract_text() or "")
                
                # Join the text from all pages and clean up common PDF extraction artifacts
                self.raw_text = "\n".join(text_content).strip()
                
                if not self.raw_text:
                    # Raises an error if no text was found (e.g., image-based PDF)
                    raise Exception("The PDF extraction yielded no text. The document might be image-based or empty.")

                print(f"✅ Text extracted successfully. Total characters: {len(self.raw_text)}")
                return self.raw_text

        except Exception as e:
            print(f"❌ An error occurred during PDF text extraction: {e}")
            self.raw_text = ""
            return ""


    def fragment_text(self, split_by: TextSplitOption = "paragraph") -> List[str]:
        """
        Splits the extracted text into fragments, either by paragraphs or by lines,
        to be fed into the study method.

        :param split_by: Fragmentation option ('paragraph' or 'line').
        :return: A list of strings, where each string is a study chunk.
        """
        if not self.raw_text:
            # Attempt to extract text if it hasn't been done yet
            self.extract_text()
            if not self.raw_text:
                return []

        # Normalize line breaks and remove excessive white space
        cleaned_text = self.raw_text.replace('\r\n', '\n').replace('\r', '\n')
        
        fragments: List[str] = []

        if split_by == "paragraph":
            # Split by two or more newlines (common paragraph separator in extracted text)
            # Filter out any empty strings that might result from extra newlines
            fragments = [
                p.strip() 
                for p in cleaned_text.split('\n\n') 
                if p.strip()
            ]
            print(f"✂️ Text fragmented by paragraph. Total fragments: {len(fragments)}")

        elif split_by == "line":
            # Split by single newline and filter out empty lines
            fragments = [
                line.strip() 
                for line in cleaned_text.split('\n') 
                if line.strip()
            ]
            print(f"✂️ Text fragmented by line. Total fragments: {len(fragments)}")
        
        else:
            print(f"⚠️ Unknown split option: {split_by}. Defaulting to paragraph split.")
            # Recursive call with default option
            return self.fragment_text(split_by="paragraph")

        return fragments

# --- Example Usage for Terminal Testing ---

def run_cli_test():
    """
    Test function to run the processor from the terminal.
    It simulates loading a PDF and choosing the fragmentation.
    """
    print("\n--- Document Processor CLI Test ---")
    
    # NOTE: You MUST replace 'sample_document.pdf' with a valid path to a test PDF
    pdf_path = input("Enter the path to your PDF file (e.g., /path/to/doc.pdf): ")
    if not pdf_path:
        print("Test cancelled. Please provide a path next time.")
        return

    try:
        processor = DocumentProcessor(pdf_path)
        
        # 1. Extraction
        text = processor.extract_text()
        if not text:
            return

        # 2. Split Option Choice
        split_choice = input("Split by (p)aragraph or (l)ine? [p/l]: ").lower()
        
        if split_choice == 'l':
            split_option: TextSplitOption = "line"
        else:
            split_option: TextSplitOption = "paragraph"
            
        # 3. Fragmentation
        study_chunks = processor.fragment_text(split_option)

        if study_chunks:
            print("\n📚 First 5 Study Chunks:")
            for i, chunk in enumerate(study_chunks[:5]):
                # Print first 80 chars of the chunk
                print(f"  [{i+1}] {chunk[:80]}...")
            
            print(f"\nSummary: Loaded {len(study_chunks)} chunks using '{split_option}' split.")
            
    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    run_cli_test()
