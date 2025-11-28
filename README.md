# Marketing AI Assistant
A comprehensive AI-powered marketing campaign generator that helps businesses create data-driven marketing strategies through interactive conversations.  
Built with **Next.js** (frontend) and **FastAPI** (backend), powered by **Ollama** for local AI inference.

## 🚀 Features
### Core Capabilities
- Interactive Conversation Flow
- User Context Understanding
- Real-time Web Search
- Campaign Generation
- Early Exit Option

### Campaign Deliverables
- Strategy Overview
- Ad Copy
- Email Drafts
- Social Media Content
- Content Calendar
- Key Messaging

### Technical Features
- Real-time web integration
- PDF export
- Responsive UI
- Context-aware state management
- Robust error handling

## 🛠️ Tech Stack
### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- Axios
- Lucide React
- jsPDF

### Backend
- FastAPI
- Ollama
- Pydantic
- Serper API
- Uvicorn

## 📦 Installation
### Prerequisites
- Python 3.8+
- Node.js 18+
- Ollama installed
- Serper API key (optional)

## Backend Setup
### 1. Clone & install
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
Create `backend/.env`

### 3. Start Ollama
```bash
ollama serve
ollama pull llama2
```

### 4. Run backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open: http://localhost:3000

## 🎯 Usage
- Guided context collection
- Early generation via `"generate campaign now"`
- Optional web search
- Multi-variation content generation
- PDF export

## 🔧 API Endpoints
- POST /chat
- POST /campaign/generate-now
- POST /search/enhance-context
- POST /conversation/{user_id}/reset
- GET /conversation/{user_id}/context
- GET /health
- GET /config
- GET /

## 🏗️ Project Structure
```
marketing-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── services.py
│   │   └── config.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── app/
    ├── package.json
    └── tailwind.config.js
```

## 🔍 How It Works
- Context collection → Insight gathering → Campaign generation
- Uses Ollama for local inference
- Context-aware system prompts
- Robust fallback & error handling

## ⚙️ Configuration
- Ollama model, temperature, tokens
- Serper API settings
- Conversation state management

## 🚨 Error Handling
- Web search fallbacks
- JSON parsing recovery
- Session restoration
- Input validation

## 📊 Performance
- Caching
- Async operations
- Health checks
- Logs & analytics

## 🔒 Security
- No data persistence
- Sanitized inputs
- CORS control
- API key security

## 🧪 Testing
### Backend
```bash
pytest tests/
```
### Frontend
```bash
npm test
```

## 🚀 Deployment
### Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
### Frontend
```bash
npm run build
npm start
```

## 🤝 Contributing
- Fork → Branch → Implement → PR
- PEP8, TypeScript, ESLint, docs

## 📝 License
MIT License

## 🙏 Acknowledgments
- Ollama
- FastAPI
- Next.js
- Serper API


Set the environment variable in your terminal before running your Python script:

On Linux/macOS:

bash
export FAL_KEY="your-api-key-here"
On Windows (Command Prompt):

cmd
set FAL_KEY=your-api-key-here
On Windows (PowerShell):

powershell
$env:FAL_KEY="your-api-key-here"