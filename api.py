import os
import json
from dotenv import load_dotenv

# 0. Load Vault FIRST (Crucial for Hugging Face Authentication)
load_dotenv()
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["TOKENIZERS_PARALLELISM"] = "false" # Silences a multiprocessing warning

# Now we import the heavy libraries after the environment is prepped
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- NEW IMPORT
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from google import genai
from flashrank import Ranker, RerankRequest
from fastapi.responses import StreamingResponse

app = FastAPI(title="Cognitive Engine ULTRA", version="6.0")

# --- NEW SECURITY CONFIGURATION (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Next.js frontend to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------

# 1. High-Performance Infrastructure
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")
ai_client = genai.Client()

# 2. Hot-Loading Neural Cores
print("🚀 Igniting Neural Cores (Embedding + Reranker)...")
model = SentenceTransformer('BAAI/bge-base-en-v1.5')
ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp")

class SearchQuery(BaseModel):
    text: str
    top_k: int = 5

# 3. Precision Logic (Vector Recall -> Neural Precision)
def get_refined_context(query_text: str):
    # A. Broad Recall
    query_vector = model.encode(query_text).tolist()
    pinecone_response = index.query(vector=query_vector, top_k=15, include_metadata=True)
    
    # B. Precision Reranking
    passages = []
    for match in pinecone_response['matches']:
        passages.append({
            "id": match['id'],
            "text": match['metadata']['content'],
            "meta": match['metadata']
        })
    
    rerank_request = RerankRequest(query=query_text, passages=passages)
    reranked_results = ranker.rerank(rerank_request)
    
    # C. Formatting
    top_context = "\n\n".join([r['text'] for r in reranked_results[:5]])
    
    clean_sources = []
    for r in reranked_results[:3]: # Extract top 3 for UI
        clean_sources.append({
            "title": r['meta'].get('title', 'Oracle Essay'),
            "author": r['meta'].get('author', 'Paul Graham'),
            "score": round(float(r['score']), 3),
            "url": r['meta'].get('source_url', '#')
        })
        
    return top_context, clean_sources

@app.post("/ask_stream")
async def ask_stream(query: SearchQuery):
    
    # DEFERRED EXECUTION: We move the intelligence INSIDE the stream generator
    def generate_events():
        # 1. The stream opens instantly, allowing the UI to show "Reranking..."
        # Now we do the heavy lifting while the connection is live
        context, sources = get_refined_context(query.text)
        
        # 2. Send the Metadata Line to the frontend
        yield json.dumps({"sources": sources}) + "\n"
        
        # 3. Build the prompt and stream Gemini
        rag_prompt = f"""
        Answer the user's question based ONLY on the following context. 
        Be direct, intellectual, and helpful.
        
        CONTEXT: {context}
        
        QUESTION: {query.text}
        """
        
        stream = ai_client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=rag_prompt
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text

    # Return the stream immediately, deferring the actual work to the generator
    return StreamingResponse(generate_events(), media_type="text/event-stream")

@app.post("/search")
def perform_search(query: SearchQuery):
    _, sources = get_refined_context(query.text)
    return {"results": sources[:query.top_k]}