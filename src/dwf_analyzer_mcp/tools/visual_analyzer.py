"""
Visual analysis of DWF files using Amazon Nova Pro.
Provides comprehensive visual analysis of extracted images from DWF files.
"""

import json
import tempfile
from typing import Dict, Any, Optional
from loguru import logger

from .image_extractor import DWFImageExtractor
from ..utils.model_manager import ModelManager


class DWFVisualAnalyzer:
    """Visual analyzer for DWF files using Amazon Nova Pro."""
    
    def __init__(self, model_manager: ModelManager):
        """Initialize the visual analyzer with a model manager."""
        self.model_manager = model_manager
    
    async def analyze_drawing_image(self, image_path: str, analysis_focus: str = "general") -> Dict[str, Any]:
        """Analyze a drawing image with specified focus area."""
        logger.info(f"Starting drawing image visual analysis: {image_path}")
        
        try:
            # Extract image extractor for encoding
            extractor = DWFImageExtractor("")  # Temporary instance for encoding
            image_base64 = extractor.encode_image_to_base64(image_path)
            
            # Generate analysis prompt
            analysis_prompt = self._generate_analysis_prompt(analysis_focus)
            
            # Analyze with Nova Pro
            analysis_result = await self._analyze_with_nova_pro(
                analysis_prompt, 
                image_base64
            )
            
            return {
                "image_path": image_path,
                "analysis_focus": analysis_focus,
                "visual_analysis": analysis_result,
                "analysis_method": "nova_pro_visual",
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Drawing image analysis error: {str(e)}")
            return {
                "image_path": image_path,
                "analysis_focus": analysis_focus,
                "error": str(e),
                "analysis_method": "failed",
                "timestamp": self._get_timestamp()
            }
    
    async def analyze_dwf_comprehensive(self, file_path: str) -> Dict[str, Any]:
        """Perform comprehensive visual analysis of a DWF file."""
        logger.info(f"Starting comprehensive DWF analysis: {file_path}")
        
        try:
            # Extract images from DWF
            extractor = DWFImageExtractor(file_path)
            images = extractor.extract_embedded_images()
            
            if not images:
                return {
                    "file_path": file_path,
                    "error": "No images found in DWF file",
                    "analysis_method": "comprehensive_failed"
                }
            
            # Save images to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                saved_files = extractor.save_extracted_images(temp_dir)
                
                if not saved_files:
                    return {
                        "file_path": file_path,
                        "error": "Failed to save extracted images",
                        "analysis_method": "comprehensive_failed"
                    }
                
                # Analyze the largest/first image
                primary_image = saved_files[0]
                analysis_result = await self.analyze_drawing_image(primary_image, "general")
                
                # Get extraction summary
                extraction_summary = extractor.get_analysis_summary()
                
                return {
                    "file_path": file_path,
                    "extraction_summary": extraction_summary,
                    "primary_analysis": analysis_result,
                    "total_images_extracted": len(images),
                    "analysis_method": "comprehensive_visual",
                    "timestamp": self._get_timestamp()
                }
                
        except Exception as e:
            logger.error(f"Comprehensive DWF analysis error: {str(e)}")
            return {
                "file_path": file_path,
                "error": str(e),
                "analysis_method": "comprehensive_failed",
                "timestamp": self._get_timestamp()
            }
    
    def _generate_analysis_prompt(self, focus: str) -> str:
        """Generate analysis prompt based on focus area."""
        base_prompt = """
Analyze this drawing image and extract the following information:

1. **Drawing Type**: Architectural, mechanical, electrical, etc.
2. **Main Components**: Lines, circles, dimensions, text, symbols, etc.
3. **Numerical Information**: All visible dimensions, coordinates, measurements
4. **Structural Elements**: Walls, doors, windows, columns, etc. (for architectural drawings)
5. **Connectivity**: Line connections, intersections, closed curve areas
6. **Text Information**: All text and labels shown in the drawing
7. **Scale/Units**: Drawing scale or unit information
"""
        
        focus_additions = {
            "structural": "\\n\\nFocus particularly on structural elements (walls, columns, beams, doors, windows).",
            "dimensions": "\\n\\nFocus particularly on all dimensions and measurements, read them accurately.",
            "connectivity": "\\n\\nFocus particularly on line connections and closed curve area identification.",
            "annotations": "\\n\\nFocus particularly on all text, labels, and annotation information."
        }
        
        if focus in focus_additions:
            base_prompt += focus_additions[focus]
        
        base_prompt += "\\n\\nProvide the analysis results in a structured format."
        
        return base_prompt
    
    async def _analyze_with_nova_pro(self, prompt: str, image_base64: str) -> str:
        """Analyze with Nova Pro multimodal model."""
        try:
            # Nova Pro multimodal analysis (image + text)
            result = await self.model_manager.invoke_analysis_model_with_image(
                prompt, 
                image_base64
            )
            return result
            
        except Exception as e:
            logger.warning(f"Nova Pro analysis failed, using fallback: {str(e)}")
            return self._fallback_visual_analysis(image_base64)
    
    def _fallback_visual_analysis(self, image_base64: str) -> str:
        """Fallback visual analysis when Nova Pro fails."""
        return json.dumps({
            "analysis_method": "fallback_visual",
            "note": "Nova Pro image analysis failed, using basic analysis",
            "image_detected": True,
            "image_size_base64": len(image_base64),
            "recommendation": "Check Nova Pro image analysis API configuration and try again."
        }, indent=2, ensure_ascii=False)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
