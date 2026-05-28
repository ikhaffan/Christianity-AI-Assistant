# Christianity-Focused AI Assistant

A grounded, safe AI assistant for Christianity-related questions with RAG-based scripture citations, Christian image generation, and robust safety measures.

## Features

- **Scripture-Aware Responses**: Answers grounded in Biblical text with verse citations
- **Bible Verse Grounding**: RAG pipeline ensures accurate scripture references
- **Christian Image Generation**: Generate Christian-themed imagery with content safety
- **Conversation Memory**: Multi-turn conversations with context retention
- **Denomination Awareness**: Handles Catholic, Protestant, Orthodox perspectives
- **Safety & Moderation**: Filters adversarial prompts, prevents hallucinations
- **Graceful Edge-Case Handling**: Handles fake verses, contradictory prompts, and manipulation attempts

## Architecture

```
User → Streamlit UI → FastAPI Backend → LLM Orchestration Layer
                                         ├── RAG Pipeline (Bible/Theology)
                                         ├── Moderation/Safety Layer
                                         ├── Image Generation Service
                                         └── Conversation Memory
```

## Tech Stack

- **Backend**: FastAPI + Python
- **LLM**: OpenAI GPT-4
- **Vector DB**: ChromaDB
- **Embeddings**: OpenAI text-embedding-3-small
- **Image Generation**: DALL-E 3
- **UI**: Streamlit

## Quick Start

### 1. Install Dependencies

```bash
cd christian-ai-assistant
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Initialize Bible Database

```bash
python -m app.scripts.init_bible_db
```

### 4. Run the Application

**Option A: Streamlit UI (Recommended)**
```bash
streamlit run ui/streamlit_app.py
```

**Option B: FastAPI Backend**
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
christian-ai-assistant/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── routes/
│   │   ├── chat.py          # Chat endpoints
│   │   └── image.py         # Image generation endpoints
│   ├── services/
│   │   ├── rag_service.py   # RAG pipeline
│   │   ├── llm_service.py   # LLM orchestration
│   │   ├── moderation.py    # Safety & moderation
│   │   ├── image_gen.py     # Image generation
│   │   └── memory.py        # Conversation memory
│   ├── prompts/
│   │   ├── system.py        # System prompts
│   │   └── safety.py        # Safety prompts
│   └── scripts/
│       └── init_bible_db.py # Database initialization
├── data/
│   ├── bible/               # Bible text data
│   └── chroma_db/           # Vector database (generated)
├── evaluation/
│   ├── test_cases.json      # Standard test cases
│   ├── adversarial.json     # Adversarial prompts
│   └── hallucination.json   # Hallucination tests
├── ui/
│   └── streamlit_app.py     # Chat interface
├── docs/
│   └── architecture.md      # Architecture documentation
├── requirements.txt
├── .env.example
└── README.md
```

## Safety Features

### Hallucination Prevention
- All scripture references are retrieved from the vector database
- Verse validation ensures cited verses actually exist
- System prompts explicitly instruct against fabricating verses

### Adversarial Prompt Handling
- Pattern detection for manipulation attempts
- Content filtering for hateful/extreme prompts
- Graceful refusal responses for policy violations

### Denomination Awareness
- Detects denominational context from queries
- Presents balanced perspectives when differences exist
- Avoids favoring one theological position

## Evaluation

Run the evaluation suite:

```bash
python -m app.scripts.run_evaluation
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send a message and get a response |
| `/chat/history/{session_id}` | GET | Get conversation history |
| `/image/generate` | POST | Generate Christian-themed image |
| `/health` | GET | Health check |

## License

MIT License
