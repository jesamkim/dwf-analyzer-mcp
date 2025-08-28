"""
DWF image extraction and processing utilities.
Extracts embedded images from DWF files and prepares them for visual analysis.
"""

import os
import re
import base64
import tempfile
import struct
import io
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from loguru import logger

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available - image format detection will be limited")


class DWFImageExtractor:
    """Extracts and processes embedded images from DWF files."""
    
    def __init__(self, dwf_file_path: str):
        """Initialize the image extractor with DWF file path."""
        self.dwf_file_path = dwf_file_path
        self.extracted_images: List[Dict[str, Any]] = []
        
    def extract_embedded_images(self) -> List[Dict[str, Any]]:
        """Extract all embedded images from the DWF file."""
        logger.info(f"Starting embedded image extraction: {self.dwf_file_path}")
        
        try:
            with open(self.dwf_file_path, 'rb') as f:
                dwf_data = f.read()
            
            # Search for various image format patterns
            image_patterns = [
                self._extract_dwg_embedded_images(dwf_data),
                self._extract_png_images(dwf_data),
                self._extract_jpeg_images(dwf_data),
                self._extract_bitmap_images(dwf_data),
            ]
            
            # Collect images found by all patterns
            for images in image_patterns:
                self.extracted_images.extend(images)
            
            logger.info(f"Total {len(self.extracted_images)} images extracted")
            return self.extracted_images
            
        except Exception as e:
            logger.error(f"Image extraction error: {str(e)}")
            return []
    
    def _extract_dwg_embedded_images(self, data: bytes) -> List[Dict[str, Any]]:
        """Extract DWG embedded images."""
        images = []
        
        # Look for DWG embedded patterns
        patterns = [
            rb'image/vnd\.dwg',
            rb'Embed.*?image',
            rb'AutoCAD.*?image'
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, data, re.IGNORECASE))
            for match in matches:
                start_pos = match.start()
                # Extract a reasonable chunk of data after the pattern
                end_pos = min(start_pos + 50000, len(data))
                image_data = data[start_pos:end_pos]
                
                images.append({
                    "type": "dwg_embedded",
                    "format": "unknown",
                    "size": len(image_data),
                    "data": image_data,
                    "position": start_pos
                })
        
        return images
    
    def _extract_png_images(self, data: bytes) -> List[Dict[str, Any]]:
        """Extract PNG images from the data."""
        images = []
        png_signature = b'\\x89PNG\\r\\n\\x1a\\n'
        
        start = 0
        while True:
            pos = data.find(png_signature, start)
            if pos == -1:
                break
                
            # Find the end of PNG (IEND chunk)
            iend_pos = data.find(b'IEND', pos)
            if iend_pos != -1:
                end_pos = iend_pos + 8  # IEND + 4 bytes CRC
                image_data = data[pos:end_pos]
                
                images.append({
                    "type": "png",
                    "format": "png",
                    "size": len(image_data),
                    "data": image_data,
                    "position": pos
                })
            
            start = pos + 1
        
        return images
    
    def _extract_jpeg_images(self, data: bytes) -> List[Dict[str, Any]]:
        """Extract JPEG images from the data."""
        images = []
        jpeg_signature = b'\\xff\\xd8\\xff'
        
        start = 0
        while True:
            pos = data.find(jpeg_signature, start)
            if pos == -1:
                break
                
            # Find the end of JPEG (EOI marker)
            eoi_pos = data.find(b'\\xff\\xd9', pos)
            if eoi_pos != -1:
                end_pos = eoi_pos + 2
                image_data = data[pos:end_pos]
                
                images.append({
                    "type": "jpeg",
                    "format": "jpeg",
                    "size": len(image_data),
                    "data": image_data,
                    "position": pos
                })
            
            start = pos + 1
        
        return images
    
    def _extract_bitmap_images(self, data: bytes) -> List[Dict[str, Any]]:
        """Extract BMP images from the data."""
        images = []
        bmp_signature = b'BM'
        
        start = 0
        while True:
            pos = data.find(bmp_signature, start)
            if pos == -1:
                break
                
            # Read BMP header to get file size
            if pos + 6 <= len(data):
                try:
                    file_size = struct.unpack('<I', data[pos+2:pos+6])[0]
                    if file_size > 0 and pos + file_size <= len(data):
                        image_data = data[pos:pos+file_size]
                        
                        images.append({
                            "type": "bmp",
                            "format": "bmp",
                            "size": len(image_data),
                            "data": image_data,
                            "position": pos
                        })
                except:
                    pass
            
            start = pos + 1
        
        return images
    
    def save_extracted_images(self, output_dir: str) -> List[str]:
        """Save extracted images to files."""
        if not self.extracted_images:
            return []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []
        
        base_name = Path(self.dwf_file_path).stem
        
        for i, image_info in enumerate(self.extracted_images):
            try:
                file_extension = image_info.get("format", "bin")
                filename = f"{base_name}_image_{i}_{image_info['type']}.{file_extension}"
                file_path = os.path.join(output_dir, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(image_info["data"])
                
                saved_files.append(file_path)
                logger.info(f"Image saved: {file_path} ({image_info['size']} bytes)")
                
            except Exception as e:
                logger.error(f"Error saving image {i}: {str(e)}")
        
        return saved_files
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of extracted images for analysis."""
        if not self.extracted_images:
            return {
                "total_images": 0,
                "image_types": {},
                "total_size": 0,
                "largest_image": None
            }
        
        # Count by type
        type_counts = {}
        total_size = 0
        largest_image = None
        largest_size = 0
        
        for image in self.extracted_images:
            img_type = image["type"]
            type_counts[img_type] = type_counts.get(img_type, 0) + 1
            total_size += image["size"]
            
            if image["size"] > largest_size:
                largest_size = image["size"]
                largest_image = {
                    "type": image["type"],
                    "format": image["format"],
                    "size": image["size"],
                    "position": image["position"]
                }
        
        return {
            "total_images": len(self.extracted_images),
            "image_types": type_counts,
            "total_size": total_size,
            "largest_image": largest_image
        }
    
    def _detect_image_format(self, data: bytes) -> Optional[str]:
        """Detect image format from binary data using magic bytes."""
        if not data:
            return None
            
        # Magic byte detection
        if data.startswith(b'\\x89PNG\\r\\n\\x1a\\n'):
            return 'png'
        elif data.startswith(b'\\xff\\xd8\\xff'):
            return 'jpeg'
        elif data.startswith(b'BM'):
            return 'bmp'
        elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
            return 'gif'
        elif data.startswith(b'RIFF') and b'WEBP' in data[:12]:
            return 'webp'
        
        # Try PIL for additional detection
        if PIL_AVAILABLE:
            try:
                with Image.open(io.BytesIO(data)) as img:
                    return img.format.lower()
            except Exception:
                pass
        
        return None
    
    def _convert_to_png(self, data: bytes) -> Optional[bytes]:
        """Convert image data to PNG format."""
        if not PIL_AVAILABLE:
            logger.warning("PIL not available - cannot convert image format")
            return None
            
        try:
            # Open original image
            with Image.open(io.BytesIO(data)) as img:
                # Convert to RGBA mode (supports transparency)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA')
                
                # Save as PNG
                output = io.BytesIO()
                img.save(output, format='PNG')
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"Image conversion error: {str(e)}")
            return None
    
    def _create_fallback_image(self, width: int = 100, height: int = 100) -> bytes:
        """Create a fallback image for unanalyzable data."""
        if not PIL_AVAILABLE:
            return b''
            
        try:
            # Create simple gray image
            img = Image.new('RGB', (width, height), color='lightgray')
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception:
            return b''
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 with format detection and conversion."""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Detect image format
            detected_format = self._detect_image_format(image_data)
            logger.info(f"Detected image format: {detected_format}")
            
            # Convert to PNG if not already PNG
            if detected_format and detected_format != 'png':
                logger.info(f"Converting from {detected_format} to PNG")
                converted_data = self._convert_to_png(image_data)
                if converted_data:
                    image_data = converted_data
                    logger.info("PNG conversion successful")
                else:
                    logger.warning("PNG conversion failed, using original data")
            elif not detected_format:
                # Create fallback image if format cannot be detected
                logger.warning("Image format detection failed, creating fallback image")
                fallback_data = self._create_fallback_image()
                if fallback_data:
                    image_data = fallback_data
                    logger.info("Fallback image created")
            
            return base64.b64encode(image_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Image encoding error: {str(e)}")
            # Create fallback image on error
            fallback_data = self._create_fallback_image()
            if fallback_data:
                return base64.b64encode(fallback_data).decode('utf-8')
            return ""
