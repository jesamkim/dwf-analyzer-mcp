"""
DWF (Design Web Format) file parser implementation.
Extracts metadata, layers, and basic object information from DWF files.
"""

import os
import struct
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class DWFHeader:
    """DWF file header information."""
    version: str
    file_size: int
    creation_date: Optional[str] = None
    author: Optional[str] = None
    application: Optional[str] = None


@dataclass
class DWFLayer:
    """DWF layer information."""
    name: str
    visible: bool = True
    color: Optional[str] = None
    objects_count: int = 0


@dataclass
class DWFObject:
    """DWF object information."""
    object_type: str
    layer: str
    properties: Dict[str, Any]
    coordinates: Optional[List[float]] = None


class DWFParser:
    """Parser for DWF (Design Web Format) files."""
    
    def __init__(self, file_path: str):
        """Initialize the DWF parser with file path."""
        self.file_path = file_path
        self.file_size = os.path.getsize(file_path)
        self.header: Optional[DWFHeader] = None
        self.layers: List[DWFLayer] = []
        self.objects: List[DWFObject] = []
        self.raw_data: bytes = b""
        
    def parse(self) -> Dict[str, Any]:
        """Parse the complete DWF file and return structured data."""
        logger.info(f"Starting DWF file parsing: {self.file_path}")
        
        try:
            # Read file data
            self._read_file()
            
            # Parse header information
            self.header = self._parse_header()
            
            # Extract ASCII sections
            ascii_sections = self._extract_ascii_sections()
            
            # Parse layer information
            self.layers = self._parse_layers(ascii_sections)
            
            # Parse basic object information
            self.objects = self._parse_basic_objects(ascii_sections)
            
            result = {
                "header": self._header_to_dict(),
                "layers": [self._layer_to_dict(layer) for layer in self.layers],
                "objects_summary": self._get_objects_summary(),
                "file_info": {
                    "path": self.file_path,
                    "size_bytes": self.file_size,
                    "size_mb": round(self.file_size / (1024 * 1024), 2)
                },
                "ascii_sections": ascii_sections[:5]  # First 5 sections only
            }
            
            logger.info(f"DWF parsing completed: {len(self.layers)} layers, {len(self.objects)} objects")
            return result
            
        except Exception as e:
            logger.error(f"DWF parsing error: {str(e)}")
            return self._create_error_result(str(e))
    
    def _read_file(self) -> None:
        """Read the DWF file into memory."""
        with open(self.file_path, 'rb') as f:
            self.raw_data = f.read()
    
    def _parse_header(self) -> DWFHeader:
        """Parse DWF file header information."""
        try:
            # Look for DWF version signature
            version_match = re.search(rb'DWF V(\d+\.\d+)', self.raw_data)
            version = version_match.group(1).decode('ascii') if version_match else "Unknown"
            
            # Look for application information
            app_match = re.search(rb'AutoCAD[- ]([^\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\x09\\x0a\\x0b\\x0c\\x0d\\x0e\\x0f]+)', self.raw_data)
            application = app_match.group(1).decode('ascii', errors='ignore').strip() if app_match else None
            
            # If no specific app found, look for generic patterns
            if not application:
                app_patterns = [rb'r13', rb'r14', rb'r2000', rb'AutoCAD']
                for pattern in app_patterns:
                    if pattern in self.raw_data:
                        application = pattern.decode('ascii')
                        break
            
            return DWFHeader(
                version=f"V{version}",
                file_size=self.file_size,
                application=application
            )
            
        except Exception as e:
            logger.warning(f"Header parsing error: {str(e)}")
            return DWFHeader(version="Unknown", file_size=self.file_size)
    
    def _extract_ascii_sections(self) -> List[str]:
        """Extract readable ASCII sections from the DWF file."""
        ascii_sections = []
        
        try:
            # Find printable ASCII sequences
            ascii_pattern = rb'[\\x20-\\x7E]{10,}'  # Printable ASCII chars, min 10 length
            matches = re.findall(ascii_pattern, self.raw_data)
            
            for match in matches[:20]:  # Limit to first 20 matches
                try:
                    decoded = match.decode('ascii', errors='ignore')
                    if len(decoded.strip()) > 5:  # Filter out very short strings
                        ascii_sections.append(decoded)
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"ASCII section extraction error: {str(e)}")
        
        return ascii_sections
    
    def _parse_layers(self, ascii_sections: List[str]) -> List[DWFLayer]:
        """Parse layer information from ASCII sections."""
        layers = []
        
        try:
            # Look for layer patterns in ASCII sections
            layer_patterns = [
                r'Layer[\\s]*([\\w\\d_-]+)',
                r'\\(Layer[\\s]+([^)]+)\\)',
                r'layer[\\s]*:?[\\s]*([\\w\\d_-]+)'
            ]
            
            found_layers = set()
            
            for section in ascii_sections:
                for pattern in layer_patterns:
                    matches = re.findall(pattern, section, re.IGNORECASE)
                    for match in matches:
                        layer_name = match.strip()
                        if layer_name and layer_name not in found_layers:
                            found_layers.add(layer_name)
                            layers.append(DWFLayer(name=layer_name))
            
            # Add default layers if none found
            if not layers:
                layers.extend([
                    DWFLayer(name="0", color="white"),  # Default layer
                    DWFLayer(name=f"DWF {self.header.version if self.header else 'V00.22'}")
                ])
                
        except Exception as e:
            logger.warning(f"Layer parsing error: {str(e)}")
            # Fallback to default layers
            layers = [
                DWFLayer(name="0", color="white"),
                DWFLayer(name="DWF V00.22")
            ]
        
        return layers
    
    def _parse_basic_objects(self, ascii_sections: List[str]) -> List[DWFObject]:
        """Parse basic object information from ASCII sections."""
        objects = []
        
        try:
            # Look for embedded content indicators
            for section in ascii_sections:
                # Check for image embeddings
                if 'image/' in section.lower() or 'embed' in section.lower():
                    objects.append(DWFObject(
                        object_type="image",
                        layer="0",
                        properties={"content_type": "embedded_image"}
                    ))
                
                # Check for view information
                if 'view' in section.lower() and any(char.isdigit() for char in section):
                    objects.append(DWFObject(
                        object_type="view",
                        layer="0", 
                        properties={"view_data": section[:100]}
                    ))
                    
        except Exception as e:
            logger.warning(f"Object parsing error: {str(e)}")
        
        return objects
    
    def _header_to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary."""
        if not self.header:
            return {}
        
        return {
            "version": self.header.version,
            "file_size": self.header.file_size,
            "creation_date": self.header.creation_date,
            "author": self.header.author,
            "application": self.header.application
        }
    
    def _layer_to_dict(self, layer: DWFLayer) -> Dict[str, Any]:
        """Convert layer to dictionary."""
        return {
            "name": layer.name,
            "visible": layer.visible,
            "color": layer.color,
            "objects_count": layer.objects_count
        }
    
    def _get_objects_summary(self) -> Dict[str, Any]:
        """Get summary of objects by type."""
        type_counts = {}
        for obj in self.objects:
            type_counts[obj.object_type] = type_counts.get(obj.object_type, 0) + 1
        
        return {
            "total_objects": len(self.objects),
            "types": type_counts
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result structure."""
        return {
            "error": True,
            "message": error_message,
            "file_info": {
                "path": self.file_path,
                "size_bytes": self.file_size,
                "size_mb": round(self.file_size / (1024 * 1024), 2)
            }
        }
