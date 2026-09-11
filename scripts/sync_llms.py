import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openrouter_insights import LLMIndexSync

def sync_llms():
    """
    Synchronizes the LLM index from OpenRouter and ArtificialAnalysis
    and saves it to a local JSON file in the app/services directory.
    """
    load_dotenv()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in .env")
        return

    print("🚀 Synchronizing LLM Index from OpenRouter and ArtificialAnalysis...")
    
    try:
        # Use API mode to fetch fresh data
        client = LLMIndexSync(mode="api")
        models = client.sync()
        
        # Save to the service directory
        target_path = Path("app/services/llm_index.json")
        
        # Convert models to serializable dicts
        # Pydantic v2 uses model_dump()
        data = [m.model_dump() for m in models]
        
        with open(target_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ Successfully synchronized {len(models)} models.")
        print(f"📄 Index saved to: {target_path}")
        
    except Exception as e:
        print(f"❌ Error during synchronization: {e}")

if __name__ == "__main__":
    sync_llms()
