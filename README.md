# Cognitive-Engine-V1
A high-performance cognitive search engine utilizing autonomous multi-agent ingestion, hybrid vector embeddings, and a Retrieval-Augmented Generation (RAG) pipeline.

<div align="center">
  <img src="https://img.icons8.com/external-solid-line-colors-kendis-lasman/128/external-brain-artificial-intelligence-solid-line-colors-kendis-lasman.png" alt="Brain Icon" width="80" />
  
  # 🧠 The Founder's Oracle
  **Enterprise-Grade Cognitive Search & Neural RAG Engine**

  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#)
  [![Next.js](https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](#)
  [![Pinecone](https://img.shields.io/badge/Pinecone_v2-000000?style=for-the-badge&logo=pinecone&logoColor=white)](#)
  [![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](#)
  
  *A high-velocity, precision-recall architecture trained on the collective wisdom of Y Combinator's Paul Graham.*
</div>

---

## 🚀 Overview

The Founder's Oracle is a full-stack, streaming Retrieval-Augmented Generation (RAG) application. Moving beyond "naive" RAG, this engine employs a **Two-Stage Precision Retrieval System** (Bi-Encoder broad recall + Cross-Encoder precision reranking) to eliminate hallucinations and deliver hyper-accurate, context-aware syntheses in real-time.

### ⚡ Peak Capabilities
* **Zero-Latency Perceived Streaming:** Implements Server-Sent Events (SSE) with Deferred Execution to bypass Time-To-First-Byte (TTFB) blocks, yielding instantaneous UI updates.
* **Neural Reranking:** Utilizes `ms-marco-MiniLM-L-12-v2` via FlashRank to mathematically verify and re-score vector matches before LLM synthesis.
* **Autonomous Ingestion Swarm:** Custom Scrapy spiders capable of dynamically traversing and extracting data from nested web directories.
* **Asynchronous React UI:** A ChatGPT-style, dark-mode Next.js interface featuring interactive metadata citation chips and hydration-safe rendering.

---

## 🏗️ System Architecture

The infrastructure is decoupled into an asynchronous data ingestion pipeline and a highly concurrent live serving environment.

```mermaid
graph TB
    classDef frontend fill:#0f172a,stroke:#6366f1,stroke-width:2px,color:#fff;
    classDef backend fill:#1e1e1e,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef db fill:#020617,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef ai fill:#4c1d95,stroke:#a855f7,stroke-width:2px,color:#fff;
    classDef crawler fill:#3f3f46,stroke:#f59e0b,stroke-width:2px,color:#fff;

    User((User)) -->|Natural Language| UI[Next.js App Router\nStreaming Chat UI]:::frontend
    UI -->|Event-Stream Request| API[FastAPI Server\nCognitive Core]:::backend

    subgraph "Phase 1: Knowledge Ingestion (Offline)"
        Spider[Scrapy Agents]:::crawler -->|Traverse & Extract| RawData[(Raw JSON\nPG Essays)]:::crawler
        RawData -->|T4 GPU Colab| Embedding[BAAI/bge-base-en-v1.5\nBi-Encoder]:::ai
        Embedding -->|768-Dimension Upsert| VectorDB[(Pinecone Cloud\ncognitive-core-v2)]:::db
    end

    subgraph "Phase 2: Live Inference (Real-Time)"
        API -->|1. Vectorize Query| EmbedQuery[Local BAAI Model]:::ai
        EmbedQuery -->|2. Broad Recall| VectorDB
        VectorDB -->|3. Top 15 Vectors| Reranker[FlashRank / MiniLM\nCross-Encoder]:::ai
        Reranker -->|4. Top 5 Precision Context| API
        API -->|5. Prompt Synthesis| Gemini[Google Gemini 2.5 Flash]:::ai
        Gemini -->|6. Token Stream| API
    end

    API -->|Multipart SSE Stream\nMetadata + Text| UI

## 🛠️ Tech Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | `Next.js 14`, `React`, `Tailwind CSS` | Async client, UI styling, Markdown parsing |
| **Backend API** | `FastAPI`, `Uvicorn`, `Python 3` | High-concurrency routing, SSE Streaming |
| **Generative AI**| `Google GenAI SDK`, `Gemini 2.5 Flash` | Ultra-fast token synthesis & reasoning |
| **Vector DB** | `Pinecone Serverless` | High-dimensional semantic storage (Cloud) |
| **Neural Search**| `SentenceTransformers`, `FlashRank` | BAAI Embeddings & Cross-Encoder Reranking |
| **Ingestion** | `Scrapy`, `Google Colab (T4 GPU)` | Autonomous web crawling & mass vectorization |

## ⚙️ Local Development & Ignition

### 1. The Secure Vault
Create a `.env` file in the root directory and inject your cryptographic keys:
```env
PINECONE_API_KEY=your_pinecone_key_here
GEMINI_API_KEY=your_gemini_key_here
HF_TOKEN=your_huggingface_read_token_here

2. Booting the Neural Core (Backend)
Open Terminal 1, activate your virtual environment, and ignite the FastAPI server:

Bash
source venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
Wait for the 🚀 Igniting Neural Cores... sequence to complete and bind to Port 8000.

3. Booting the UI (Frontend)
Open Terminal 2, navigate to the React directory, and start the development server:

Bash
cd web-frontend
npm install
npm run dev
Navigate to http://localhost:3000 (or your active Codespace port) to access the Oracle.

🗺️ Roadmap / Future Expeditions
[x] Vertical Slice: Vector Matching & Generation

[x] Enterprise Architecture: Streamlit -> Next.js Migration

[x] Peak Optimization: Streaming SSE & Neural Reranking

[ ] Deployment: Containerize & deploy to Render (Backend) and Vercel (Frontend).

[ ] Data Expansion: Deploy new Spiders to ingest SEC filings, scientific journals, and financial datasets.

[ ] Memory Integration: Implement Redis-backed conversation history for multi-turn contextual awareness.

"Startups are so counterintuitive that if you trust your instincts, you'll make a lot of mistakes." — Paul Graham

<div align="center">
<sub>Built with precision. Designed for scale.</sub>
</div>