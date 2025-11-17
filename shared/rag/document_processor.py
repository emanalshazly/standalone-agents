"""
Document processing and chunking utilities
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import hashlib
import re

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document representation"""
    content: str
    metadata: Dict[str, Any]
    doc_id: str
    source: str


@dataclass
class Chunk:
    """Text chunk representation"""
    content: str
    chunk_id: str
    doc_id: str
    metadata: Dict[str, Any]
    start_char: int
    end_char: int


class DocumentProcessor:
    """
    Document processing pipeline for RAG

    Features:
    - Multiple format support (PDF, DOCX, TXT, HTML, MD, JSON)
    - Intelligent chunking strategies
    - Metadata extraction
    - Text cleaning and normalization
    - Deduplication
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ):
        """
        Initialize document processor

        Args:
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def process_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Process a file into a Document

        Args:
            file_path: Path to file
            metadata: Additional metadata

        Returns:
            Processed Document
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type and extract content
        content = self._extract_content(path)

        # Generate document ID
        doc_id = self._generate_doc_id(content, str(path))

        # Build metadata
        doc_metadata = {
            "filename": path.name,
            "file_type": path.suffix,
            "file_size": path.stat().st_size,
            "source": str(path),
            **(metadata or {})
        }

        return Document(
            content=content,
            metadata=doc_metadata,
            doc_id=doc_id,
            source=str(path)
        )

    def process_text(
        self,
        text: str,
        source: str = "text_input",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Process raw text into a Document

        Args:
            text: Raw text content
            source: Source identifier
            metadata: Additional metadata

        Returns:
            Processed Document
        """
        # Clean text
        content = self._clean_text(text)

        # Generate document ID
        doc_id = self._generate_doc_id(content, source)

        doc_metadata = {
            "source": source,
            "text_length": len(content),
            **(metadata or {})
        }

        return Document(
            content=content,
            metadata=doc_metadata,
            doc_id=doc_id,
            source=source
        )

    def chunk_document(
        self,
        document: Document,
        strategy: str = "fixed"
    ) -> List[Chunk]:
        """
        Chunk a document into smaller pieces

        Args:
            document: Document to chunk
            strategy: Chunking strategy (fixed, semantic, sentence)

        Returns:
            List of Chunks
        """
        if strategy == "fixed":
            return self._fixed_size_chunking(document)
        elif strategy == "semantic":
            return self._semantic_chunking(document)
        elif strategy == "sentence":
            return self._sentence_chunking(document)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

    def _fixed_size_chunking(self, document: Document) -> List[Chunk]:
        """Chunk by fixed character size with overlap"""

        chunks = []
        text = document.content
        start = 0
        chunk_num = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.min_chunk_size:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    space = text.rfind(' ', start, end)
                    if space > start + self.min_chunk_size:
                        end = space

            chunk_text = text[start:end].strip()

            if len(chunk_text) >= self.min_chunk_size:
                chunk_id = f"{document.doc_id}_chunk_{chunk_num}"

                chunks.append(Chunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    doc_id=document.doc_id,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_num,
                        "total_chunks": 0  # Will update later
                    },
                    start_char=start,
                    end_char=end
                ))

                chunk_num += 1

            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else end

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)

        return chunks

    def _semantic_chunking(self, document: Document) -> List[Chunk]:
        """Chunk by semantic boundaries (paragraphs, sections)"""

        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', document.content)

        chunks = []
        current_chunk = ""
        chunk_num = 0
        start_char = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding paragraph exceeds chunk size, save current chunk
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunk_id = f"{document.doc_id}_chunk_{chunk_num}"
                end_char = start_char + len(current_chunk)

                chunks.append(Chunk(
                    content=current_chunk.strip(),
                    chunk_id=chunk_id,
                    doc_id=document.doc_id,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_num,
                        "chunking_strategy": "semantic"
                    },
                    start_char=start_char,
                    end_char=end_char
                ))

                chunk_num += 1
                start_char = end_char
                current_chunk = ""

            current_chunk += para + "\n\n"

        # Add final chunk
        if current_chunk.strip():
            chunk_id = f"{document.doc_id}_chunk_{chunk_num}"
            chunks.append(Chunk(
                content=current_chunk.strip(),
                chunk_id=chunk_id,
                doc_id=document.doc_id,
                metadata={
                    **document.metadata,
                    "chunk_index": chunk_num,
                    "chunking_strategy": "semantic"
                },
                start_char=start_char,
                end_char=start_char + len(current_chunk)
            ))

        return chunks

    def _sentence_chunking(self, document: Document) -> List[Chunk]:
        """Chunk by sentences"""

        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', document.content)

        chunks = []
        current_chunk = ""
        chunk_num = 0
        start_char = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunk_id = f"{document.doc_id}_chunk_{chunk_num}"
                end_char = start_char + len(current_chunk)

                chunks.append(Chunk(
                    content=current_chunk.strip(),
                    chunk_id=chunk_id,
                    doc_id=document.doc_id,
                    metadata={
                        **document.metadata,
                        "chunk_index": chunk_num,
                        "chunking_strategy": "sentence"
                    },
                    start_char=start_char,
                    end_char=end_char
                ))

                chunk_num += 1
                start_char = end_char
                current_chunk = ""

            current_chunk += sentence + ". "

        if current_chunk.strip():
            chunk_id = f"{document.doc_id}_chunk_{chunk_num}"
            chunks.append(Chunk(
                content=current_chunk.strip(),
                chunk_id=chunk_id,
                doc_id=document.doc_id,
                metadata={
                    **document.metadata,
                    "chunk_index": chunk_num,
                    "chunking_strategy": "sentence"
                },
                start_char=start_char,
                end_char=start_char + len(current_chunk)
            ))

        return chunks

    def _extract_content(self, path: Path) -> str:
        """Extract text content from file"""

        suffix = path.suffix.lower()

        if suffix == '.txt' or suffix == '.md':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()

        elif suffix == '.pdf':
            return self._extract_from_pdf(path)

        elif suffix == '.docx':
            return self._extract_from_docx(path)

        elif suffix == '.html':
            return self._extract_from_html(path)

        elif suffix == '.json':
            return self._extract_from_json(path)

        else:
            # Try reading as text
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                raise ValueError(f"Unsupported file type: {suffix}")

    def _extract_from_pdf(self, path: Path) -> str:
        """Extract text from PDF"""
        # Placeholder - would use PyPDF2 or pdfplumber
        logger.warning("PDF extraction not fully implemented")
        return f"Content from PDF: {path.name}"

    def _extract_from_docx(self, path: Path) -> str:
        """Extract text from DOCX"""
        # Placeholder - would use python-docx
        logger.warning("DOCX extraction not fully implemented")
        return f"Content from DOCX: {path.name}"

    def _extract_from_html(self, path: Path) -> str:
        """Extract text from HTML"""
        # Placeholder - would use BeautifulSoup
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        # Simple tag removal
        text = re.sub(r'<[^>]+>', '', html)
        return text

    def _extract_from_json(self, path: Path) -> str:
        """Extract text from JSON"""
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert to readable text
        return json.dumps(data, indent=2)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s.!?,;:()\-\']', '', text)

        # Normalize newlines
        text = text.replace('\r\n', '\n')

        return text.strip()

    def _generate_doc_id(self, content: str, source: str) -> str:
        """Generate unique document ID"""

        hash_input = f"{content[:1000]}{source}"
        return hashlib.md5(hash_input.encode()).hexdigest()
