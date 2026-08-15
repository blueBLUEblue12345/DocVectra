# DocVectra

> DocVectra is an enterprise-grade intelligent knowledge base system built on RAG (Retrieval-Augmented Generation) technology, providing precise knowledge retrieval and intelligent Q&A services for vertical domains.

## Project Overview

DocVectra targets vertical scenarios such as electronic product manuals, repair guides, and technical documentation. It transforms unstructured documents (PDF, Markdown) into searchable structured knowledge, improves retrieval accuracy through multi-path recall strategies, and delivers smooth streaming Q&A interaction experiences.

## Core Features

| Feature | Description |
|---------|-------------|
| Intelligent Document Import | Supports PDF/Markdown file upload with automatic parsing, chunking, and vectorization |
| Hybrid Vector Retrieval | Dense vector + sparse vector (BM25) hybrid retrieval |
| Multi-Path Recall Fusion | Vector retrieval + HyDE + Web search |
| Intelligent Reranking | Reranker model reranking with cliff detection and dynamic truncation |
| Streaming Q&A | SSE real-time push with character-by-character output |
| Conversation History Management | MongoDB storage for dialogue history, supporting contextual continuous conversations |

## System Architecture

| Module | Responsibility | Technology |
|--------|----------------|------------|
| **API Layer** | HTTP interface exposure, request routing | FastAPI + Uvicorn |
| **Processor Layer** | Business process orchestration, node scheduling | LangGraph |
| **Utils Layer** | Utility function encapsulation, external service calls | Python modules |
| **Data Layer** | Data persistence and retrieval | Milvus / MongoDB / MinIO |

## Project Structure

```
knowledge_base/
├── processor/
│   ├── import_processor/    # Document import workflow
│   │   ├── nodes/           # Workflow nodes
│   │   │   ├── node_pdf_to_md.py          # PDF to Markdown conversion
│   │   │   ├── node_md_img.py             # Markdown image processing
│   │   │   ├── node_document_split.py     # Intelligent document chunking
│   │   │   ├── node_bge_embedding.py      # BGE vectorization
│   │   │   ├── node_item_name_recognition.py  # Product name recognition
│   │   │   └── node_import_milvus.py      # Milvus data import
│   │   ├── config.py        # Configuration management
│   │   ├── state.py         # State definitions
│   │   └── main_graph.py    # LangGraph main graph
│   └── query_processor/     # Query retrieval workflow
│       ├── nodes/           # Workflow nodes
│       │   ├── node_search_embedding.py       # Vector retrieval
│       │   ├── node_search_embedding_hyde.py  # HyDE retrieval
│       │   ├── node_web_search_mcp.py         # MCP web search
│       │   ├── node_rrf.py                    # RRF fusion
│       │   ├── node_rerank.py                 # Reranking
│       │   ├── node_item_name_confirm.py      # Product name confirmation
│       │   └── node_answer_output.py          # Answer generation
│       └── main_graph.py    # LangGraph main graph
├── utils/                   # Utility modules (Milvus/MinIO/Embedding)
├── tools/                   # Helper scripts
├── .env.example             # Environment variable template
└── pyproject.toml           # Project configuration
```

## Core Workflows

### Document Import

```
PDF/Document → MinerU Parsing → Markdown Image Processing → Document Chunking → BGE Vectorization → Product Name Recognition → Milvus Import
```

### Query Retrieval

```
User Query → Product Name Confirmation → Vector Retrieval (Dense+Sparse) → HyDE Expansion → MCP Web Search → RRF Fusion → Rerank Reranking → Streaming Answer Generation
```

## Technology Stack

| Category | Technology | Description |
|----------|------------|-------------|
| Backend Framework | FastAPI + Uvicorn | Asynchronous high-performance HTTP service |
| Workflow Engine | LangGraph | Stateful graph orchestration framework |
| Large Language Model | Alibaba Cloud DashScope (Qwen) | qwen-flash / qwen3-vl-flash |
| Vector Embedding | OpenAI text-embedding-v4 + BGE-M3 | 1536-dim dense + 1024-dim sparse |
| Reranking Model | BGE-Reranker-Large | Local deployment |
| Vector Database | Milvus | Hybrid retrieval (dense + sparse) |
| Document Database | MongoDB | Conversation history storage |
| Object Storage | MinIO | File and image storage |
| PDF Parsing | MinerU | PDF to Markdown conversion |

## Quick Start

### 1. System Requirements

#### Hardware Requirements
- **GPU**: NVIDIA GPU (RTX 3060 or higher recommended, VRAM ≥ 6GB) for local Embedding and Reranker model inference
- **Memory**: ≥ 16GB RAM
- **Disk**: ≥ 50GB free space (for model cache and vector database)

#### Software Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), macOS
- **Python**: >= 3.11
- **CUDA**: 12.x (for GPU acceleration)
- **Node.js**: >= 18 (for frontend development)
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (recommended Python package manager)

### 2. Required Services

Before starting the project, ensure the following services are installed and running:

#### 2.1 Milvus (Vector Database)
```bash
# Start Milvus using Docker
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:v2.4.0
```
Verify: Visit http://localhost:9091 to check Milvus status

#### 2.2 MongoDB (Document Database)
```bash
# Start MongoDB using Docker
docker run -d --name mongodb \
  -p 27017:27017 \
  mongo:7.0
```
Verify: Connect using MongoDB Compass at `mongodb://localhost:27017`

