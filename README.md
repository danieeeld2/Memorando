# 🧠 Memorando: The Smart Study Companion

## 🌟 Quick Overview
**Memorando** is a desktop application designed to transform passive reading of PDF documents into active, guided study sessions.  

By leveraging **AI-powered document processing**, **Text-to-Speech (TTS)** technology, and structured memorization techniques, it helps users achieve deeper learning and better information retention.

This initial version is a **Minimal Viable Product (MVP)**, entirely free, built to validate the core concept, test the architecture, and collect critical usage data (analytics) before scaling to a commercial mobile version.

---

## 🎯 Our Goals

### 1. Portfolio Showcase (Open Source & AGPLv3)
The core logic of the free desktop MVP is licensed under the **AGPLv3 (Affero General Public License)**.  

This strategy achieves two key objectives:
- **Career Advancement**: A high-quality portfolio piece demonstrating robust, scalable Python architecture, AI integration, modern API design (FastAPI), and clean coding practices.  
- **Legal Protection**: AGPLv3 safeguards the project against competitors attempting to copy the free code and turn it into a closed, paid service.

### 2. Business Validation & Future Growth
The MVP serves as a **data-gathering tool**. We aim to measure user engagement and method preference to inform the decision to secure funding for the next phase:
- **Mobile Port**: iOS and Android versions (likely using React Native).  
- **Premium Features**: Proprietary memorization algorithms and cloud-based features (kept private and protected).

---

## 🛠️ Technology Stack (Current MVP)

| **Component**          | **Technology**              | **Purpose**                                                                 |
|------------------------|-----------------------------|-------------------------------------------------------------------------------|
| Backend API            | FastAPI + Python            | RESTful API for document management, session creation, and study control.     |
| Document Processing    | Google Gemini API           | AI-powered extraction of structured content from PDF documents.               |
| Database               | SQLite                      | Lightweight storage for users, documents, and study sessions.                 |
| TTS Engine             | pyttsx3                     | Local text-to-speech voice synthesis for study methods.                       |
| Testing                | pytest + unittest.mock      | Comprehensive test coverage with isolated testing environments.               |
| GUI (Planned)          | Electron + React            | Package the web interface into a cross-platform desktop app (Windows/Mac/Linux). |

---

## 🤖 AI-Powered Features

### Intelligent Document Processing
Memorando uses **Google's Gemini 2.5 Flash** model to:
- Extract and structure content from PDFs into a hierarchical JSON format
- Separate narrative text from tables, code snippets, and technical elements
- Detect document language automatically (Spanish/English)
- Break down content into study-optimized segments (sentences/clauses)

This approach ensures **high-quality extraction** that preserves document structure while making content ideal for active learning methods.

---

## 📚 Study Methods Implemented

