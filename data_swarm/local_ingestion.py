import os
import json
import hashlib
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

print("🚀 Booting Local Ingestion Engine...")
load_dotenv()

# 1. Connect to Infrastructure
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")
embedder = SentenceTransformer('BAAI/bge-base-en-v1.5')

# 2. Load the Technical Blueprints
#file_path = "data_swarm/tech_roadmaps.json"
file_path = "data_swarm/omni_roadmaps.json"
print(f"📂 Reading {file_path}...")

with open(file_path, 'r', encoding='utf-8') as f:
    roadmaps = json.load(f)

# 3. Vectorize and Inject
print(f"🧬 Injecting {len(roadmaps)} highly specialized technical roadmaps...")
for item in roadmaps:
    # Generate unique ID based on content
    doc_id = f"tech_spec_{hashlib.md5(item['content'].encode()).hexdigest()[:10]}"
    
    # Create neural vector
    vector = embedder.encode(item['content']).tolist()
    
    # Package metadata
    metadata = {
        "title": item['title'],
        "author": item['author'],
        "content": item['content'],
        "domain": "engineering",
        "doc_type": "technical_roadmap",
        "source_url": "Internal Blueprint"
    }
    
    # Inject to Pinecone
    index.upsert(vectors=[(doc_id, vector, metadata)])
    print(f"   🟢 Injected: {item['title']}")

print("\n✅ LOCAL INGESTION COMPLETE. The Oracle has been upgraded.")