"""
FastMCP server implementation for DWF file analysis.
Provides tools for parsing DWF files, extracting images, and performing visual analysis.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from loguru import logger

from .tools.dwf_parser import DWFParser
from .tools.image_extractor import DWFImageExtractor
from .tools.visual_analyzer import DWFVisualAnalyzer
from .utils.model_manager import ModelManager
from .utils.metrics import get_metrics_collector, track_tool_usage
from .resources.schemas import AnalysisConfig


# Initialize FastMCP server
mcp = FastMCP(
    "DWF Analyzer",
    dependencies=["boto3", "pillow", "loguru", "pydantic"]
)

# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get or create the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        aws_region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
        _model_manager = ModelManager(aws_region=aws_region)
    return _model_manager


@track_tool_usage("extract_dwf_metadata")
@mcp.tool()
def extract_dwf_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract metadata and basic information from a DWF file.
    
    Args:
        file_path: Path to the DWF file to analyze
        
    Returns:
        Dictionary containing file metadata, layers, and object summary
    """
    logger.info(f"Starting DWF metadata extraction: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            return {
                "error": True,
                "message": f"File not found: {file_path}"
            }
        
        parser = DWFParser(file_path)
        result = parser.parse()
        
        logger.info(f"Metadata extraction completed for: {file_path}")
        return {
            "success": True,
            "file_path": file_path,
            "metadata": result
        }
        
    except Exception as e:
        error_msg = f"Metadata extraction failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": True,
            "message": error_msg,
            "file_path": file_path
        }


@track_tool_usage("extract_dwf_images")
@mcp.tool()
def extract_dwf_images(file_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract embedded images from a DWF file.
    
    Args:
        file_path: Path to the DWF file
        output_dir: Optional directory to save extracted images
        
    Returns:
        Dictionary containing extraction results and image information
    """
    logger.info(f"Starting DWF image extraction: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            return {
                "error": True,
                "message": f"File not found: {file_path}"
            }
        
        extractor = DWFImageExtractor(file_path)
        images = extractor.extract_embedded_images()
        
        result = {
            "success": True,
            "file_path": file_path,
            "extraction_summary": extractor.get_analysis_summary(),
            "extracted_images": len(images)
        }
        
        # Save images if output directory is specified
        if output_dir and images:
            saved_files = extractor.save_extracted_images(output_dir)
            result["saved_files"] = saved_files
            result["output_directory"] = output_dir
        
        logger.info(f"Image extraction completed: {len(images)} images found")
        return result
        
    except Exception as e:
        error_msg = f"Image extraction failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": True,
            "message": error_msg,
            "file_path": file_path
        }


@track_tool_usage("analyze_dwf_visual")
@mcp.tool()
async def analyze_dwf_visual(
    file_path: str, 
    focus_area: str = "general",
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Perform visual analysis of a DWF file using Amazon Nova Pro.
    
    Args:
        file_path: Path to the DWF file to analyze
        focus_area: Analysis focus area (general, structural, dimensions, connectivity, annotations)
        include_metadata: Whether to include file metadata in results
        
    Returns:
        Dictionary containing visual analysis results
    """
    logger.info(f"Starting DWF visual analysis: {file_path}, focus: {focus_area}")
    
    try:
        if not os.path.exists(file_path):
            return {
                "error": True,
                "message": f"File not found: {file_path}"
            }
        
        # Validate focus area
        valid_focus_areas = ["general", "structural", "dimensions", "connectivity", "annotations"]
        if focus_area not in valid_focus_areas:
            return {
                "error": True,
                "message": f"Invalid focus area. Must be one of: {valid_focus_areas}"
            }
        
        # Get model manager
        model_manager = get_model_manager()
        analyzer = DWFVisualAnalyzer(model_manager)
        
        # Perform comprehensive analysis
        analysis_result = await analyzer.analyze_dwf_comprehensive(file_path)
        
        result = {
            "success": True,
            "file_path": file_path,
            "focus_area": focus_area,
            "visual_analysis": analysis_result
        }
        
        # Include metadata if requested
        if include_metadata:
            try:
                parser = DWFParser(file_path)
                metadata = parser.parse()
                result["metadata"] = metadata
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {str(e)}")
        
        logger.info(f"Visual analysis completed for: {file_path}")
        return result
        
    except Exception as e:
        error_msg = f"Visual analysis failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": True,
            "message": error_msg,
            "file_path": file_path,
            "focus_area": focus_area
        }


