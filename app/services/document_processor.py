import io
from typing import List

from docx import Document as DocxDocument
from fastapi import UploadFile
from pypdf import PdfReader

from app.core.config import settings
from app.core.logging import logger


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP

    async def process_file(self, file: UploadFile) -> str:
        """Processa diferentes tipos de arquivo."""
        content = await file.read()

        if file.filename.endswith(".pdf"):
            return self._process_pdf(content)
        elif file.filename.endswith(".docx"):
            return self._process_docx(content)
        elif file.filename.endswith(".txt"):
            return content.decode("utf-8")
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {file.filename}")

    def _process_pdf(self, content: bytes) -> str:
        """Processa arquivo PDF."""
        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}")
            raise ValueError(f"Erro ao processar PDF: {str(e)}")

    def _process_docx(self, content: bytes) -> str:
        """Processa arquivo DOCX."""
        try:
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Erro ao processar DOCX: {str(e)}")
            raise ValueError(f"Erro ao processar DOCX: {str(e)}")

    def chunk_text(self, text: str) -> List[str]:
        """Divide o texto em chunks menores."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Se não é o último chunk, tenta encontrar um ponto de quebra natural
            if end < len(text):
                # Procura por quebra de linha ou ponto final próximo
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if text[i] in ".\n":
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Próximo chunk com overlap
            start = end - self.chunk_overlap
            start = max(start, 0)

        return chunks
