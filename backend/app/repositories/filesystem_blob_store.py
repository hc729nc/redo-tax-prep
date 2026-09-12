from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.repositories.interfaces import DocumentBlobStore


class LocalFilesystemBlobStore(DocumentBlobStore):
    """Stores document bytes on local disk under STORAGE_ROOT.

    `storage_key` is an opaque relative path string - callers must never assume
    it is a real filesystem path outside this class, so swapping in an S3-backed
    implementation later doesn't change any calling code.
    """

    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, tax_return_id: UUID, document_id: UUID, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix or ".bin"
        relative_path = Path(str(tax_return_id)) / f"{document_id}{suffix}"
        full_path = self.root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(relative_path)

    def load(self, storage_key: str) -> bytes:
        full_path = self.root / storage_key
        return full_path.read_bytes()

    def delete(self, storage_key: str) -> None:
        full_path = self.root / storage_key
        full_path.unlink(missing_ok=True)

    def save_generated(self, tax_return_id: UUID, filename: str, content: bytes) -> str:
        """For output files (e.g. a filled 1040 PDF) that aren't user-uploaded
        documents, so don't need a document_id. Not part of DocumentBlobStore - the
        generated-output path is local-only for now, unlike user document storage
        which the ABC keeps swappable for S3 later."""
        relative_path = Path(str(tax_return_id)) / "generated" / filename
        full_path = self.root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(relative_path)