@track_tool_usage("analyze_dwf_comprehensive")
@mcp.tool()
async def analyze_dwf_comprehensive(file_path: str) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of a DWF file including metadata, images, and visual analysis.
    
    Args:
        file_path: Path to the DWF file to analyze
        
    Returns:
        Dictionary containing complete analysis results
    """
    logger.info(f"Starting comprehensive DWF analysis: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            return {
                "error": True,
                "message": f"File not found: {file_path}"
            }
        
        results = {
            "success": True,
            "file_path": file_path,
            "analysis_type": "comprehensive"
        }
        
        # 1. Extract metadata
        try:
            parser = DWFParser(file_path)
            metadata = parser.parse()
            results["metadata"] = metadata
            logger.info("Metadata extraction completed")
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {str(e)}")
            results["metadata_error"] = str(e)
        
        # 2. Extract images
        try:
            extractor = DWFImageExtractor(file_path)
            images = extractor.extract_embedded_images()
            results["image_extraction"] = {
                "summary": extractor.get_analysis_summary(),
                "images_found": len(images)
            }
            logger.info(f"Image extraction completed: {len(images)} images")
        except Exception as e:
            logger.warning(f"Image extraction failed: {str(e)}")
            results["image_extraction_error"] = str(e)
        
        # 3. Visual analysis (if images were found)
        if "image_extraction" in results and results["image_extraction"]["images_found"] > 0:
            try:
                model_manager = get_model_manager()
                analyzer = DWFVisualAnalyzer(model_manager)
                visual_analysis = await analyzer.analyze_dwf_comprehensive(file_path)
                results["visual_analysis"] = visual_analysis
                logger.info("Visual analysis completed")
            except Exception as e:
                logger.warning(f"Visual analysis failed: {str(e)}")
                results["visual_analysis_error"] = str(e)
        else:
            results["visual_analysis"] = {
                "note": "No images found for visual analysis"
            }
        
        logger.info(f"Comprehensive analysis completed for: {file_path}")
        return results
        
    except Exception as e:
        error_msg = f"Comprehensive analysis failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": True,
            "message": error_msg,
            "file_path": file_path
        }


@mcp.resource("dwf://analysis/config")
def get_analysis_config() -> str:
    """Get the current analysis configuration schema."""
    config = AnalysisConfig()
    return json.dumps(config.model_dump(), indent=2)


@mcp.resource("dwf://analysis/supported-formats")
def get_supported_formats() -> str:
    """Get information about supported DWF formats and capabilities."""
    return json.dumps({
        "supported_dwf_versions": [
            "V00.22", "V00.30", "V00.55", "V06.00"
        ],
        "supported_image_formats": [
            "PNG", "JPEG", "BMP", "GIF", "WEBP"
        ],
        "analysis_focus_areas": [
            "general", "structural", "dimensions", "connectivity", "annotations"
        ],
        "max_file_size_mb": 100,
        "aws_regions_supported": [
            "us-west-2", "us-east-1", "eu-west-1", "ap-southeast-1"
        ]
    }, indent=2)


# Health check endpoint
@track_tool_usage("health_check")
@mcp.tool()
def health_check() -> Dict[str, Any]:
    """
    Perform a health check of the DWF analyzer service.
    
    Returns:
        Dictionary containing service health status
    """
    try:
        # Check AWS connection
        model_manager = get_model_manager()
        aws_status = "connected"
        
        # Check PIL availability
        try:
            from PIL import Image
            pil_status = "available"
        except ImportError:
            pil_status = "not_available"
        
        return {
            "status": "healthy",
            "service": "DWF Analyzer MCP Server",
            "version": "0.2.0",
            "aws_bedrock": aws_status,
            "image_processing": pil_status,
            "timestamp": _get_current_timestamp()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": _get_current_timestamp()
        }


@mcp.tool()
def get_usage_statistics(hours: int = 24) -> Dict[str, Any]:
    """
    Get tool usage statistics for the specified time period.
    
    Args:
        hours: Number of hours to look back (default: 24)
        
    Returns:
        Dictionary containing usage statistics
    """
    try:
        collector = get_metrics_collector()
        stats = collector.get_tool_usage_stats(hours)
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": _get_current_timestamp()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to get usage statistics: {str(e)}",
            "timestamp": _get_current_timestamp()
        }


@mcp.tool()
def get_error_statistics() -> Dict[str, Any]:
    """
    Get error statistics and common failure patterns.
    
    Returns:
        Dictionary containing error statistics
    """
    try:
        collector = get_metrics_collector()
        error_stats = collector.get_error_statistics()
        
        return {
            "success": True,
            "error_statistics": error_stats,
            "timestamp": _get_current_timestamp()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to get error statistics: {str(e)}",
            "timestamp": _get_current_timestamp()
        }


@mcp.tool()
def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance metrics including response times and throughput.
    
    Returns:
        Dictionary containing performance metrics
    """
    try:
        collector = get_metrics_collector()
        perf_metrics = collector.get_performance_metrics()
        
        return {
            "success": True,
            "performance_metrics": perf_metrics,
            "timestamp": _get_current_timestamp()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to get performance metrics: {str(e)}",
            "timestamp": _get_current_timestamp()
        }


@mcp.tool()
def export_metrics_report(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Export comprehensive metrics report to JSON file.
    
    Args:
        file_path: Optional path to save the report (default: auto-generated)
        
    Returns:
        Dictionary containing export status and report data
    """
    try:
        collector = get_metrics_collector()
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"dwf_analyzer_metrics_{timestamp}.json"
        
        report_data = collector.export_metrics(file_path)
        
        return {
            "success": True,
            "message": f"Metrics report exported to: {file_path}",
            "file_path": file_path,
            "report_size_bytes": len(report_data),
            "timestamp": _get_current_timestamp()
        }
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to export metrics report: {str(e)}",
            "timestamp": _get_current_timestamp()
        }


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()


# Export the MCP server instance
__all__ = ["mcp"]
