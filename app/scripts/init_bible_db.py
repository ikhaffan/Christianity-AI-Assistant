"""
Script to initialize the Bible database.
Run this before starting the application for the first time.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from app.services.rag_service import get_rag_service


def main():
    """Initialize the Bible verse database."""
    print("=" * 50)
    print("Christianity AI Assistant - Database Initialization")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your-gemini-api-key-here":
        print("\n⚠️  WARNING: Gemini API key not configured!")
        print("Please set your API key in the .env file:")
        print("  GEMINI_API_KEY=your-actual-gemini-key-here")
        print("\nThe database cannot be initialized without a valid API key.")
        return
    
    print("\nInitializing RAG service...")
    rag_service = get_rag_service()
    
    # Check if already indexed
    current_count = rag_service.get_verse_count()
    if current_count > 0:
        print(f"\n✓ Database already contains {current_count} verses.")
        response = input("Do you want to re-index? (y/N): ")
        if response.lower() != 'y':
            print("Skipping indexing.")
            return
        
        # Clear existing data
        print("Clearing existing data...")
        rag_service.chroma_client.delete_collection(rag_service.collection.name)
        rag_service._initialize_chroma()
    
    # Index verses
    print("\nIndexing Bible verses...")
    print("This will generate embeddings for each verse using OpenAI.")
    print("Please wait...\n")
    
    try:
        verses_path = os.path.join(project_root, "data", "bible", "verses.json")
        rag_service.index_bible_verses(verses_path)
        
        final_count = rag_service.get_verse_count()
        print(f"\n✓ Successfully indexed {final_count} verses!")
        print("\nYou can now run the application:")
        print("  streamlit run ui/streamlit_app.py")
        
    except Exception as e:
        print(f"\n✗ Error during indexing: {e}")
        print("\nPlease check:")
        print("  1. Your OpenAI API key is valid")
        print("  2. You have API credits available")
        print("  3. The data/bible/verses.json file exists")


if __name__ == "__main__":
    main()
