# 🧠 Memorando: The Smart Study Companion

## 🌟 Quick Overview
**Memorando** is a desktop application designed to transform passive reading of PDF documents into active, guided study sessions.  
By leveraging **Text-to-Speech (TTS)** technology and structured memorization techniques, it helps users achieve deeper learning and better information retention.

This initial version is a **Minimal Viable Product (MVP)**, entirely free, built to validate the core concept, test the architecture, and collect critical usage data (analytics) before scaling to a commercial mobile version.

---

## 🎯 Our Goals

### 1. Portfolio Showcase (Open Source & AGPLv3)
The core logic of the free desktop MVP is licensed under the **AGPLv3 (Affero General Public License)**.  
This strategy achieves two key objectives:

- **Career Advancement**: A high-quality portfolio piece demonstrating robust, scalable Python architecture, domain expertise (document processing), and clean coding practices.  
- **Legal Protection**: AGPLv3 safeguards the project against competitors attempting to copy the free code and turn it into a closed, paid service.

### 2. Business Validation & Future Growth
The MVP serves as a **data-gathering tool**. We aim to measure user engagement and method preference to inform the decision to secure funding for the next phase:

- **Mobile Port**: iOS and Android versions (likely using React Native).  
- **Premium Features**: Proprietary memorization algorithms and cloud-based features (kept private and protected).

---

## 🛠️ Technology Stack (Current MVP)

| **Component**     | **Technology**   | **Purpose**                                                                 |
|--------------------|------------------|-------------------------------------------------------------------------------|
| Backend / Logic    | Python           | Handles text extraction, segmentation, study method logic, and TTS engine.    |
| GUI (Planned)      | Electron + React | Package the web interface into a cross-platform desktop app (Windows/Mac/Linux). |
| Core Functions     | PyPDF2, pyttsx3  | Local PDF processing and TTS voice functions.                                 |

---

## 📚 Study Methods Implemented (CLI)

- **Read & Repeat**: Reads a segment, pauses for user repetition, and repeats the segment for reinforcement.  
- **Question & Answer (Flashcards)**: Splits text into simulated Q&A pairs; reads the question, waits for user input, then reveals the answer.

---

## 🚀 Getting Started (CLI)

The application currently runs entirely from the terminal, making it easy to test the core logic.

### 1. Setup Virtual Environment
Run from the project root:

```bash
python3 -m venv backend/.venv
```

### 2. Activate the Environment

| Operating System | Command                                   |
|------------------|-------------------------------------------|
| Linux / macOS    | `source backend/.venv/bin/activate`       |
| Windows (CMD)    | `backend\.venv\Scripts\activate`          |

### 3. Install Dependencies
With the environment active, install the required libraries:

```bash
pip install -r backend/requirements.txt
```

### 4. Run the Application
Start the program:

```bash
python backend/main.py
```

Follow the prompts in the terminal to load a PDF and select a study method.

## ⚖️ Licensing

This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.

**Key Legal Note:** The AGPLv3 requires that anyone who modifies this software and runs it as a service over a network (for example, offering it as a paid online platform) **MUST provide the complete, corresponding source code** to their users.  

This ensures that no competitor can take the free and open code and turn it into a closed, proprietary service.  

For full details, see the [LICENSE](./LICENSE) file.
