"""
Test suite for the DWF Analyzer MCP Server.
"""

import os
import pytest
from pathlib import Path

from dwf_analyzer_mcp.tools.dwf_parser import DWFParser
from dwf_analyzer_mcp.tools.image_extractor import DWFImageExtractor
from dwf_analyzer_mcp.utils.model_manager import ModelManager


# Test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_DWF = FIXTURES_DIR / "home1.dwf"


class TestDWFParser:
    """Test cases for DWF parser functionality."""
    
    def test_parser_initialization(self):
        """Test DWF parser initialization."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        parser = DWFParser(str(SAMPLE_DWF))
        assert parser.file_path == str(SAMPLE_DWF)
        assert parser.file_size > 0
    
    def test_parse_dwf_file(self):
        """Test DWF file parsing."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        parser = DWFParser(str(SAMPLE_DWF))
        result = parser.parse()
        
        assert isinstance(result, dict)
        assert "header" in result
        assert "layers" in result
        assert "objects_summary" in result
        assert "file_info" in result
    
    def test_parse_nonexistent_file(self):
        """Test parsing of non-existent file."""
        parser = DWFParser("nonexistent.dwf")
        result = parser.parse()
        
        assert "error" in result
        assert result["error"] is True


class TestDWFImageExtractor:
    """Test cases for DWF image extraction."""
    
    def test_extractor_initialization(self):
        """Test image extractor initialization."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        extractor = DWFImageExtractor(str(SAMPLE_DWF))
        assert extractor.dwf_file_path == str(SAMPLE_DWF)
        assert extractor.extracted_images == []
    
    def test_extract_images(self):
        """Test image extraction from DWF file."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        extractor = DWFImageExtractor(str(SAMPLE_DWF))
        images = extractor.extract_embedded_images()
        
        assert isinstance(images, list)
        # The sample file should contain some images
        if images:
            assert len(images) > 0
            assert "type" in images[0]
            assert "size" in images[0]
    
    def test_analysis_summary(self):
        """Test analysis summary generation."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        extractor = DWFImageExtractor(str(SAMPLE_DWF))
        extractor.extract_embedded_images()
        summary = extractor.get_analysis_summary()
        
        assert isinstance(summary, dict)
        assert "total_images" in summary
        assert "image_types" in summary
        assert "total_size" in summary


class TestModelManager:
    """Test cases for model manager."""
    
    def test_model_manager_initialization(self):
        """Test model manager initialization."""
        manager = ModelManager()
        assert manager.aws_region == "us-west-2"
        assert manager.orchestration_model["model_id"]
        assert manager.analysis_model["model_id"]
    
    def test_model_manager_with_region(self):
        """Test model manager with custom region."""
        manager = ModelManager(aws_region="us-east-1")
        assert manager.aws_region == "us-east-1"


class TestServerIntegration:
    """Integration tests for the MCP server."""
    
    @pytest.mark.skipif(
        not os.getenv("AWS_ACCESS_KEY_ID"),
        reason="AWS credentials not available"
    )
    def test_health_check(self):
        """Test server health check."""
        from dwf_analyzer_mcp.server import health_check
        
        result = health_check()
        assert isinstance(result, dict)
        assert "status" in result
        assert "service" in result
    
    def test_extract_metadata_tool(self):
        """Test metadata extraction tool."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        from dwf_analyzer_mcp.server import extract_dwf_metadata
        
        result = extract_dwf_metadata(str(SAMPLE_DWF))
        assert isinstance(result, dict)
        assert "success" in result or "error" in result
    
    def test_extract_images_tool(self):
        """Test image extraction tool."""
        if not SAMPLE_DWF.exists():
            pytest.skip("Sample DWF file not available")
        
        from dwf_analyzer_mcp.server import extract_dwf_images
        
        result = extract_dwf_images(str(SAMPLE_DWF))
        assert isinstance(result, dict)
        assert "success" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