- **Read & Repeat**: Reads a segment, pauses for user repetition, and repeats the segment for reinforcement.  
- **Question & Answer (Flashcards)**: _(Planned)_ Splits text into simulated Q&A pairs; reads the question, waits for user input, then reveals the answer.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Google Gemini API key (get one at [ai.google.dev](https://ai.google.dev))

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Memorando.git
cd Memorando
```

### 2. Setup Environment Variables
Create a `.env` file in the `backend/` directory:
```bash
GEMINI_API_KEY=your_api_key_here
```

### 3. Setup Virtual Environment
Run from the project root:
```bash
python3 -m venv backend/.venv
```

### 4. Activate the Environment

| Operating System | Command                                   |
|------------------|-------------------------------------------|
| Linux / macOS    | `source backend/.venv/bin/activate`       |
| Windows (CMD)    | `backend\.venv\Scripts\activate`          |
| Windows (PowerShell) | `backend\.venv\Scripts\Activate.ps1`  |

### 5. Install Dependencies
With the environment active, install the required libraries:
```bash
pip install -r backend/requirements.txt
```

### 6. Run the Application
Start the FastAPI server:
```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`  
Interactive API documentation: `http://localhost:8000/docs`

---

## 🧪 Running Tests

Memorando includes comprehensive test coverage using pytest:

```bash
# Run all tests
pytest -v tests/

# Run specific test files
pytest -v tests/test_document_processor.py
pytest -v tests/test_session_api.py
pytest -v tests/test_user_and_auth.py

# Run with coverage report
pytest --cov=backend tests/
```

---

## 📁 Project Structure

```
Memorando/
├── backend/
│   ├── api/
│   │   └── study_routes.py               # FastAPI endpoints (User Auth & Study/Doc Mgmt)
│   ├── core/
│   │   ├── db_manager.py                 # Database operations (SQLite)
│   │   ├── document_processor.py         # AI document processing (Gemini API)
│   │   ├── session_manager.py            # Study session management
│   │   ├── study_methods/                # Study Method Implementations
│   │   │   ├── base_method.py            # Base class for study methods
│   │   │   └── method_read_repeat.py     # Implementation of the 'Read & Repeat' method
│   │   └── tts_engine.py                 # Local text-to-speech voice synthesis (pyttsx3)
│   ├── services/
│   │   ├── study_service.py              # Core study method logic
│   │   └── user_service.py               # User authentication and registration
│   ├── main.py                         # FastAPI application entry point
│   └── requirements.txt                # Python dependencies
├── tests/
│   ├── test_document_processor.py      # Tests for AI document parsing
│   ├── test_session_api.py             # Tests for study session API endpoints
│   ├── test_study_service.py           # Tests for core study logic
│   └── test_user_and_auth.py           # Tests for user authentication and user service
├── .github/                            # (Implied from README) CI/CD workflows
├── LICENSE                             # AGPLv3 License file
├── README.md                           # Project documentation
└── test_flow.py                        # (Additional file) Script for automation execution flow
```

---

## 🔄 API Endpoints Overview

### User Authentication
- `POST /study/register` - Register new user
- `POST /study/login` - Authenticate user

### Document Management
- `POST /study/upload-document` - Upload and process PDF with AI
- `POST /study/documents/{id}/create-sessions` - Generate study sessions
- `GET /study/documents/{id}/sessions` - List available sessions

### Study Execution
- `POST /study/start` - Start a study session
- `POST /study/stop` - Stop active session
- `GET /study/status` - Get current session status
- `GET /study/methods` - List available study methods

---

## 🔐 Security & Privacy

- User passwords are hashed using industry-standard bcrypt
- Gemini API key is stored securely in environment variables (never in code)
- All user data is stored locally in SQLite
- No telemetry or tracking in the MVP version

---

## ⚖️ Licensing

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

**Key Legal Note:** The AGPLv3 requires that anyone who modifies this software and runs it as a service over a network (for example, offering it as a paid online platform) **MUST provide the complete, corresponding source code** to their users.  

This ensures that no competitor can take the free and open code and turn it into a closed, proprietary service.  

For full details, see the [LICENSE](./LICENSE) file.

---

## 📞 Contact & Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/yourusername/Memorando/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/yourusername/Memorando/discussions)

---

## 🗺️ Roadmap

### Current Version (MVP - v0.1)
- ✅ AI-powered PDF processing with Gemini
- ✅ RESTful API with FastAPI
- ✅ SQLite database integration
- ✅ User authentication system
- ✅ Read & Repeat study method
- ✅ Comprehensive test suite
- ✅ CI/CD pipeline with GitHub Actions

### Upcoming Features
- 🔄 Web-based GUI (React)
- 🔄 Electron desktop packaging
- 🔄 Question & Answer study method
- 🔄 Progress tracking and analytics
- 🔄 Spaced repetition algorithm
- 🔄 Multi-language TTS support

### Future (Mobile & Premium)
- 📱 React Native mobile app
- ☁️ Cloud sync capabilities
- 🎯 Advanced AI-powered study methods
- 📊 Detailed learning analytics