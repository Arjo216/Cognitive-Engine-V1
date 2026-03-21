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
from flashrank import Ranker, RerankRequest
from fastapi.responses import StreamingResponse
from upstash_redis import Redis

# 0. Load Vault FIRST
load_dotenv()
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = FastAPI(title="Cognitive Engine ULTRA", version="8.0")

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
    """Gatekeeper: Mathematically verifies the token on every request."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid Security Token")

# --- INFRASTRUCTURE INITIALIZATION ---
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")
ai_client = genai.Client()

print("🧠 Connecting to Upstash Redis Memory Bank...")
redis_client = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
)

print("🚀 Igniting Neural Cores (Embedding + Reranker)...")
model = SentenceTransformer('BAAI/bge-base-en-v1.5')
ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp")

# Data Models
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
        passages.append({
            "id": match['id'],
            "text": match['metadata']['content'],
            "meta": match['metadata']
        })
    
    if not passages:
        return "", []

    rerank_request = RerankRequest(query=query_text, passages=passages)
    reranked_results = ranker.rerank(rerank_request)
    
    top_context = "\n\n".join([r['text'] for r in reranked_results[:5]])
    
    clean_sources = []
    for r in reranked_results[:3]: 
        clean_sources.append({
            "title": r['meta'].get('title', 'Oracle Context'),
            "author": r['meta'].get('author', 'Unknown'),
            "score": round(float(r['score']), 3),
            "url": r['meta'].get('source_url', '#')
        })
        
    return top_context, clean_sources

def get_standalone_query(user_query: str, session_id: str) -> str:
    """Uses LLM to rewrite pronouns based on Redis history."""
    history_key = f"chat_history:{session_id}"
    try:
        history = redis_client.lrange(history_key, 0, 3)
        if not history:
            return user_query 
            
        history_text = "\n".join(history)
        rewrite_prompt = f"""
        Given the following conversation history and the user's new question, rewrite the new question to be a standalone search query. 
        Do NOT answer the question. Just rewrite it so it contains all the context needed for a database search.
        If the new question is already self-contained, just return it exactly as is.
        
        HISTORY:
        {history_text}
        
        NEW QUESTION: {user_query}
        
        STANDALONE QUERY:
        """
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=rewrite_prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Memory Rewrite Failed (likely rate limit): {e}")
        return user_query # Fallback to original query if LLM fails

# --- 🌐 ENDPOINT 1: AI GENERATION (STREAMING) ---
@app.post("/ask_stream")
async def ask_stream(query: SearchQuery, token_payload: dict = Depends(verify_jwt)):
    
    def generate_events():
        try:
            standalone_query = get_standalone_query(query.text, query.session_id)
            print(f"🔒 [Secure User] Asked: {query.text} | AI Rewrote To: {standalone_query}")
            
            context, sources = get_refined_context(standalone_query)
            yield json.dumps({"sources": sources}) + "\n"
            
            rag_prompt = f"""
            Answer the user's question based ONLY on the following context. 
            Be direct, intellectual, and helpful. Format with clear markdown.
            
            CONTEXT: {context}
            
            QUESTION: {standalone_query}
            """
            
            stream = ai_client.models.generate_content_stream(
                model='gemini-2.5-flash',
                contents=rag_prompt
            )
            
            full_assistant_response = ""
            for chunk in stream:
                if chunk.text:
                    full_assistant_response += chunk.text
                    yield chunk.text

            # Save to Redis
            try:
                history_key = f"chat_history:{query.session_id}"
                redis_client.rpush(history_key, f"User: {query.text}")
                redis_client.rpush(history_key, f"Oracle: {full_assistant_response}")
                redis_client.ltrim(history_key, -6, -1)
                redis_client.expire(history_key, 3600)
            except Exception as e:
                print(f"⚠️ Redis Save Failed: {e}")

        except APIError as e:
            error_msg = f"\n\n⚠️ **System Alert:** AI computing quota exceeded. Please wait 60 seconds and try again."
            yield error_msg
        except Exception as e:
            yield f"\n\n⚠️ **System Alert:** An unexpected error occurred: {str(e)}"

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