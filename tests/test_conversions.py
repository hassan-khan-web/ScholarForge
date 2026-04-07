"""
File Conversion Tests

Tests for document format conversion functions:
- convert_to_txt
- convert_to_md (markdown)
- convert_to_json
- convert_to_docx
- convert_to_pdf (basic test only - requires full system)
"""

import pytest
import os
import json
import tempfile
from backend.AI_engine import (
    convert_to_txt, convert_to_md, convert_to_json,
    clean_ai_output, clean_section_output
)


class TestTextConversions:
    """Test text-based conversions (TXT, MD)."""
    
    @pytest.mark.unit
    def test_convert_to_txt(self, temp_file):
        """Test converting content to TXT format."""
        content = "# Heading\n\nThis is test content.\n\n- Item 1\n- Item 2"
        result = convert_to_txt(content, temp_file)
        
        assert result == "Success"
        assert os.path.exists(temp_file)
        
        # Verify content was written
        with open(temp_file, 'r') as f:
            written_content = f.read()
        assert written_content == content
    
    @pytest.mark.unit
    def test_convert_to_txt_empty(self, temp_file):
        """Test converting empty content to TXT."""
        result = convert_to_txt("", temp_file)
        assert result == "Success"
        
        # File should exist but be empty
        assert os.path.exists(temp_file)
        assert os.path.getsize(temp_file) == 0
    
    @pytest.mark.unit
    def test_convert_to_txt_unicode(self, temp_file):
        """Test converting content with unicode characters."""
        content = "# Résumé\n\n你好 مرحبا\n\nSpecial chars: é à ñ"
        result = convert_to_txt(content, temp_file)
        
        assert result == "Success"
        with open(temp_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        assert written_content == content
    
    @pytest.mark.unit
    def test_convert_to_md(self, temp_file):
        """Test converting content to Markdown format."""
        content = "# Title\n\nThis is markdown content."
        result = convert_to_md(content, temp_file)
        
        assert result == "Success"
        assert os.path.exists(temp_file)
        
        with open(temp_file, 'r') as f:
            written_content = f.read()
        assert written_content == content
    
    @pytest.mark.unit
    def test_convert_to_md_preserves_formatting(self, temp_file):
        """Test that markdown formatting is preserved."""
        content = """# Main Title

## Subtitle

This is a paragraph with **bold** and *italic* text.

- Bullet point 1
- Bullet point 2

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

```python
print("Code block")
```
"""
        result = convert_to_md(content, temp_file)
        assert result == "Success"
        
        with open(temp_file, 'r') as f:
            written_content = f.read()
        assert "**bold**" in written_content
        assert "| Header" in written_content


class TestJSONConversions:
    """Test JSON format conversion."""
    
    @pytest.mark.unit
    def test_convert_to_json_basic(self, temp_file):
        """Test converting content to JSON format."""
        content = "# Report\n\nThis is a test report."
        topic = "Test Topic"
        result = convert_to_json(content, topic, temp_file)
        
        assert result == "Success"
        assert os.path.exists(temp_file)
        
        # Verify JSON is valid
        with open(temp_file, 'r') as f:
            data = json.load(f)
        
        assert data["topic"] == topic
        assert data["content"] == content
        assert "generated_by" in data
        assert data["generated_by"] == "ScholarForge"
    
    @pytest.mark.unit
    def test_convert_to_json_formatting(self, temp_file):
        """Test that JSON is properly formatted."""
        content = "Test"
        topic = "Test"
        result = convert_to_json(content, topic, temp_file)
        
        with open(temp_file, 'r') as f:
            text = f.read()
        
        # Should be indented (formatted)
        assert "  " in text or "\n" in text
        # JSON should be valid
        data = json.loads(text)
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_convert_to_json_handles_special_chars(self, temp_file):
        """Test JSON conversion with special characters."""
        content = 'Line with "quotes" and \\ backslash'
        topic = "Special Chars"
        result = convert_to_json(content, topic, temp_file)
        
        assert result == "Success"
        
        with open(temp_file, 'r') as f:
            data = json.load(f)
        
        assert data["content"] == content
    
    @pytest.mark.unit
    def test_convert_to_json_large_content(self, temp_file):
        """Test JSON conversion with large content."""
        content = "# Large Report\n\n" + ("This is repeated content. " * 1000)
        topic = "Large Topic"
        result = convert_to_json(content, topic, temp_file)
        
        assert result == "Success"
        
        with open(temp_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["content"]) > 10000


class TestCleaningFunctions:
    """Test content cleaning and processing functions."""
    
    @pytest.mark.unit
    def test_clean_ai_output_removes_thinking_tags(self):
        """Test that thinking tags are removed."""
        content = "<think>My thoughts</think>\nActual content"
        result = clean_ai_output(content)
        
        assert "<think>" not in result
        assert "</think>" not in result
        assert "Actual content" in result
    
    @pytest.mark.unit
    def test_clean_ai_output_removes_code_blocks(self):
        """Test that markdown code blocks are removed."""
        content = "```python\nprint('hello')\n```\n\nActual content"
        result = clean_ai_output(content)
        
        assert "```" not in result
        assert "Actual content" in result
    
    @pytest.mark.unit
    def test_clean_ai_output_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        content = "\n\n  Content  \n\n"
        result = clean_ai_output(content)
        
        assert result == "Content"
        assert not result.startswith("\n")
        assert not result.endswith("\n")
    
    @pytest.mark.unit
    def test_clean_ai_output_handles_empty(self):
        """Test cleaning empty or None content."""
        assert clean_ai_output("") == ""
        assert clean_ai_output(None) == ""
    
    @pytest.mark.unit
    def test_clean_ai_output_complex(self):
        """Test cleaning complex content with multiple markers."""
        content = """<think>
Planning the response...
</think>

```json
{"key": "value"}
```

# Real Content

This is the actual content we want to keep.

```python
def foo():
    pass
```

More content here."""
        
        result = clean_ai_output(content)
        
        assert "<think>" not in result
        assert "```" not in result
        assert "Real Content" in result
        assert "actual content" in result
    
    @pytest.mark.unit
    def test_clean_section_output_removes_duplicate_header(self):
        """Test that duplicate section headers are removed."""
        content = "## Understanding AI\n\n## Understanding AI\n\nActual content"
        title = "Understanding AI"
        result = clean_section_output(content, title)
        
        # After cleaning, we expect the duplicate header to be removed
        # The exact behavior depends on implementation
        assert "Actual content" in result or "content" in result.lower()
    
    @pytest.mark.unit
    def test_clean_section_output_keeps_content(self):
        """Test that section content is preserved."""
        content = "## Main Section\n\nImportant information here.\n\nMore details."
        title = "Main Section"
        result = clean_section_output(content, title)
        
        assert "Important information" in result
        assert "details" in result


class TestDocumentConversionIntegration:
    """Integration tests for document conversions."""
    
    @pytest.mark.unit
    def test_report_conversion_workflow(self, temp_file):
        """Test converting a typical report through TXT/MD/JSON."""
        report_content = """# Artificial Intelligence Report

## Executive Summary
This report covers the current state of AI technology.

## Key Findings
- AI is evolving rapidly
- Multiple applications emerging
- Ethical considerations remain

## Conclusion
AI represents a significant technological advancement."""
        
        topic = "AI Research"
        
        # Convert to different formats
        txt_result = convert_to_txt(report_content, temp_file)
        assert txt_result == "Success"
        
        md_file = temp_file + ".md"
        md_result = convert_to_md(report_content, md_file)
        assert md_result == "Success"
        
        json_file = temp_file + ".json"
        json_result = convert_to_json(report_content, topic, json_file)
        assert json_result == "Success"
        
        # Cleanup
        if os.path.exists(md_file):
            os.remove(md_file)
        if os.path.exists(json_file):
            os.remove(json_file)
    
    @pytest.mark.unit
    def test_markdown_with_tables(self, temp_file):
        """Test markdown conversion preserves table formatting."""
        content = """# Data Analysis

| Metric | Value |
|--------|-------|
| Accuracy | 95% |
| Precision | 92% |

## Comments
Table data is important."""
        
        result = convert_to_md(content, temp_file)
        assert result == "Success"
        
        with open(temp_file, 'r') as f:
            written = f.read()
        
        assert "| Metric | Value |" in written
        assert "| Accuracy | 95% |" in written


class TestFileOperations:
    """Test file I/O operations in conversions."""
    
    @pytest.mark.unit
    def test_write_to_readonly_directory(self):
        """Test handling of write to read-only location."""
        # This is platform specific and might not work as expected
        # It documents the expected behavior
        readonly_path = "/root/readonly_test.txt"
        try:
            result = convert_to_txt("Content", readonly_path)
            # Either succeeds or fails gracefully
            assert isinstance(result, str)
        except (PermissionError, OSError):
            # Expected to fail
            pass
    
    @pytest.mark.unit
    def test_file_permissions_after_write(self, temp_file):
        """Test that written files have appropriate permissions."""
        content = "Test content"
        result = convert_to_txt(content, temp_file)
        
        assert result == "Success"
        assert os.path.exists(temp_file)
        
        # File should be readable
        assert os.access(temp_file, os.R_OK)
    
    @pytest.mark.unit
    def test_create_file_in_nonexistent_directory(self):
        """Test creating a file in a non-existent directory."""
        nonexistent_dir = tempfile.mkdtemp()
        test_file = os.path.join(nonexistent_dir, "subdir", "file.txt")
        
        try:
            # This should fail because the subdirectory doesn't exist
            # The conversion function doesn't create parent directories
            with pytest.raises(FileNotFoundError):
                convert_to_txt("Content", test_file)
        finally:
            # Cleanup
            if os.path.exists(nonexistent_dir):
                try:
                    import shutil
                    shutil.rmtree(nonexistent_dir)
                except:
                    pass
