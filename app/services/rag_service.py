"""
RAG (Retrieval-Augmented Generation) service for Bible verse retrieval and grounding.
"""
import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import settings


class RAGService:
    """Service for retrieving relevant Bible verses using vector similarity search."""
    
    def __init__(self):
        # Use local sentence-transformers model for embeddings
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.chroma_client = None
        self.collection = None
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection."""
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=settings.bible_collection_name,
            metadata={"description": "Bible verses for RAG retrieval"}
        )
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using local sentence-transformers model."""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def index_bible_verses(self, verses_path: str = "data/bible/verses.json"):
        """Index Bible verses into ChromaDB."""
        # Check if already indexed
        if self.collection.count() > 0:
            print(f"Collection already has {self.collection.count()} verses indexed.")
            return
        
        # Load verses
        with open(verses_path, 'r', encoding='utf-8') as f:
            verses = json.load(f)
        
        # Prepare data for indexing
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        print(f"Indexing {len(verses)} verses...")
        
        for i, verse in enumerate(verses):
            verse_id = f"{verse['book']}_{verse['chapter']}_{verse['verse']}"
            reference = f"{verse['book']} {verse['chapter']}:{verse['verse']}"
            
            # Create searchable document combining reference and text
            doc_text = f"{reference}: {verse['text']}"
            
            ids.append(verse_id)
            documents.append(doc_text)
            metadatas.append({
                "book": verse['book'],
                "chapter": str(verse['chapter']),
                "verse": str(verse['verse']),
                "reference": reference,
                "text": verse['text'],
                "testament": verse['testament'],
                "topics": ",".join(verse.get('topic', []))
            })
            
            # Get embedding
            embedding = self._get_embedding(doc_text)
            embeddings.append(embedding)
            
            if (i + 1) % 10 == 0:
                print(f"Indexed {i + 1}/{len(verses)} verses")
        
        # Add to collection in batches (ChromaDB max batch size is ~5000)
        BATCH_SIZE = 5000
        total = len(ids)
        
        for start in range(0, total, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total)
            print(f"Adding batch {start//BATCH_SIZE + 1}: verses {start+1}-{end}")
            
            self.collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
                embeddings=embeddings[start:end]
            )
        
        print(f"Successfully indexed {len(verses)} verses.")
    
    def retrieve_verses(
        self, 
        query: str, 
        top_k: int = None,
        filter_testament: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant Bible verses for a query.
        
        Args:
            query: User query or question
            top_k: Number of verses to retrieve
            filter_testament: Filter by "Old" or "New" testament
            
        Returns:
            List of verse dictionaries with metadata
        """
        if top_k is None:
            top_k = settings.retrieval_top_k
        
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        
        # Build where filter if testament specified
        where_filter = None
        if filter_testament:
            where_filter = {"testament": filter_testament}
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        verses = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if results['distances'] else None
                
                verses.append({
                    "id": doc_id,
                    "reference": metadata['reference'],
                    "text": metadata['text'],
                    "book": metadata['book'],
                    "chapter": int(metadata['chapter']),
                    "verse": int(metadata['verse']),
                    "testament": metadata['testament'],
                    "topics": metadata['topics'].split(",") if metadata['topics'] else [],
                    "similarity_score": 1 - distance if distance else None
                })
        
        return verses
    
    def format_context(self, verses: List[Dict]) -> str:
        """Format retrieved verses as context for the LLM."""
        if not verses:
            return "No relevant Bible verses found for this query."
        
        context_parts = []
        for verse in verses:
            context_parts.append(
                f"[{verse['reference']}] \"{verse['text']}\""
            )
        
        return "\n\n".join(context_parts)
    
    def validate_verse_reference(self, reference: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate if a Bible verse reference exists in our database.
        
        Args:
            reference: Bible reference like "John 3:16"
            
        Returns:
            Tuple of (is_valid, verse_data or None)
        """
        # Try to find the verse by searching for exact reference
        results = self.collection.query(
            query_texts=[reference],
            n_results=1,
            include=["metadatas", "distances"]
        )
        
        if results['ids'] and results['ids'][0]:
            metadata = results['metadatas'][0][0]
            # Check if reference matches closely
            if metadata['reference'].lower() == reference.lower():
                return True, {
                    "reference": metadata['reference'],
                    "text": metadata['text'],
                    "book": metadata['book'],
                    "chapter": int(metadata['chapter']),
                    "verse": int(metadata['verse'])
                }
        
        return False, None
    
    def search_by_topic(self, topic: str, top_k: int = 5) -> List[Dict]:
        """Search for verses by topic."""
        # Search with topic as query
        return self.retrieve_verses(topic, top_k=top_k)
    
    def get_verse_count(self) -> int:
        """Get the number of indexed verses."""
        return self.collection.count()


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
