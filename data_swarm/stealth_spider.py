import os
import time
import requests
import hashlib
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from google import genai
from google.genai.errors import APIError
from groq import Groq 

print("🕷️ Booting V4.1 Multi-Core Stealth Spider...")
load_dotenv()

# --- 1. INFRASTRUCTURE & TUNNELS ---
SEC_HEADERS = {
    'User-Agent': 'FoundersOracle_Research_Division (crawler.bot@gmail.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'www.sec.gov'
}

proxy_url = os.getenv("PROXY_URL")
proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
if proxies:
    print("🛡️ Proxy Tunnel Engaged. IP Masking Active.")
else:
    print("⚠️ No Proxy detected in .env. Attempting direct connection...")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("cognitive-core-v2")
embedder = SentenceTransformer('BAAI/bge-base-en-v1.5')

ai_client = genai.Client() # Primary: Gemini
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) # Secondary: Groq

# --- 2. VERIFIED TARGET MANIFEST (Updated for Proxy Stability) ---
TARGETS = [
    # --- BIG TECH ---
    {"company": "Apple Inc. (AAPL)", "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"},
    {"company": "Microsoft Corp. (MSFT)", "url": "https://www.sec.gov/Archives/edgar/data/78901/000007890123000058/msft-20230630.htm"},
    {"company": "NVIDIA Corp. (NVDA)", "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm"},
    # --- HIGH FINANCE / BANKING ---
    {"company": "JPMorgan Chase & Co. (JPM)", "url": "https://www.sec.gov/Archives/edgar/data/19617/000001961724000215/jpm-20231231.htm"},
    # --- RETAIL & LOGISTICS ---
    {"company": "Walmart Inc. (WMT)", "url": "https://www.sec.gov/Archives/edgar/data/104169/000010416924000037/wmt-20240131.htm"},
    {"company": "Amazon.com, Inc. (AMZN)", "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872424000008/amzn-20231231.htm"},
    # --- HEALTHCARE / PHARMA ---
    {"company": "Johnson & Johnson (JNJ)", "url": "https://www.sec.gov/Archives/edgar/data/200406/000020040624000012/jnj-20231231.htm"},
    # --- Automation & EV ---
    {"company": "Tesla, Inc. (TSLA)", "url": "https://www.sec.gov/Archives/edgar/data/1318605/000162828024002390/tsla-20231231.htm"}
]

def process_filing(target):
    print(f"\n📡 Fetching 10-K for {target['company']}...")
    
    try:
        response = requests.get(target['url'], headers=SEC_HEADERS, proxies=proxies, timeout=20)
        if response.status_code != 200:
            print(f"⚠️ HTTP Error {response.status_code}. Skipping.")
            return

        print("🧹 Purifying HTML and stripping tables...")
        soup = BeautifulSoup(response.text, "html.parser")
        raw_text = soup.get_text(separator=' ', strip=True)
        chunk = raw_text[:15000] 

        prompt = f"""
        You are an expert financial analyst. Read the following text extracted from a company's 10-K filing. 
        Identify and summarize the top 3 core business risks or competitive threats facing this company.
        Format your response as a clean, concise paragraph. No fluff.
        
        TEXT:
        {chunk}
        """
        
        # --- 2. THE AI WATERFALL ARCHITECTURE ---
        extracted_insight = ""
        try:
            print("🧠 Engaging Primary Core (Gemini)...")
            ai_response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            extracted_insight = ai_response.text
            print("🟢 Gemini Extraction Successful!")
            
        except APIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("⚠️ Gemini Limit Hit. Cascading to Secondary Core (Groq/LLaMA-3.1)...")
                try:
                    # UPDATED GROQ MODEL HERE
                    groq_response = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant", 
                        temperature=0.3,
                        max_tokens=500
                    )
                    extracted_insight = groq_response.choices[0].message.content
                    print("🟣 Groq Extraction Successful!")
                except Exception as groq_e:
                    print(f"❌ Secondary Core Failed: {groq_e}")
                    return
            else:
                print(f"❌ Primary Core Fatal Error: {e}")
                return

        # 3. Vector Injection
        if extracted_insight:
            print("🧬 Embedding and Injecting to Pinecone...")
            doc_id = f"sec_stealth_{hashlib.md5(extracted_insight.encode()).hexdigest()[:10]}"
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
        
    except requests.exceptions.ProxyError:
        print("❌ Proxy Connection Failed. Check your proxy credentials in .env.")
    except Exception as e:
        print(f"❌ System Error: {e}")

if __name__ == "__main__":
    for target in TARGETS:
        process_filing(target)
        print("⏳ Standard 5-second cooldown between targets...")
        time.sleep(5) 
        
    print("\n✅ V4.1 MULTI-CORE SWARM COMPLETE.")