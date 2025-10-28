import os
import json
from google import genai
from google.genai import types
from datetime import date
from typing import Dict, Any
from dotenv import load_dotenv 

# Load API Keys
load_dotenv()

def _get_client():
    """Lazy initialization of the Gemini client."""
    return genai.Client()

# --- CONFIGURATION: JSON SCHEMA ---
# Defines the JSON schema to ensure consistent structured output from the model.
json_schema = types.Schema(
    type=types.Type.OBJECT,
    required=["title", "uploaded_date", "language", "chapters", "structured_elements"],
    properties={
        "title": types.Schema(type=types.Type.STRING, description="Main title of the PDF document."),
        "uploaded_date": types.Schema(type=types.Type.STRING, description="Today's date in YYYY-MM-DD format.", format="date"),
        "language": types.Schema(type=types.Type.STRING, description="Detect the predominant language ('es' for Spanish, 'en' for English).", enum=["es", "en"]),
        "chapters": types.Schema(
            type=types.Type.ARRAY,
            description="List of chapters or main sections containing narrative study text.",
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["chapter_title", "sections"],
                properties={
                    "chapter_title": types.Schema(type=types.Type.STRING, description="The chapter or main section title."),
                    "sections": types.Schema(
                        type=types.Type.ARRAY,
                        description="Subsections within the chapter.",
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            required=["section_title", "paragraphs"],
                            properties={
                                "section_title": types.Schema(type=types.Type.STRING, description="The subsection title."),
                                "paragraphs": types.Schema(
                                    type=types.Type.ARRAY,
                                    description="List of paragraphs within this subsection.",
                                    items=types.Schema(
                                        type=types.Type.OBJECT,
                                        required=["lines"],
                                        properties={
                                            "lines": types.Schema(
                                                type=types.Type.ARRAY,
                                                description="The content of the paragraph, subdivided into individual sentences/clauses.",
                                                items=types.Schema(type=types.Type.STRING),
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
        ),
        "structured_elements": types.Schema(
            type=types.Type.ARRAY,
            description="List of non-narrative elements (tables, figures, code, etc.) extracted in RAW format.",
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["element_type", "content_raw"],
                properties={
                    "element_type": types.Schema(
                        type=types.Type.STRING,
                        description="Classification of the structured element.",
                        enum=["table", "list_of_parameters", "code_snippet", "figure_caption", "json_example"],
                    ),
                    "content_raw": types.Schema(
                        type=types.Type.STRING,
                        description="The text of the structured element, extracted as is.",
                    ),
                    "context_heading": types.Schema(
                        type=types.Type.STRING,
                        description="The closest preceding heading to provide context.",
                    ),
                },
            ),
        ),
    },
)

# Define the final instruction prompt
PROMPT_INSTRUCTION = """
An attached PDF document is provided below for analysis.

Your sole task is to generate a single JSON object that strictly follows the provided schema and completes two main extraction tasks:

1. Metadata Extraction: Fill `title`, `uploaded_date` (today's date, YYYY-MM-DD), and `language` ('es' or 'en').
2. Narrative Text Extraction (`chapters` array):
    * Extract **only** the narrative text (the main body content) and ignore all tables, technical lists, and code examples.
    * Structure the narrative text into **Chapters** (`chapters`), then **Subsections** (`sections`), and then **Paragraphs** (`paragraphs`).
    * **CRITICAL:** The content of each paragraph must be subdivided into a **List of Lines** (`lines`). Each element in this array must be a **complete, grammatically independent sentence or clause**, separated by punctuation marks (periods, question marks, exclamation points).
3. Structured Elements Extraction (`structured_elements` array):
    * Extract **all** tables, parameter lists, or code/JSON examples that were skipped in the narrative extraction.
    * For each element, fill `content_raw` with the text extracted **exactly as it appears** (preserving the table format or list structure).
    * Classify each element using the `element_type` enum (e.g., 'table', 'json_example', 'list_of_parameters').
    * Provide the closest preceding heading in `context_heading` to aid identification.

Ensure that all content is included in either the `chapters` or `structured_elements` array.
"""

# --- MAIN PROCESSING FUNCTION ---

def process_pdf_to_json(user_pdf_path: str, model_name: str = "gemini-2.5-flash") -> dict | None:
    """
    Uploads a PDF, calls the Gemini API to generate structured JSON,
    and then cleans up the uploaded file from the Gemini service.
    
    :param user_pdf_path: The local path to the user's uploaded PDF file.
    :param model_name: The Gemini model to use for extraction.
    :return: A dictionary containing the structured study data, or None on error.
    """
    pdf_file = None
    try:
        # Initialize client
        client = _get_client()
        
        # 1. Upload the user file
        print(f"Uploading file for analysis: {os.path.basename(user_pdf_path)}...")
        pdf_file = client.files.upload(file=user_pdf_path)
        
        # 2. Request configuration with schema
        config = types.GenerateContentConfig(
            temperature=0.1, 
            response_mime_type="application/json",
            response_schema=json_schema,
        )

        # 3. Content: Prompt and the uploaded file
        contents = [PROMPT_INSTRUCTION, pdf_file]

        # 4. API Call
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        # 5. Return the JSON as a Python dictionary
        data = json.loads(response.text)
        # Add today's date for consistency
        data['uploaded_date'] = date.today().isoformat()
        return data

    except Exception as e:
        print(f"❌ An error occurred during Gemini processing: {e}")
        return None
        
    finally:
        # 6. Cleanup: Delete the file uploaded to the Gemini service.
        if pdf_file:
            client.files.delete(name=pdf_file.name)
            print(f"Temporary file {pdf_file.name} deleted from Gemini service.")
