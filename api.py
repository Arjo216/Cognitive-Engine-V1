import os
import json
import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from google import genai
from google.genai.errors import APIError
from groq import Groq  # <-- NEW: Groq Engine Imported
from flashrank import Ranker, RerankRequest
from fastapi.responses import StreamingResponse
from upstash_redis import Redis

# 0. Load Vault FIRST
load_dotenv()
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = FastAPI(title="Cognitive Engine ULTRA", version="9.0 - Invincible Core")

# --- 🔒 SECURITY CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
SECRET_KEY = os.getenv("API_SECRET_KEY", "founders_oracle_ultra_secure_key_999!")

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid Security Token")

# --- INFRASTRUCTURE INITIALIZATION ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")

# 🧠 Initialize Dual-Core LLMs
ai_client = genai.Client() # Primary
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) # Secondary

redis_client = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
)

print("🚀 Igniting Neural Cores (Embedding + Reranker)...")
model = SentenceTransformer('BAAI/bge-base-en-v1.5')
ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp")

class SearchQuery(BaseModel):
    text: str
    top_k: int = 5
    session_id: str = "oracle_default_session"

# --- CORE LOGIC ---
def get_refined_context(query_text: str):
    query_vector = model.encode(query_text).tolist()
    pinecone_response = index.query(vector=query_vector, top_k=15, include_metadata=True)
    
    passages = []
    for match in pinecone_response['matches']:
        passages.append({"id": match['id'], "text": match['metadata']['content'], "meta": match['metadata']})
    
    if not passages:
        return "", []

    rerank_request = RerankRequest(query=query_text, passages=passages)
    reranked_results = ranker.rerank(rerank_request)
    
    top_context = "\n\n".join([r['text'] for r in reranked_results[:6]])
    clean_sources = [{"title": r['meta'].get('title', 'Oracle Context'), "author": r['meta'].get('author', 'Unknown'), "score": round(float(r['score']), 3), "url": r['meta'].get('source_url', '#')} for r in reranked_results[:6]]
        
    return top_context, clean_sources

def get_standalone_query(user_query: str, session_id: str) -> str:
    """Uses LLM to rewrite pronouns (with Groq Fallback)."""
    history_key = f"chat_history:{session_id}"
    try:
        history = redis_client.lrange(history_key, 0, 3)
        if not history: return user_query 
            
        history_text = "\n".join(history)
        rewrite_prompt = f"Given the history, rewrite the new question to be a standalone search query. HISTORY: {history_text}\nNEW QUESTION: {user_query}\nSTANDALONE QUERY:"
        
        try:
            # Primary Core
            response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=rewrite_prompt)
            return response.text.strip()
        except APIError:
            # Secondary Core (Groq) Fallback
            groq_response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": rewrite_prompt}],
                model="llama-3.1-8b-instant", temperature=0.3, max_tokens=100
            )
            return groq_response.choices[0].message.content.strip()
    except Exception:
        return user_query 

# --- 🌐 ENDPOINT 1: AI GENERATION (DUAL-CORE STREAMING) ---
@app.post("/ask_stream")
async def ask_stream(query: SearchQuery, token_payload: dict = Depends(verify_jwt)):
    
    def generate_events():
        try:
            standalone_query = get_standalone_query(query.text, query.session_id)
            context, sources = get_refined_context(standalone_query)
            yield json.dumps({"sources": sources}) + "\n"
            
            rag_prompt = f"Answer the user's question based ONLY on the following context. Be direct, intellectual, and helpful. Format with clear markdown.\nCONTEXT: {context}\nQUESTION: {standalone_query}"
            
            full_assistant_response = ""
            
            # --- THE WATERFALL ---
            try:
                # 1. Try Gemini First
                stream = ai_client.models.generate_content_stream(model='gemini-2.5-flash', contents=rag_prompt)
                for chunk in stream:
                    if chunk.text:
                        full_assistant_response += chunk.text
                        yield chunk.text
            except APIError as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    # 2. Silently Failover to Groq
                    groq_stream = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": rag_prompt}],
                        model="llama-3.1-8b-instant",
                        temperature=0.3,
                        stream=True # <-- Groq streams too!
                    )
                    for chunk in groq_stream:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_assistant_response += content
                            yield content
                else:
                    raise e # Throw other random errors

            # Save to Redis Memory
            try:
                history_key = f"chat_history:{query.session_id}"
                redis_client.rpush(history_key, f"User: {query.text}")
                redis_client.rpush(history_key, f"Oracle: {full_assistant_response}")
                redis_client.ltrim(history_key, -6, -1)
                redis_client.expire(history_key, 3600)
            except Exception as e:
                print(f"⚠️ Redis Save Failed: {e}")

        except Exception as e:
            yield f"\n\n⚠️ **System Alert:** All AI Cores exhausted or unexpected error: {str(e)}"

    return StreamingResponse(generate_events(), media_type="text/event-stream")

# --- 🌐 ENDPOINT 2: RAW VECTOR SEARCH ---
@app.post("/search")
def perform_search(query: SearchQuery, token_payload: dict = Depends(verify_jwt)):
    """
    🔒 SECURED ENDPOINT
    Performs a direct vector search without invoking the generative LLM.
    Useful for frontend applications that just want the source documents.
    """
    _, sources = get_refined_context(query.text)
    return {"results": sources[:query.top_k]}