#### 2.3 MinIO (Object Storage)
```bash
# Start MinIO using Docker
docker run -d --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```
Verify: Visit http://localhost:9001 (username/password: minioadmin/minioadmin)

#### 2.4 Redis (Task State Storage)
```bash
# Start Redis using Docker
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine
```
Verify: `redis-cli ping` should return `PONG`

### 3. Install Dependencies

#### 3.1 Install uv (Python Package Manager)
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 3.2 Install Python Dependencies
```bash
# Clone the project
git clone <your-repo-url>
cd DocVectra

# Create virtual environment and install dependencies
uv sync
```

#### 3.3 Download Local Models
The project requires downloading the following models locally:

```bash
# Download BGE-M3 Embedding model (approximately 2GB)
python tools/download_bgem3.py

# Or download using ModelScope
# Models will be automatically cached to the directory specified by MODELSCOPE_CACHE
```

### 4. Configure Environment Variables

```bash
# Copy environment variable template
cp .env.example .env
```

Edit the `.env` file and configure the following key items:

#### 4.1 LLM API Configuration
```bash
# Alibaba Cloud DashScope API Key (required)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# API base URL (default: Alibaba Cloud DashScope)
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# Model selection
LLM_DEFAULT_MODEL=qwen-flash          # Text generation model
VL_MODEL=qwen3-vl-flash               # Vision-language model (for image understanding)
ITEM_MODEL=qwen-flash                 # Product name recognition model
```

#### 4.2 Database Connection Configuration
```bash
# Milvus configuration
MILVUS_URL=http://localhost:19530
CHUNKS_COLLECTION=kb_chunks
ITEM_NAME_COLLECTION=kb_item_names

# MongoDB configuration
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=kb001

# MinIO configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=knowledge-base

# Redis configuration
REDIS_URL=redis://localhost:6379/0
```

#### 4.3 Model Path Configuration
```bash
# BGE-M3 model path (modify according to actual download path)
BGE_M3_PATH=/path/to/your/models/BAAI/bge-m3
BGE_M3=BAAI/bge-m3

# BGE Reranker model path
BGE_RERANKER_LARGE=/path/to/your/models/BAAI/bge-reranker-large

# GPU device configuration
BGE_DEVICE=cuda:0                     # Use GPU 0
BGE_FP16=True                         # Enable half-precision acceleration
BGE_RERANKER_DEVICE=cuda:0
BGE_RERANKER_FP16=1
```

#### 4.4 MinerU API Configuration (PDF Parsing)
```bash
# MinerU API Token (apply at: https://mineru.net)
MINERU_API_TOKEN=your-mineru-api-token
MINERU_BASE_URL=https://mineru.net/api/v4
```

#### 4.5 MCP Web Search Configuration
```bash
# Alibaba Cloud DashScope MCP Web Search service
MCP_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse
```

### 5. Start Services

#### 5.1 Start Backend Services

**Method 1: Unified Entry Point (Recommended)**
```bash
# Start unified backend service (includes import and query APIs)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Method 2: Start Separately**
```bash
# Terminal 1: Start import service
uvicorn backend.api.import_service:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start query service
uvicorn backend.api.query_service:app --host 0.0.0.0 --port 8001 --reload
```

Verify backend services:
- Import API documentation: http://localhost:8000/docs
- Query API documentation: http://localhost:8001/docs (if started separately)
- Health check: `curl http://localhost:8000/health`

#### 5.2 Start Frontend Service

```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit: http://localhost:3000

#### 5.3 Production Deployment

```bash
# Backend production deployment
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend build
cd frontend
npm run build

# Use Nginx to host frontend static files
# Configure reverse proxy to backend API
```

### 6. Verify Deployment

#### 6.1 Check Service Status
```bash
# Check backend service
curl http://localhost:8000/health

# Check Milvus
curl http://localhost:9091

# Check MongoDB
mongosh --eval "db.runCommand({ ping: 1 })"

# Check Redis
redis-cli ping
```

#### 6.2 Test APIs
```bash
# Test file upload
curl -X POST http://localhost:8000/import/upload \
  -F "files=@test.pdf"

# Test query
curl -X POST http://localhost:8000/query/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test question", "session_id": "test-001"}'
```

### 7. Troubleshooting

#### Q1: Insufficient GPU Memory
```bash
# Modify .env, disable half-precision or switch to CPU
BGE_FP16=False
BGE_DEVICE=cpu
BGE_RERANKER_FP16=0
BGE_RERANKER_DEVICE=cpu
```

#### Q2: Model Download Failed
```bash
# Use ModelScope mirror
export MODELSCOPE_CACHE=/your/cache/path
python tools/download_bgem3.py
```

#### Q3: MinIO Connection Timeout
- Check if MinIO service is running: `docker ps | grep minio`
- Check if firewall allows port 9000
- Verify credentials: Visit http://localhost:9001 to login

#### Q4: Milvus Connection Failed
```bash
# Restart Milvus
docker restart milvus-standalone

# View logs
docker logs milvus-standalone
```

#### Q5: Redis Connection Failed
```bash
# Check Redis service
docker ps | grep redis

# Test connection
redis-cli -h localhost -p 6379 ping
```

## License

MIT
