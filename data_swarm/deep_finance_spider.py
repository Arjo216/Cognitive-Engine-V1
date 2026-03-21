import os
import time
import requests
import hashlib
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from google import genai

# 1. Initialize Vault & Connections
print("🚀 Booting Resource-Optimized SEC Spider...")
load_dotenv()

# The SEC strictly requires a User-Agent with an email, or they block the IP.
# The SEC strictly requires a heavily formatted User-Agent, Accept-Encoding, and Host.
SEC_HEADERS = {
    'User-Agent': 'FoundersOracle_Research_Division (oraclecrawlerbot123@gmail.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

# Initialize Neural Models
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")
embedder = SentenceTransformer('BAAI/bge-base-en-v1.5')
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Target Manifest (Apple and Microsoft latest 10-Ks)
# For the prototype, we hardcode two specific filings to avoid scraping the massive SEC index.
TARGETS = [
    {
        "company": "Apple Inc. (AAPL)",
        "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"
    },
    {
        "company": "Microsoft Corp. (MSFT)",
        "url": "https://www.sec.gov/Archives/edgar/data/78901/000007890123000058/msft-20230630.htm"
    }
]

def process_filing(target):
    print(f"\n📡 Fetching 10-K for {target['company']}...")
    
    # A. Fetch Document to RAM (No Disk Space Used)
    response = requests.get(target['url'], headers=SEC_HEADERS)
    if response.status_code != 200:
        print("⚠️ SEC blocked the request. Skipping.")
        return

    # B. Purify HTML to Raw Text
    print("🧹 Purifying HTML and stripping tables...")
    soup = BeautifulSoup(response.text, "html.parser")
    raw_text = soup.get_text(separator=' ', strip=True)
    
    # C. Truncate for Token Conservation (First 25,000 chars ~ 5000 tokens)
    chunk = raw_text[:25000] 

    # D. Cognitive Extraction (Gemini)
    print("🧠 Engaging Gemini for Risk Factor Extraction...")
    prompt = f"""
    You are an expert financial analyst. Read the following text extracted from a company's 10-K filing. 
    Identify and summarize the top 3 core business risks or competitive threats facing this company.
    Format your response as a clean, concise paragraph. No fluff.
    
    TEXT:
    {chunk}
    """
    
    try:
        ai_response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        extracted_insight = ai_response.text
        print(f"✅ AI Extracted: {extracted_insight[:100]}...")
        
        # E. Vectorize & Inject
        print("🧬 Embedding and Injecting to Pinecone...")
        doc_id = f"sec_deep_{hashlib.md5(extracted_insight.encode()).hexdigest()[:10]}"
        vector = embedder.encode(extracted_insight).tolist()
        
        metadata = {
            "title": f"{target['company']} - Core Risk Factors",
            "author": "SEC EDGAR 10-K",
            "content": extracted_insight,
            "domain": "finance",
            "doc_type": "10-k_risk_analysis",
            "source_url": target['url']
        }
        
        index.upsert(vectors=[(doc_id, vector, metadata)])
        print("🟢 Injection Successful.")
        
    except Exception as e:
        print(f"❌ AI Extraction Failed: {e}")

if __name__ == "__main__":
    for target in TARGETS:
        process_filing(target)
        print("⏳ Initiating 15-second API Cooldown to respect Free Tier Limits...")
        time.sleep(15) # CRITICAL: Prevents 429 Resource Exhausted Error
        
    print("\n✅ V2 DEEP FINANCE SWARM COMPLETE.")