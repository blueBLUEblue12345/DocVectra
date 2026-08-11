# DocVectra

> DocVectra是一个企业级智能知识库系统，基于 RAG（检索增强生成）技术，为垂直领域提供精准的知识检索与智能问答服务。

## 项目定位

DocVectra面向电子产品手册、维修指南、技术文档等垂直场景，将非结构化文档（PDF、Markdown）转化为可检索的结构化知识，通过多路召回策略提升检索准确率，提供流畅的流式问答交互体验。

## 核心功能

| 功能 | 描述 |
|------|------|
| 文档智能导入 | 支持 PDF/Markdown 文件上传，自动解析、切分、向量化 |
| 混合向量检索 | 稠密向量 + 稀疏向量（BM25）混合检索 |
| 多路召回融合 | 向量检索 + HyDE + Web 搜索 |
| 智能重排序 | Reranker 模型重排序，断崖检测动态截断 |
| 流式问答 | SSE 实时推送，逐字输出答案 |
| 会话历史管理 | MongoDB 存储对话历史，支持上下文连续对话 |

## 系统架构

| 模块 | 职责 | 技术实现 |
|------|------|----------|
| **API 层** | HTTP 接口暴露、请求路由 | FastAPI + Uvicorn |
| **Processor 层** | 业务流程编排、节点调度 | LangGraph |
| **Utils 层** | 工具函数封装、外部服务调用 | Python 模块 |
| **数据层** | 数据持久化、检索 | Milvus / MongoDB / MinIO |

## 项目结构

```
knowledge_base/
├── processor/
│   ├── import_processor/    # 文档导入流程
│   │   ├── nodes/           # 工作流节点
│   │   │   ├── node_pdf_to_md.py          # PDF 转 Markdown
│   │   │   ├── node_md_img.py             # Markdown 图片处理
│   │   │   ├── node_document_split.py     # 文档智能切片
│   │   │   ├── node_bge_embedding.py      # BGE 向量化
│   │   │   ├── node_item_name_recognition.py  # 商品名识别
│   │   │   └── node_import_milvus.py      # Milvus 入库
│   │   ├── config.py        # 配置管理
│   │   ├── state.py         # 状态定义
│   │   └── main_graph.py    # LangGraph 主图
│   └── query_processor/     # 查询检索流程
│       ├── nodes/           # 工作流节点
│       │   ├── node_search_embedding.py       # 向量检索
│       │   ├── node_search_embedding_hyde.py  # HyDE 检索
│       │   ├── node_web_search_mcp.py         # MCP 联网搜索
│       │   ├── node_rrf.py                    # RRF 融合
│       │   ├── node_rerank.py                 # 重排序
│       │   ├── node_item_name_confirm.py      # 商品名确认
│       │   └── node_answer_output.py          # 答案生成
│       └── main_graph.py    # LangGraph 主图
├── utils/                   # 工具模块（Milvus/MinIO/Embedding）
├── tools/                   # 辅助脚本
├── .env.example             # 环境变量示例
└── pyproject.toml           # 项目配置
```

## 核心流程

### 文档导入

```
PDF/文档 → MinerU 解析 → Markdown 图片处理 → 文档智能切片 → BGE 向量化 → 商品名识别 → Milvus 入库
```

### 查询检索

```
用户提问 → 商品名确认 → 向量检索(稠密+稀疏) → HyDE 扩展 → MCP Web 搜索 → RRF 融合 → Rerank 重排序 → 流式生成回答
```

## 技术栈

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI + Uvicorn | 异步高性能 HTTP 服务 |
| 工作流引擎 | LangGraph | 有状态图编排框架 |
| 大语言模型 | 阿里云 DashScope (Qwen) | qwen-flash / qwen3-vl-flash |
| 向量嵌入 | OpenAI text-embedding-v4 + BGE-M3 | 1536维稠密 + 1024维稀疏 |
| 重排序模型 | BGE-Reranker-Large | 本地部署 |
| 向量数据库 | Milvus | 混合检索（稠密+稀疏） |
| 文档数据库 | MongoDB | 对话历史存储 |
| 对象存储 | MinIO | 文件与图片存储 |
| PDF 解析 | MinerU | PDF 转 Markdown |

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写实际的 API 密钥、数据库连接等信息。

### 3. 启动服务

```bash
# TODO: 补充启动命令
```

## 环境要求

- Python >= 3.11
- Milvus >= 2.4
- MongoDB >= 6.0
- MinIO
- CUDA（用于本地 Embedding 模型推理）

## License

MIT
