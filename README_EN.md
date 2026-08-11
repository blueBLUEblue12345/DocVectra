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

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file with your actual API keys, database connections, and other configurations.

### 3. Start the Service

```bash
# TODO: Add startup command
```

## Requirements

- Python >= 3.11
- Milvus >= 2.4
- MongoDB >= 6.0
- MinIO
- CUDA (for local Embedding model inference)

## License

MIT
