"""
Script to re-index the Bible database with all verses.
This clears the existing database and creates fresh embeddings.
"""
import os
import sys
import shutil
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from app.config import settings


def main():
    """Re-index the Bible database."""
    print("=" * 60)
    print("Bible Database Re-indexing")
    print("=" * 60)
    
    # Clear existing database
    db_path = Path(project_root) / settings.chroma_persist_directory
    if db_path.exists():
        print(f"\nClearing existing database at {db_path}...")
        shutil.rmtree(db_path)
        print("Database cleared.")
    
    # Import after clearing to get fresh connection
    from app.services.rag_service import RAGService
    
    print("\nInitializing fresh RAG service...")
    print("(Loading local embedding model - this may take a moment on first run)")
    rag_service = RAGService()
    
    # Check verse count
    verses_path = Path(project_root) / "data" / "bible" / "verses.json"
    if not verses_path.exists():
        print(f"\n✗ Verses file not found at {verses_path}")
        print("Please run: python -m app.scripts.download_bible")
        return
    
    import json
    with open(verses_path) as f:
        verses = json.load(f)
    
    print(f"\nFound {len(verses)} verses to index.")
    print("Using local sentence-transformers embeddings (no API calls needed).")
    print("Estimated time: 2-5 minutes depending on CPU.\n")
    
    response = input("Proceed? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    print("\nStarting indexing process...")
    print("This uses local embeddings - much faster than cloud API.\n")
    
    try:
        rag_service.index_bible_verses(str(verses_path))
        
        final_count = rag_service.get_verse_count()
        print(f"\n✓ Successfully indexed {final_count} verses!")
        print("\nYou can now run the application:")
        print("  streamlit run ui/streamlit_app.py")
        
    except Exception as e:
        print(f"\n✗ Error during indexing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
