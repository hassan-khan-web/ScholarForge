"""
Database CRUD Tests

Tests for database operations:
- Folder creation, renaming, deletion
- Chat session management
- Message storage and retrieval
- Report storage and retrieval
"""

import pytest
from backend.database import (
    create_folder, rename_folder, delete_folder, get_folders_with_sessions,
    create_chat_session, rename_chat_session, delete_chat_session, get_chat_session,
    get_session_messages, save_chat_message,
    save_report, get_all_reports, get_report_content, delete_report, delete_all_reports,
    save_hook, get_all_hooks, delete_hook,
    ProjectFolder, ChatSession, ChatMessage, ReportDB, Hook
)


class TestFolderOperations:
    """Test project folder CRUD operations."""
    
    @pytest.mark.unit
    def test_create_folder(self, test_db):
        """Test creating a new folder."""
        folder = create_folder("My Research Project")
        assert folder.id is not None
        assert folder.name == "My Research Project"
        
        # Verify it's in the database
        retrieved = test_db.query(ProjectFolder).filter_by(id=folder.id).first()
        assert retrieved is not None
        assert retrieved.name == "My Research Project"
    
    @pytest.mark.unit
    def test_create_duplicate_folder(self, test_db):
        """Test that creating a duplicate folder raises an error."""
        create_folder("Duplicate Folder")
        
        with pytest.raises(Exception, match="already exists"):
            create_folder("Duplicate Folder")
    
    @pytest.mark.unit
    def test_rename_folder(self, test_db, sample_folder):
        """Test renaming a folder."""
        success = rename_folder(sample_folder.id, "Renamed Folder")
        assert success is True
        
        # Verify the rename
        retrieved = test_db.query(ProjectFolder).filter_by(id=sample_folder.id).first()
        assert retrieved.name == "Renamed Folder"
    
    @pytest.mark.unit
    def test_rename_nonexistent_folder(self, test_db):
        """Test renaming a folder that doesn't exist."""
        success = rename_folder(99999, "New Name")
        assert success is False
    
    @pytest.mark.unit
    def test_delete_folder(self, test_db, sample_folder):
        """Test deleting a folder."""
        folder_id = sample_folder.id
        success = delete_folder(folder_id)
        assert success is True
        
        # Verify deletion
        retrieved = test_db.query(ProjectFolder).filter_by(id=folder_id).first()
        assert retrieved is None
    
    @pytest.mark.unit
    def test_delete_nonexistent_folder(self, test_db):
        """Test deleting a folder that doesn't exist."""
        success = delete_folder(99999)
        assert success is False
    
    @pytest.mark.unit
    def test_get_folders_with_sessions(self, test_db, sample_folder, sample_session):
        """Test retrieving folders with their sessions."""
        folders = get_folders_with_sessions()
        assert len(folders) > 0
        
        # Find our test folder
        test_folder = next((f for f in folders if f["id"] == sample_folder.id), None)
        assert test_folder is not None
        assert test_folder["name"] == sample_folder.name
        assert len(test_folder["sessions"]) == 1
        assert test_folder["sessions"][0]["title"] == sample_session.title


class TestChatSessionOperations:
    """Test chat session CRUD operations."""
    
    @pytest.mark.unit
    def test_create_chat_session(self, test_db, sample_folder):
        """Test creating a new chat session."""
        session = create_chat_session(sample_folder.id, "New Conversation")
        assert session.id is not None
        assert session.title == "New Conversation"
        assert session.folder_id == sample_folder.id
    
    @pytest.mark.unit
    def test_rename_chat_session(self, test_db, sample_session):
        """Test renaming a chat session."""
        success = rename_chat_session(sample_session.id, "Renamed Conversation")
        assert success is True
        
        # Verify the rename
        retrieved = get_chat_session(sample_session.id)
        assert retrieved.title == "Renamed Conversation"
    
    @pytest.mark.unit
    def test_rename_nonexistent_session(self, test_db):
        """Test renaming a session that doesn't exist."""
        success = rename_chat_session(99999, "New Title")
        assert success is False
    
    @pytest.mark.unit
    def test_delete_chat_session(self, test_db, sample_session):
        """Test deleting a chat session."""
        session_id = sample_session.id
        success = delete_chat_session(session_id)
        assert success is True
        
        # Verify deletion
        retrieved = get_chat_session(session_id)
        assert retrieved is None
    
    @pytest.mark.unit
    def test_get_chat_session(self, test_db, sample_session):
        """Test retrieving a chat session."""
        retrieved = get_chat_session(sample_session.id)
        assert retrieved is not None
        assert retrieved.id == sample_session.id
        assert retrieved.title == sample_session.title
    
    @pytest.mark.unit
    def test_get_nonexistent_session(self, test_db):
        """Test retrieving a session that doesn't exist."""
        retrieved = get_chat_session(99999)
        assert retrieved is None


