# SmartPrep AI 🎓

> An AI-powered academic intelligence platform that transforms your study materials into an interactive learning companion — powered entirely by local AI.

Upload your textbooks, notes, and question papers. Chat with your content, generate smart notes, take quizzes, analyze exam patterns, and build study plans — all running locally on your machine with Llama 3.2.

---

## ✨ Features

### 📚 Course Management
- Create, rename, and delete academic courses
- Organize all your materials by subject

### 📄 Smart Document Repository
- Upload PDFs, DOCX, PPTX, and TXT files (up to 50 MB)
- Automatic text extraction with OCR for scanned documents
- SHA-256 exact duplicate detection + TF-IDF near-duplicate detection (90% threshold)
- Background processing with real-time progress indicator
- Processing status tracking (processing → ready → failed with retry)

### 💬 AI Chat (RAG)
- Ask questions about your uploaded materials and get cited answers
- Retrieval-Augmented Generation using ChromaDB vector search
- Multi-turn conversation context (retains last 10 exchanges)
- Source citations with document name, category, and page number
- **General knowledge fallback** — if the answer isn't in your materials, the AI asks if you'd like a general answer

### 📝 Smart Notes Generator
- **Short Summary** — condensed overview (≤ 300 words)
- **Detailed Summary** — organized under section headings
- **Revision Notes** — bullet points (≤ 30 words each)
- **Formula Sheet** — one formula per line with labels
- Source citations per section

### 🧠 Quiz Generator
- **MCQ** — 4 options, per-option explanations, auto-scoring
- **Short Answer / Viva** — with model answers
- **Long Answer** — with structured outline answers
- **Mixed Test (All-in-One)** — configurable combo of all types
- 50/50 sourcing split between Question Papers and Textbook/Notes
- Insufficient content handling with reduced question sets

### 📈 Performance Tracking
- Score history over time (area chart)
- Average score per topic (bar chart)
- Total quizzes taken, average score, best score stats
- Full quiz review — view past attempts with your answers and correct answers

### 📊 Exam Analyzer
- Topic frequency extraction from Question Papers using AI
- Chapter weightage visualization (bar charts)
- Year-over-year trend analysis (requires 3+ year-distinct papers)
- OCR support for scanned question papers

### 📅 Study Planner
- Day-by-day study schedule generation
- Exam date, daily hours (0.5–24h in 0.5 increments), up to 50 topics
- Revision day insertion (1 per every 5 study days)
- Condensed last-minute plans (< 2 days to exam)
- Optional frequency-weighted topic distribution

### 🎨 User Experience
- Light/Dark mode toggle with persistence
- Animated upload progress bar with percentage
- Auto-polling document status (refreshes every 5 seconds)
- Responsive design with smooth Framer Motion animations
- Professional UI with Tailwind CSS

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS |
| **UI/UX** | Framer Motion, Recharts, Lucide Icons |
| **Backend** | FastAPI (Python 3.11+), Uvicorn, Pydantic v2 |
| **LLM** | Llama 3.2 (3B, Q4_K_M) via Ollama — fully local |
| **Embeddings** | nomic-embed-text (768-dim) via Ollama |
| **Vector Database** | ChromaDB (persistent, cosine similarity) |
| **Database** | SQLite (WAL mode) with migrations |
| **Text Extraction** | pdfplumber, python-docx, python-pptx, pytesseract (OCR) |
| **Chunking** | LangChain RecursiveCharacterTextSplitter (512 tokens, 64 overlap) |
| **NLP** | scikit-learn TF-IDF + cosine similarity (duplicate detection) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                         │
│                  http://localhost:3000                         │
│  ┌─────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌───────┐ ┌──────┐│
│  │ Courses │ │ Docs │ │ Chat │ │Notes │ │ Quiz  │ │Planner││
│  └─────────┘ └──────┘ └──────┘ └──────┘ └───────┘ └──────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                          │
│                  http://localhost:8000                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ API Routers  │ │   Services   │ │  Processor Pipeline  │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└────────┬──────────────────┬───────────────────┬─────────────┘
         │                  │                   │
    ┌────▼────┐      ┌─────▼─────┐      ┌─────▼─────┐
    │ SQLite  │      │ ChromaDB  │      │  Ollama   │
    │metadata │      │  vectors  │      │ Llama 3.2 │
    └─────────┘      └───────────┘      └───────────┘
                                     http://localhost:11434
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com/download)

### Option 1: One-Click (Windows)

```bash
# First time only:
setup.bat

# Every time you want to use it:
start.bat
```

### Option 2: Manual Setup

```bash
# 1. Start Ollama and pull models
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text

# 2. Backend (Terminal 1)
cd backend
pip install -r requirements.txt
npm run dev
# → http://localhost:8000

# 3. Frontend (Terminal 2)
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## 📁 Project Structure

```
CampusGPT/
├── backend/
│   ├── app/
│   │   ├── routers/        # API endpoints (courses, documents, chat, notes, quiz, exam, planner)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── config.py       # Environment configuration
│   │   ├── dependencies.py # Dependency injection
│   │   └── main.py         # FastAPI app entry point
│   ├── src/
│   │   ├── course_service.py
│   │   ├── document_service.py
│   │   ├── duplicate_detector.py
│   │   ├── processor_pipeline.py
│   │   ├── rag_engine.py
│   │   ├── notes_generator.py
│   │   ├── quiz_generator.py
│   │   ├── exam_analyzer.py
│   │   ├── study_planner.py
│   │   ├── error_handler.py
│   │   ├── database.py
│   │   └── models.py
│   ├── tests/              # Unit + property-based tests (Hypothesis)
│   ├── requirements.txt
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # Reusable UI (charts, layout, features)
│   │   ├── lib/            # API client, theme provider, utilities
│   │   └── styles/         # Tailwind globals
│   └── package.json
├── setup.bat               # First-time installer (Windows)
├── start.bat               # One-click launcher
├── stop.bat                # Kill all services
├── .gitignore
├── LICENSE
├── package.json            # Root convenience scripts
└── README.md
```

---

## 🔌 API Documentation

With the backend running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses/` | List all courses |
| POST | `/api/courses/` | Create a course |
| POST | `/api/documents/{course_id}/upload` | Upload a document |
| POST | `/api/chat/{course_id}/query` | RAG chat query |
| POST | `/api/chat/{course_id}/general` | General knowledge answer |
| POST | `/api/notes/{course_id}/generate` | Generate notes |
| POST | `/api/quiz/{course_id}/generate` | Generate quiz |
| POST | `/api/quiz/score` | Score an MCQ quiz |
| POST | `/api/exam/{course_id}/analyze` | Analyze exam patterns |
| POST | `/api/planner/generate` | Generate study plan |
| GET | `/api/quiz/{course_id}/attempts` | Quiz attempt history |

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `CHAT_MODEL` | `llama3.2` | LLM for text generation |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Model for vector embeddings |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | Backend API URL |

---

## 🧪 Testing

```bash
cd backend
pytest --tb=short -q
```

Includes unit tests, property-based tests (Hypothesis), and integration tests.

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

Built with ❤️ for students who want to study smarter, not harder.
