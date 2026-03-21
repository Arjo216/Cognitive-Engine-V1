import os
import json
import hashlib
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# 0. Load the Secure Vault
load_dotenv()
if os.getenv("HF_TOKEN"):
    os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 1. Initialize Neural Cores & Database
print("🚀 Initializing BAAI Embedding Model...")
model = SentenceTransformer('BAAI/bge-base-en-v1.5')

print("🧠 Connecting to Pinecone Cloud ('cognitive-core-v2')...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")

def ingest_data(filepath, domain, doc_type, fallback_author="Various"):
    """Dynamically reads, vectorizes, and tags data into the Unified Knowledge Graph."""
    if not os.path.exists(filepath):
        print(f"⚠️ File not found: {filepath}. Skipping...")
        return

    print(f"\n🟢 Ingesting {domain.upper()} dataset from {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    batch_size = 100
    vectors = []

    for i, item in enumerate(data):
        # Dynamic extraction: Handles BOTH the old 'massive_dataset' and the new Swarm JSONs
        text = item.get('content') or item.get('quote') or item.get('text')
        if not text:
            continue
            
        title = item.get('title', f"{domain.capitalize()} Fragment")
        author = item.get('author', fallback_author)
        url = item.get('source_url', '#')
        
        # Generate a mathematically unique ID using an MD5 hash of the text.
        # This guarantees we never accidentally overwrite existing Paul Graham data.
        doc_id = f"{domain}_{hashlib.md5(text.encode('utf-8')).hexdigest()[:16]}"
        
        # Create Neural Embedding
        embedding = model.encode(text).tolist()
        
        # Construct Metadata Tag
        metadata = {
            "title": title,
            "author": author,
            "content": text,
            "domain": domain,
            "doc_type": doc_type,
            "source_url": url
        }
        
        vectors.append((doc_id, embedding, metadata))
        
        # Batch Upsert to Cloud
        if len(vectors) >= batch_size or i == len(data) - 1:
            index.upsert(vectors=vectors)
            print(f"   Upserted {len(vectors)} vectors... ({i+1}/{len(data)})")
            vectors = []

if __name__ == "__main__":
    print("⚡ COMMENCING MULTI-TENANT INJECTION PROTOCOL ⚡")
    
    # 1. The Science Swarm
    ingest_data("data_swarm/science_corpus.json", "science", "arxiv_paper")
    
    # 2. The High-Finance Swarm
    ingest_data("data_swarm/finance_corpus.json", "finance", "sec_filing")
    
    # 3. The Original Foundation (Massive)
    ingest_data("ingestion_core/massive_dataset.json", "general_wisdom", "foundational_quote", "Philosopher/Leader")
    
    # 4. The Prototype Foundation (Dataset)
    ingest_data("ingestion_core/dataset.json", "general_wisdom", "prototype_quote", "Philosopher/Leader")
    
    print("\n✅ UNIFIED KNOWLEDGE GRAPH COMPLETE. All domains successfully integrated.")