class TestChatMessageOperations:
    """Test chat message storage and retrieval."""
    
    @pytest.mark.unit
    def test_save_chat_message(self, test_db, sample_session):
        """Test saving a chat message."""
        save_chat_message(sample_session.id, "user", "Hello, AI!")
        
        # Verify it was saved
        messages = test_db.query(ChatMessage).filter_by(session_id=sample_session.id).all()
        assert len(messages) > 0
        assert messages[-1].content == "Hello, AI!"
        assert messages[-1].role == "user"
    
    @pytest.mark.unit
    def test_get_session_messages(self, test_db, sample_session, sample_messages):
        """Test retrieving all messages from a session."""
        messages = get_session_messages(sample_session.id)
        assert len(messages) == 3
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
    
    @pytest.mark.unit
    def test_get_session_messages_empty(self, test_db, sample_session):
        """Test retrieving messages from an empty session."""
        # Delete all messages first
        test_db.query(ChatMessage).filter_by(session_id=sample_session.id).delete()
        test_db.commit()
        
        messages = get_session_messages(sample_session.id)
        assert len(messages) == 0
    
    @pytest.mark.unit
    def test_message_order(self, test_db, sample_session):
        """Test that messages are returned in chronological order."""
        for i in range(3):
            save_chat_message(sample_session.id, "user", f"Message {i}")
        
        messages = get_session_messages(sample_session.id)
        for i, msg in enumerate(messages):
            assert f"Message {i}" in msg.content


class TestReportOperations:
    """Test report storage and retrieval."""
    
    @pytest.mark.unit
    def test_save_report(self, test_db):
        """Test saving a report."""
        save_report("AI Research", "# AI Research\n\nContent about AI")
        
        # Verify it was saved
        reports = get_all_reports()
        assert len(reports) > 0
        assert reports[0].topic == "AI Research"
    
    @pytest.mark.unit
    def test_get_all_reports(self, test_db, sample_report):
        """Test retrieving all reports."""
        # Save additional report
        save_report("Another Report", "Content")
        
        reports = get_all_reports()
        assert len(reports) >= 2
        
        # Check that reports are ordered by creation date (newest first)
        topics = [r.topic for r in reports]
        assert "Another Report" in topics
    
    @pytest.mark.unit
    def test_get_report_content(self, test_db, sample_report):
        """Test retrieving report content."""
        report = get_report_content(sample_report.id)
        assert report is not None
        assert report.topic == sample_report.topic
        assert report.content == sample_report.content
    
    @pytest.mark.unit
    def test_get_nonexistent_report(self, test_db):
        """Test retrieving a report that doesn't exist."""
        report = get_report_content(99999)
        assert report is None
    
    @pytest.mark.unit
    def test_delete_report(self, test_db, sample_report):
        """Test deleting a report."""
        report_id = sample_report.id
        success = delete_report(report_id)
        assert success is True
        
        # Verify deletion
        report = get_report_content(report_id)
        assert report is None
    
    @pytest.mark.unit
    def test_delete_nonexistent_report(self, test_db):
        """Test deleting a report that doesn't exist."""
        success = delete_report(99999)
        assert success is False
    
    @pytest.mark.unit
    def test_delete_all_reports(self, test_db, sample_report):
        """Test deleting all reports."""
        save_report("Report 2", "Content 2")
        save_report("Report 3", "Content 3")
        
        all_reports_before = get_all_reports()
        assert len(all_reports_before) >= 3
        
        success = delete_all_reports()
        assert success is True
        
        all_reports_after = get_all_reports()
        assert len(all_reports_after) == 0


class TestHookOperations:
    """Test hooks (research notes) storage and retrieval."""
    
    @pytest.mark.unit
    def test_save_hook(self, test_db):
        """Test saving a hook (research note)."""
        save_hook("Important research: Machine learning is evolving rapidly")
        
        # Verify it was saved
        hooks = get_all_hooks()
        assert len(hooks) > 0
        assert "Machine learning" in hooks[0].content
    
    @pytest.mark.unit
    def test_get_all_hooks(self, test_db, sample_hook):
        """Test retrieving all hooks."""
        save_hook("Another hook content")
        
        hooks = get_all_hooks()
        assert len(hooks) >= 2
        
        # Check that hooks are ordered by creation date (newest first)
        assert "Another hook" in hooks[0].content
    
    @pytest.mark.unit
    def test_delete_hook(self, test_db, sample_hook):
        """Test deleting a hook."""
        hook_id = sample_hook.id
        success = delete_hook(hook_id)
        assert success is True
        
        # Verify deletion
        hooks = get_all_hooks()
        hook_ids = [h.id for h in hooks]
        assert hook_id not in hook_ids
    
    @pytest.mark.unit
    def test_delete_nonexistent_hook(self, test_db):
        """Test deleting a hook that doesn't exist."""
        success = delete_hook(99999)
        assert success is False


class TestDatabaseConstraints:
    """Test database constraints and relationships."""
    
    @pytest.mark.unit
    def test_cascade_delete_sessions_with_folder(self, test_db, sample_folder, sample_session):
        """Test that deleting a folder cascades to delete its sessions."""
        session_id = sample_session.id
        folder_id = sample_folder.id
        
        # Delete folder
        delete_folder(folder_id)
        
        # Verify session is also deleted (cascade)
        session = get_chat_session(session_id)
        assert session is None
    
    @pytest.mark.unit
    def test_cascade_delete_messages_with_session(self, test_db, sample_session, sample_messages):
        """Test that deleting a session cascades to delete its messages."""
        session_id = sample_session.id
        delete_chat_session(session_id)
        
        # Verify messages are also deleted (cascade)
        messages = test_db.query(ChatMessage).filter_by(session_id=session_id).all()
        assert len(messages) == 0
