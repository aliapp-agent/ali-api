"""PostgreSQL implementation of DocumentRepositoryInterface for Ali API.

This module contains the concrete implementation of document data access
using PostgreSQL and SQLModel.
"""

from datetime import datetime
from typing import (
    Dict,
    List,
    Optional,
)

from sqlalchemy import (
    and_,
    func,
    or_,
    text,
)
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlmodel import (
    Session,
    select,
)

from app.core.config import settings
from app.core.logging import logger
from app.domain.entities import (
    DocumentCategory,
    DocumentContent,
    DocumentEntity,
    DocumentMetadata,
    DocumentSource,
    DocumentStatus,
    DocumentType,
)
from app.domain.exceptions import (
    DocumentAlreadyExistsError,
    DocumentNotFoundError,
    RepositoryError,
)
from app.domain.repositories import DocumentRepositoryInterface
from app.models.rag import Document as DocumentModel


class PostgresDocumentRepository(DocumentRepositoryInterface):
    """PostgreSQL implementation of the document repository.

    This class implements document data access using PostgreSQL database
    through SQLModel ORM.
    """

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session.

        Args:
            db_session: SQLModel database session
        """
        self.db_session = db_session

    async def create(self, document: DocumentEntity) -> DocumentEntity:
        """Create a new document in the database.

        Args:
            document: Document entity to create

        Returns:
            DocumentEntity: Created document with assigned ID

        Raises:
            DocumentAlreadyExistsError: If document with ID already exists
            RepositoryError: If creation fails
        """
        try:
            # Convert entity to model
            document_model = self._entity_to_model(document)

            # Save to database
            self.db_session.add(document_model)
            self.db_session.commit()
            self.db_session.refresh(document_model)

            logger.info(
                "document_created",
                document_id=document_model.id,
                user_id=document.user_id,
                title=document.title,
                document_type=document.document_type.value,
            )

            # Convert back to entity
            return self._model_to_entity(document_model)

        except IntegrityError as e:
            self.db_session.rollback()
            if "id" in str(e).lower():
                raise DocumentAlreadyExistsError(document.id)
            else:
                raise RepositoryError(f"Failed to create document: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(
                "document_creation_failed",
                error=str(e),
                user_id=document.user_id,
                title=document.title,
            )
            raise RepositoryError(f"Database error during document creation: {str(e)}")

    async def get_by_id(self, document_id: str) -> Optional[DocumentEntity]:
        """Get document by ID from the database.

        Args:
            document_id: Document ID to lookup

        Returns:
            DocumentEntity or None if not found
        """
        try:
            document_model = self.db_session.get(DocumentModel, document_id)

            if not document_model:
                return None

            return self._model_to_entity(document_model)

        except SQLAlchemyError as e:
            logger.error(
                "get_document_by_id_failed", error=str(e), document_id=document_id
            )
            raise RepositoryError(f"Database error during document lookup: {str(e)}")

    async def update(self, document: DocumentEntity) -> DocumentEntity:
        """Update an existing document in the database.

        Args:
            document: Document entity with updated data

        Returns:
            DocumentEntity: Updated document

        Raises:
            DocumentNotFoundError: If document doesn't exist
            RepositoryError: If update fails
        """
        try:
            # Get existing document
            document_model = self.db_session.get(DocumentModel, document.id)
            if not document_model:
                raise DocumentNotFoundError(document.id)

            # Update model fields
            self._update_model_from_entity(document_model, document)

            # Save changes
            self.db_session.commit()
            self.db_session.refresh(document_model)

            logger.info(
                "document_updated", document_id=document.id, title=document.title
            )

            return self._model_to_entity(document_model)

        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(
                "document_update_failed", error=str(e), document_id=document.id
            )
            raise RepositoryError(f"Database error during document update: {str(e)}")

    async def delete(self, document_id: str) -> bool:
        """Delete a document (soft delete) from the database.

        Args:
            document_id: ID of document to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            DocumentNotFoundError: If document doesn't exist
        """
        try:
            document_model = self.db_session.get(DocumentModel, document_id)
            if not document_model:
                raise DocumentNotFoundError(document_id)

            # Soft delete by setting status
            document_model.status = DocumentStatus.DELETED.value
            document_model.updated_at = datetime.utcnow()

            self.db_session.commit()

            logger.info("document_deleted", document_id=document_id)

            return True

        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(
                "document_deletion_failed", error=str(e), document_id=document_id
            )
            raise RepositoryError(f"Database error during document deletion: {str(e)}")

    async def get_user_documents(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[DocumentStatus] = None,
        category: Optional[DocumentCategory] = None,
    ) -> List[DocumentEntity]:
        """Get documents for a specific user.

        Args:
            user_id: User ID to get documents for
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            status: Filter by document status
            category: Filter by document category

        Returns:
            List[DocumentEntity]: User's documents
        """
        try:
            query = select(DocumentModel).where(DocumentModel.user_id == user_id)

            # Apply filters
            if status:
                query = query.where(DocumentModel.status == status.value)
            else:
                # Exclude deleted documents by default
                query = query.where(
                    DocumentModel.status != DocumentStatus.DELETED.value
                )

            if category:
                query = query.where(DocumentModel.category == category.value)

            # Apply pagination and ordering
            query = (
                query.offset(offset)
                .limit(limit)
                .order_by(DocumentModel.updated_at.desc())
            )

            document_models = self.db_session.exec(query).all()

            return [self._model_to_entity(model) for model in document_models]

        except SQLAlchemyError as e:
            logger.error("get_user_documents_failed", error=str(e), user_id=user_id)
            raise RepositoryError(
                f"Database error during user documents lookup: {str(e)}"
            )

    async def get_public_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[DocumentCategory] = None,
    ) -> List[DocumentEntity]:
        """Get public documents.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            category: Filter by document category

        Returns:
            List[DocumentEntity]: Public documents
        """
        try:
            query = select(DocumentModel).where(
                and_(
                    DocumentModel.is_public == True,
                    DocumentModel.status == DocumentStatus.ACTIVE.value,
                )
            )

            if category:
                query = query.where(DocumentModel.category == category.value)

            query = (
                query.offset(offset)
                .limit(limit)
                .order_by(DocumentModel.updated_at.desc())
            )

            document_models = self.db_session.exec(query).all()

            return [self._model_to_entity(model) for model in document_models]

        except SQLAlchemyError as e:
            logger.error("get_public_documents_failed", error=str(e))
            raise RepositoryError(
                f"Database error during public documents lookup: {str(e)}"
            )

    async def search_documents(
        self,
        query: str,
        user_id: Optional[int] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0,
        category: Optional[DocumentCategory] = None,
    ) -> List[DocumentEntity]:
        """Search documents by content and metadata.

        Args:
            query: Search query
            user_id: Filter by specific user (None for all)
            include_public: Whether to include public documents
            limit: Maximum number of results
            offset: Number of results to skip
            category: Filter by document category

        Returns:
            List[DocumentEntity]: Documents matching search
        """
        try:
            search_term = f"%{query.lower()}%"

            # Build search conditions
            search_conditions = or_(
                DocumentModel.title.ilike(search_term),
                DocumentModel.content.ilike(search_term),
                DocumentModel.description.ilike(search_term),
            )

            # Build access conditions
            access_conditions = []

            if user_id:
                access_conditions.append(DocumentModel.user_id == user_id)

            if include_public:
                access_conditions.append(
                    and_(
                        DocumentModel.is_public == True,
                        DocumentModel.status == DocumentStatus.ACTIVE.value,
                    )
                )

            # Combine conditions
            if access_conditions:
                base_query = select(DocumentModel).where(
                    and_(
                        search_conditions,
                        or_(*access_conditions),
                        DocumentModel.status != DocumentStatus.DELETED.value,
                    )
                )
            else:
                base_query = select(DocumentModel).where(
                    and_(
                        search_conditions,
                        DocumentModel.status != DocumentStatus.DELETED.value,
                    )
                )

            # Apply category filter
            if category:
                base_query = base_query.where(DocumentModel.category == category.value)

            # Apply pagination and ordering
            base_query = (
                base_query.offset(offset)
                .limit(limit)
                .order_by(DocumentModel.updated_at.desc())
            )

            document_models = self.db_session.exec(base_query).all()

            return [self._model_to_entity(model) for model in document_models]

        except SQLAlchemyError as e:
            logger.error("search_documents_failed", error=str(e))
            raise RepositoryError(f"Database error during search: {str(e)}")

    async def get_documents_by_hash(self, content_hash: str) -> List[DocumentEntity]:
        """Get documents by content hash.

        Args:
            content_hash: Content hash to search for

        Returns:
            List[DocumentEntity]: Documents with matching hash
        """
        try:
            query = select(DocumentModel).where(
                and_(
                    DocumentModel.metadata["file_hash"].astext == content_hash,
                    DocumentModel.status != DocumentStatus.DELETED.value,
                )
            )

            document_models = self.db_session.exec(query).all()

            return [self._model_to_entity(model) for model in document_models]

        except SQLAlchemyError as e:
            logger.error(
                "get_documents_by_hash_failed", error=str(e), content_hash=content_hash
            )
            raise RepositoryError(f"Database error during hash lookup: {str(e)}")

    async def count_user_documents(
        self, user_id: int, status: Optional[DocumentStatus] = None
    ) -> int:
        """Count documents for a specific user.

        Args:
            user_id: User ID to count documents for
            status: Filter by document status

        Returns:
            int: Number of documents
        """
        try:
            query = select(func.count(DocumentModel.id)).where(
                DocumentModel.user_id == user_id
            )

            if status:
                query = query.where(DocumentModel.status == status.value)
            else:
                # Exclude deleted documents by default
                query = query.where(
                    DocumentModel.status != DocumentStatus.DELETED.value
                )

            count = self.db_session.exec(query).one()
            return count

        except SQLAlchemyError as e:
            logger.error("count_user_documents_failed", error=str(e), user_id=user_id)
            raise RepositoryError(f"Database error during document count: {str(e)}")

    async def get_document_statistics(
        self,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict:
        """Get document statistics.

        Args:
            user_id: Filter by specific user
            date_from: Start date for statistics
            date_to: End date for statistics

        Returns:
            Dict: Statistics including counts, categories, etc.
        """
        try:
            # Build base filters
            filters = [DocumentModel.status != DocumentStatus.DELETED.value]

            if user_id:
                filters.append(DocumentModel.user_id == user_id)
            if date_from:
                filters.append(DocumentModel.created_at >= date_from)
            if date_to:
                filters.append(DocumentModel.created_at <= date_to)

            # Total documents
            total_documents = self.db_session.exec(
                select(func.count(DocumentModel.id)).where(and_(*filters))
            ).one()

            # Documents by status
            active_documents = self.db_session.exec(
                select(func.count(DocumentModel.id)).where(
                    and_(DocumentModel.status == DocumentStatus.ACTIVE.value, *filters)
                )
            ).one()

            draft_documents = self.db_session.exec(
                select(func.count(DocumentModel.id)).where(
                    and_(DocumentModel.status == DocumentStatus.DRAFT.value, *filters)
                )
            ).one()

            archived_documents = self.db_session.exec(
                select(func.count(DocumentModel.id)).where(
                    and_(
                        DocumentModel.status == DocumentStatus.ARCHIVED.value, *filters
                    )
                )
            ).one()

            error_documents = self.db_session.exec(
                select(func.count(DocumentModel.id)).where(
                    and_(DocumentModel.status == DocumentStatus.ERROR.value, *filters)
                )
            ).one()

            # Public documents
            public_documents = self.db_session.exec(
                select(func.count(DocumentModel.id)).where(
                    and_(DocumentModel.is_public == True, *filters)
                )
            ).one()

            # Average statistics
            avg_stats = self.db_session.exec(
                select(
                    func.avg(
                        DocumentModel.metadata["word_count"].astext.cast(
                            text("integer")
                        )
                    ),
                    func.avg(
                        DocumentModel.metadata["character_count"].astext.cast(
                            text("integer")
                        )
                    ),
                    func.avg(
                        DocumentModel.metadata["file_size"].astext.cast(text("integer"))
                    ),
                ).where(and_(*filters))
            ).first()

            avg_word_count, avg_char_count, avg_file_size = avg_stats or (0, 0, 0)

            return {
                "total_documents": total_documents,
                "active_documents": active_documents,
                "draft_documents": draft_documents,
                "archived_documents": archived_documents,
                "error_documents": error_documents,
                "public_documents": public_documents,
                "private_documents": total_documents - public_documents,
                "avg_word_count": float(avg_word_count or 0),
                "avg_character_count": float(avg_char_count or 0),
                "avg_file_size_bytes": float(avg_file_size or 0),
            }

        except SQLAlchemyError as e:
            logger.error("get_document_statistics_failed", error=str(e))
            raise RepositoryError(f"Database error during statistics: {str(e)}")

    async def archive_old_documents(
        self, older_than: datetime, exclude_user_ids: Optional[List[int]] = None
    ) -> int:
        """Archive old documents.

        Args:
            older_than: Archive documents older than this date
            exclude_user_ids: User IDs to exclude from archiving

        Returns:
            int: Number of documents archived
        """
        try:
            filters = [
                DocumentModel.updated_at < older_than,
                DocumentModel.status == DocumentStatus.ACTIVE.value,
            ]

            if exclude_user_ids:
                filters.append(DocumentModel.user_id.notin_(exclude_user_ids))

            # Use raw SQL for bulk update
            result = self.db_session.exec(
                text(
                    """
                    UPDATE documents 
                    SET status = 'archived', updated_at = :updated_at 
                    WHERE updated_at < :older_than 
                    AND status = 'active'
                    {} 
                """.format(
                        "AND user_id NOT IN :exclude_user_ids"
                        if exclude_user_ids
                        else ""
                    )
                ),
                {
                    "older_than": older_than,
                    "updated_at": datetime.utcnow(),
                    **(
                        {"exclude_user_ids": tuple(exclude_user_ids)}
                        if exclude_user_ids
                        else {}
                    ),
                },
            )

            self.db_session.commit()

            affected_rows = result.rowcount
            logger.info("documents_archived", count=affected_rows)

            return affected_rows

        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error("archive_old_documents_failed", error=str(e))
            raise RepositoryError(f"Database error during archiving: {str(e)}")

    def _entity_to_model(self, entity: DocumentEntity) -> DocumentModel:
        """Convert DocumentEntity to DocumentModel.

        Args:
            entity: Document entity to convert

        Returns:
            DocumentModel: Converted document model
        """
        # Convert metadata to dict
        metadata_dict = {}
        if entity.metadata:
            metadata_dict = {
                "word_count": entity.metadata.word_count,
                "character_count": entity.metadata.character_count,
                "file_size": entity.metadata.file_size,
                "file_hash": entity.metadata.file_hash,
                "embedding_model": entity.metadata.embedding_model,
                "processed_at": (
                    entity.metadata.processed_at.isoformat()
                    if entity.metadata.processed_at
                    else None
                ),
                "chunk_count": entity.metadata.chunk_count,
            }

        # Convert source to dict
        source_dict = {}
        if entity.source:
            source_dict = {
                "url": entity.source.url,
                "original_filename": entity.source.original_filename,
                "upload_user_id": entity.source.upload_user_id,
                "source_system": entity.source.source_system,
                "import_batch_id": entity.source.import_batch_id,
            }

        return DocumentModel(
            id=entity.id,
            title=entity.title,
            content=entity.content.raw_text if entity.content else "",
            user_id=entity.user_id,
            document_type=entity.document_type.value,
            category=entity.category.value,
            status=entity.status.value,
            tags=entity.tags,
            description=entity.description,
            is_public=entity.is_public,
            metadata=metadata_dict,
            source=source_dict,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _model_to_entity(self, model: DocumentModel) -> DocumentEntity:
        """Convert DocumentModel to DocumentEntity.

        Args:
            model: Document model to convert

        Returns:
            DocumentEntity: Converted document entity
        """
        # Convert content
        content = DocumentContent(
            raw_text=model.content or "", processed_text=model.content or "", chunks=[]
        )

        # Convert metadata
        metadata_data = model.metadata or {}
        metadata = DocumentMetadata(
            word_count=metadata_data.get("word_count", 0),
            character_count=metadata_data.get("character_count", 0),
            file_size=metadata_data.get("file_size", 0),
            file_hash=metadata_data.get("file_hash"),
            embedding_model=metadata_data.get("embedding_model"),
            processed_at=(
                datetime.fromisoformat(metadata_data.get("processed_at"))
                if metadata_data.get("processed_at")
                else None
            ),
            chunk_count=metadata_data.get("chunk_count", 0),
        )

        # Convert source
        source_data = model.source or {}
        source = DocumentSource(
            url=source_data.get("url"),
            original_filename=source_data.get("original_filename"),
            upload_user_id=source_data.get("upload_user_id"),
            source_system=source_data.get("source_system"),
            import_batch_id=source_data.get("import_batch_id"),
        )

        return DocumentEntity(
            title=model.title,
            content=content,
            user_id=model.user_id,
            document_type=DocumentType(model.document_type),
            category=DocumentCategory(model.category),
            status=DocumentStatus(model.status),
            metadata=metadata,
            source=source,
            tags=model.tags or [],
            description=model.description,
            is_public=model.is_public,
            created_at=model.created_at,
            updated_at=model.updated_at,
            document_id=model.id,
        )

    def _update_model_from_entity(
        self, model: DocumentModel, entity: DocumentEntity
    ) -> None:
        """Update DocumentModel fields from DocumentEntity.

        Args:
            model: Document model to update
            entity: Document entity with new data
        """
        model.title = entity.title
        model.content = entity.content.raw_text if entity.content else ""
        model.document_type = entity.document_type.value
        model.category = entity.category.value
        model.status = entity.status.value
        model.tags = entity.tags
        model.description = entity.description
        model.is_public = entity.is_public
        model.updated_at = entity.updated_at

        # Update metadata
        if entity.metadata:
            model.metadata = {
                "word_count": entity.metadata.word_count,
                "character_count": entity.metadata.character_count,
                "file_size": entity.metadata.file_size,
                "file_hash": entity.metadata.file_hash,
                "embedding_model": entity.metadata.embedding_model,
                "processed_at": (
                    entity.metadata.processed_at.isoformat()
                    if entity.metadata.processed_at
                    else None
                ),
                "chunk_count": entity.metadata.chunk_count,
            }

        # Update source
        if entity.source:
            model.source = {
                "url": entity.source.url,
                "original_filename": entity.source.original_filename,
                "upload_user_id": entity.source.upload_user_id,
                "source_system": entity.source.source_system,
                "import_batch_id": entity.source.import_batch_id,
            }
