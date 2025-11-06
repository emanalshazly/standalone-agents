"""
RAG System - نظام الاسترجاع المعزز بالتوليد
Advanced Retrieval-Augmented Generation with multi-source knowledge
"""

from typing import List, Dict, Any, Optional, Union
import os
from pathlib import Path
import logging
from datetime import datetime
import json

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document


class RAGSystem:
    """
    Revolutionary RAG System with:
    - Multi-source knowledge aggregation
    - Vector-based semantic search
    - Context-aware retrieval
    - Pain-point focused knowledge base
    - Multi-language support (Arabic & English)
    """

    def __init__(
        self,
        domain: str,
        collection_name: str,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        persist_directory: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """Initialize RAG system"""
        self.domain = domain
        self.collection_name = collection_name
        self.logger = logging.getLogger(f"{__name__}.{domain}")

        # Set persist directory
        if persist_directory is None:
            persist_directory = f"./src/knowledge/vectors/{domain}"

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize embedding model (supports Arabic & English)
        self.logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self._embedding_function
            )
            self.logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self._embedding_function,
                metadata={"domain": domain}
            )
            self.logger.info(f"Created new collection: {collection_name}")

        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", "،", "؛", " ", ""]
        )

        # Knowledge statistics
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "sources": set(),
            "languages": set()
        }

        self._update_stats()

    def _embedding_function(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def _update_stats(self):
        """Update knowledge base statistics"""
        try:
            count = self.collection.count()
            self.stats["total_chunks"] = count
            self.logger.info(f"Knowledge base contains {count} chunks")
        except Exception as e:
            self.logger.error(f"Error updating stats: {str(e)}")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        source: str = "manual",
        language: str = "auto"
    ):
        """
        Add documents to the knowledge base

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            source: Source identifier
            language: Document language (auto-detect if 'auto')
        """
        if not documents:
            return

        # Prepare metadata
        if metadatas is None:
            metadatas = [{}] * len(documents)

        all_chunks = []
        all_metadatas = []
        all_ids = []

        for idx, (doc, metadata) in enumerate(zip(documents, metadatas)):
            # Detect language if needed
            if language == "auto":
                doc_language = self._detect_language(doc)
            else:
                doc_language = language

            # Split into chunks
            chunks = self.text_splitter.split_text(doc)

            for chunk_idx, chunk in enumerate(chunks):
                # Create chunk metadata
                chunk_metadata = {
                    **metadata,
                    "source": source,
                    "language": doc_language,
                    "domain": self.domain,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                    "timestamp": datetime.now().isoformat()
                }

                all_chunks.append(chunk)
                all_metadatas.append(chunk_metadata)
                all_ids.append(f"{source}_{idx}_{chunk_idx}_{datetime.now().timestamp()}")

        # Add to collection
        try:
            self.collection.add(
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_ids
            )

            self.stats["sources"].add(source)
            self.stats["languages"].add(doc_language)
            self._update_stats()

            self.logger.info(
                f"Added {len(all_chunks)} chunks from {len(documents)} documents (source: {source})"
            )

        except Exception as e:
            self.logger.error(f"Error adding documents: {str(e)}", exc_info=True)
            raise

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_relevance_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query

        Args:
            query: Search query
            k: Number of results to retrieve
            filter_metadata: Optional metadata filters
            min_relevance_score: Minimum relevance threshold

        Returns:
            List of relevant documents with metadata
        """
        try:
            # Build where clause
            where = None
            if filter_metadata:
                where = filter_metadata

            # Query collection
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where
            )

            # Process results
            documents = []
            if results and results['documents']:
                for idx in range(len(results['documents'][0])):
                    # Calculate relevance score (distance to similarity)
                    distance = results['distances'][0][idx] if results['distances'] else 0
                    relevance_score = 1 / (1 + distance)  # Convert distance to similarity

                    if relevance_score >= min_relevance_score:
                        doc = {
                            "content": results['documents'][0][idx],
                            "metadata": results['metadatas'][0][idx] if results['metadatas'] else {},
                            "relevance_score": relevance_score,
                            "source": results['metadatas'][0][idx].get('source', 'Unknown') if results['metadatas'] else 'Unknown'
                        }
                        documents.append(doc)

            self.logger.info(f"Retrieved {len(documents)} relevant documents for query")
            return documents

        except Exception as e:
            self.logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            return []

    def retrieve_with_reranking(
        self,
        query: str,
        k: int = 10,
        rerank_top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with re-ranking for better relevance

        Args:
            query: Search query
            k: Initial number of candidates
            rerank_top_k: Final number after re-ranking
            filter_metadata: Optional metadata filters

        Returns:
            Re-ranked list of documents
        """
        # Initial retrieval
        candidates = self.retrieve(query, k=k, filter_metadata=filter_metadata)

        if not candidates:
            return []

        # Re-rank based on multiple factors
        for doc in candidates:
            # Combine relevance score with other factors
            metadata = doc.get('metadata', {})

            # Boost recent documents
            timestamp = metadata.get('timestamp')
            recency_boost = 1.0
            if timestamp:
                try:
                    doc_time = datetime.fromisoformat(timestamp)
                    days_old = (datetime.now() - doc_time).days
                    recency_boost = 1.0 / (1 + days_old / 30)  # Decay over 30 days
                except Exception:
                    pass

            # Boost based on source priority
            source_priority = {
                'verified': 1.3,
                'expert': 1.2,
                'manual': 1.1,
                'automatic': 1.0
            }
            source_boost = source_priority.get(metadata.get('source_type', 'automatic'), 1.0)

            # Combined score
            doc['final_score'] = (
                doc['relevance_score'] * 0.7 +
                recency_boost * 0.2 +
                source_boost * 0.1
            )

        # Sort by final score
        candidates.sort(key=lambda x: x['final_score'], reverse=True)

        return candidates[:rerank_top_k]

    def add_pain_point_knowledge(
        self,
        pain_point: str,
        solution: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add pain-point specific knowledge

        Args:
            pain_point: Description of the pain point
            solution: Solution or guidance
            metadata: Additional metadata
        """
        document = f"Pain Point: {pain_point}\n\nSolution: {solution}"

        doc_metadata = {
            **(metadata or {}),
            "type": "pain_point",
            "pain_point": pain_point,
            "priority": metadata.get("priority", "medium") if metadata else "medium"
        }

        self.add_documents(
            documents=[document],
            metadatas=[doc_metadata],
            source="pain_points"
        )

    def search_pain_points(
        self,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for relevant pain points and solutions"""
        return self.retrieve(
            query=query,
            k=k,
            filter_metadata={"type": "pain_point"}
        )

    def _detect_language(self, text: str) -> str:
        """Detect text language"""
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars > len(text) * 0.3:
            return "ar"
        return "en"

    def import_from_file(
        self,
        file_path: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Import knowledge from a file

        Supports: .txt, .md, .json
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if source is None:
            source = path.stem

        # Read file based on extension
        if path.suffix == '.txt' or path.suffix == '.md':
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.add_documents([content], [metadata or {}], source)

        elif path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if isinstance(data, list):
                    documents = [item.get('content', str(item)) for item in data]
                    metadatas = [
                        {**item.get('metadata', {}), **(metadata or {})}
                        for item in data
                    ]
                    self.add_documents(documents, metadatas, source)
                else:
                    self.add_documents([str(data)], [metadata or {}], source)

        self.logger.info(f"Imported knowledge from: {file_path}")

    def export_knowledge(self, output_path: str):
        """Export knowledge base to JSON"""
        try:
            # Get all documents
            results = self.collection.get()

            export_data = {
                "domain": self.domain,
                "collection": self.collection_name,
                "stats": {
                    **self.stats,
                    "sources": list(self.stats["sources"]),
                    "languages": list(self.stats["languages"])
                },
                "documents": [
                    {
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i] if results['metadatas'] else {}
                    }
                    for i in range(len(results['ids']))
                ],
                "exported_at": datetime.now().isoformat()
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Exported {len(results['ids'])} documents to {output_path}")

        except Exception as e:
            self.logger.error(f"Error exporting knowledge: {str(e)}", exc_info=True)
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            **self.stats,
            "sources": list(self.stats["sources"]),
            "languages": list(self.stats["languages"])
        }

    def clear(self):
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_function
            )
            self._update_stats()
            self.logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Error clearing collection: {str(e)}")
            raise
