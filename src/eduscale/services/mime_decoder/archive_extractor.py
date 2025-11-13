"""Archive extraction module for processing ZIP, TAR, and GZIP files."""

import gzip
import logging
import mimetypes
import os
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class ArchiveExtractionError(Exception):
    """Exception raised when archive extraction fails."""
    pass


@dataclass
class ExtractedFile:
    """Metadata for an extracted file."""
    filename: str
    size_bytes: int
    mime_type: str
    local_path: str


class ArchiveExtractor:
    """Extractor for various archive formats with safety limits."""

    def __init__(
        self,
        max_files: int = 100,
        max_file_size_mb: int = 50
    ):
        """Initialize extractor with limits.
        
        Args:
            max_files: Maximum number of files to extract
            max_file_size_mb: Maximum size per file in MB
        """
        self.max_files = max_files
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    async def extract_archive(
        self,
        archive_path: str,
        archive_type: str,
        extract_dir: str
    ) -> List[ExtractedFile]:
        """Extract archive and return list of extracted files.
        
        Args:
            archive_path: Path to archive file
            archive_type: Type of archive (zip, tar, gzip)
            extract_dir: Directory to extract files to
            
        Returns:
            List of ExtractedFile objects
            
        Raises:
            ArchiveExtractionError: If extraction fails
        """
        logger.info(
            f"Starting extraction of {archive_type} archive",
            extra={
                "archive_path": archive_path,
                "archive_type": archive_type,
                "extract_dir": extract_dir
            }
        )

        # Ensure extract directory exists
        Path(extract_dir).mkdir(parents=True, exist_ok=True)

        try:
            if archive_type == "zip":
                return await self._extract_zip(archive_path, extract_dir)
            elif archive_type == "tar":
                return await self._extract_tar(archive_path, extract_dir)
            elif archive_type == "gzip":
                return await self._extract_gzip(archive_path, extract_dir)
            else:
                raise ArchiveExtractionError(f"Unsupported archive type: {archive_type}")
        except Exception as e:
            logger.error(
                f"Failed to extract archive: {e}",
                extra={"archive_path": archive_path, "error": str(e)}
            )
            raise ArchiveExtractionError(f"Extraction failed: {e}") from e

    async def _extract_zip(self, archive_path: str, extract_dir: str) -> List[ExtractedFile]:
        """Extract ZIP archive."""
        extracted_files = []

        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Check if password protected
                for info in zip_ref.infolist():
                    if info.flag_bits & 0x1:
                        logger.warning(
                            "Skipping password-protected ZIP archive",
                            extra={"archive_path": archive_path}
                        )
                        return []

                # Extract files with limits
                for info in zip_ref.infolist():
                    if len(extracted_files) >= self.max_files:
                        logger.warning(
                            f"Reached max files limit ({self.max_files}), stopping extraction",
                            extra={"archive_path": archive_path}
                        )
                        break

                    # Skip directories
                    if info.is_dir():
                        continue

                    # Check file size
                    if info.file_size > self.max_file_size_bytes:
                        logger.warning(
                            f"Skipping large file: {info.filename} ({info.file_size} bytes)",
                            extra={"file_name": info.filename, "size": info.file_size}
                        )
                        continue

                    # Check for path traversal
                    if not self._is_safe_path(extract_dir, info.filename):
                        logger.warning(
                            f"Skipping unsafe path: {info.filename}",
                            extra={"file_name": info.filename}
                        )
                        continue

                    # Extract file
                    extracted_path = zip_ref.extract(info, extract_dir)
                    mime_type = self._detect_mime_type(info.filename)

                    extracted_files.append(ExtractedFile(
                        filename=info.filename,
                        size_bytes=info.file_size,
                        mime_type=mime_type,
                        local_path=extracted_path
                    ))

        except zipfile.BadZipFile as e:
            logger.error(
                f"Corrupted ZIP archive: {e}",
                extra={"archive_path": archive_path}
            )
            raise ArchiveExtractionError(f"Corrupted ZIP archive: {e}") from e

        return extracted_files

    async def _extract_tar(self, archive_path: str, extract_dir: str) -> List[ExtractedFile]:
        """Extract TAR archive (including .tar.gz, .tar.bz2)."""
        extracted_files = []

        try:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                # Extract files with limits
                for member in tar_ref.getmembers():
                    if len(extracted_files) >= self.max_files:
                        logger.warning(
                            f"Reached max files limit ({self.max_files}), stopping extraction",
                            extra={"archive_path": archive_path}
                        )
                        break

                    # Skip directories and special files
                    if not member.isfile():
                        continue

                    # Check file size
                    if member.size > self.max_file_size_bytes:
                        logger.warning(
                            f"Skipping large file: {member.name} ({member.size} bytes)",
                            extra={"file_name": member.name, "size": member.size}
                        )
                        continue

                    # Check for path traversal
                    if not self._is_safe_path(extract_dir, member.name):
                        logger.warning(
                            f"Skipping unsafe path: {member.name}",
                            extra={"file_name": member.name}
                        )
                        continue

                    # Extract file
                    tar_ref.extract(member, extract_dir)
                    extracted_path = os.path.join(extract_dir, member.name)
                    mime_type = self._detect_mime_type(member.name)

                    extracted_files.append(ExtractedFile(
                        filename=member.name,
                        size_bytes=member.size,
                        mime_type=mime_type,
                        local_path=extracted_path
                    ))

        except tarfile.TarError as e:
            logger.error(
                f"Corrupted TAR archive: {e}",
                extra={"archive_path": archive_path}
            )
            raise ArchiveExtractionError(f"Corrupted TAR archive: {e}") from e

        return extracted_files

    async def _extract_gzip(self, archive_path: str, extract_dir: str) -> List[ExtractedFile]:
        """Extract GZIP archive (single file compression)."""
        extracted_files = []

        try:
            # GZIP typically compresses a single file
            # Extract to filename without .gz extension
            archive_name = Path(archive_path).name
            if archive_name.endswith('.gz'):
                output_filename = archive_name[:-3]
            else:
                output_filename = archive_name + '.extracted'

            output_path = os.path.join(extract_dir, output_filename)

            with gzip.open(archive_path, 'rb') as gz_file:
                with open(output_path, 'wb') as out_file:
                    # Read and write in chunks to handle large files
                    chunk_size = 1024 * 1024  # 1MB chunks
                    total_size = 0

                    while True:
                        chunk = gz_file.read(chunk_size)
                        if not chunk:
                            break

                        total_size += len(chunk)

                        # Check size limit
                        if total_size > self.max_file_size_bytes:
                            logger.warning(
                                f"GZIP file exceeds size limit, stopping extraction",
                                extra={"archive_path": archive_path, "size": total_size}
                            )
                            os.remove(output_path)
                            return []

                        out_file.write(chunk)

            mime_type = self._detect_mime_type(output_filename)

            extracted_files.append(ExtractedFile(
                filename=output_filename,
                size_bytes=total_size,
                mime_type=mime_type,
                local_path=output_path
            ))

        except (gzip.BadGzipFile, OSError) as e:
            logger.error(
                f"Corrupted GZIP archive: {e}",
                extra={"archive_path": archive_path}
            )
            raise ArchiveExtractionError(f"Corrupted GZIP archive: {e}") from e

        return extracted_files

    def _is_safe_path(self, base_dir: str, filename: str) -> bool:
        """Check if extracted path is safe (no path traversal).
        
        Args:
            base_dir: Base extraction directory
            filename: Filename from archive
            
        Returns:
            True if path is safe, False otherwise
        """
        # Normalize paths
        base_path = os.path.abspath(base_dir)
        target_path = os.path.abspath(os.path.join(base_dir, filename))

        # Check if target is within base directory
        return target_path.startswith(base_path)

    def _detect_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
