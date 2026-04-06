import os
import sys
import logging

# Ensure project root is in path
sys.path.append(os.getcwd())

from app.agents.universal_extractor.registry import GrammarRegistry

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestStep1")

def test_registry():
    """Verifies that GrammarRegistry loads .scm files and parsers correctly."""
    print("\n--- Testing Universal Signal Extractor (Step 1: Registry) ---\n")
    
    grammars_dir = "app/agents/universal_extractor/grammars"
    registry = GrammarRegistry(grammars_dir)
    
    languages = ["python", "javascript", "typescript"]
    all_ok = True
    
    for lang in languages:
        query = registry.get_query(lang)
        parser = registry.get_parser(lang)
        
        if query and parser:
            print(f"✅ Language '{lang}': Registry LOADED query and parser.")
        else:
            print(f"❌ Language '{lang}': FAILED. Query={bool(query)}, Parser={bool(parser)}")
            all_ok = False

    # Test resolution
    py_res = registry.resolve_language("app/main.py")
    ts_res = registry.resolve_language("src/index.tsx")
    
    print(f"\nResolution test (.py): {py_res}")
    print(f"Resolution test (.tsx): {ts_res}")
    
    if py_res == "python" and ts_res == "typescript":
        print("✅ Language resolution is working correctly.")
    else:
        print("❌ Language resolution failed.")
        all_ok = False

    if all_ok:
        print("\n✨ STEP 1 VERIFIED: Registry is modular and correctly configured.\n")
    else:
        print("\n⚠️ STEP 1 FAILED: Please check the errors above.\n")

if __name__ == "__main__":
    test_registry()
