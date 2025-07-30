"""
Configuration schemas for the DWF Analyzer MCP server.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class AWSConfig(BaseModel):
    """AWS configuration for Bedrock access."""
    
    aws_access_key_id: str = Field(
        description="AWS Access Key ID for Bedrock access"
    )
    aws_secret_access_key: str = Field(
        description="AWS Secret Access Key"
    )
    aws_region: str = Field(
        default="us-west-2",
        description="AWS Region for Bedrock service"
    )


class AnalysisConfig(BaseModel):
    """Configuration for DWF analysis parameters."""
    
    focus_area: Literal["general", "structural", "dimensions", "connectivity", "annotations"] = Field(
        default="general",
        description="Focus area for visual analysis"
    )
    max_images: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of images to extract"
    )
    output_format: Literal["json", "markdown"] = Field(
        default="json",
        description="Output format for analysis results"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include file metadata in results"
    )


class ServerConfig(BaseModel):
    """Complete server configuration."""
    
    aws: AWSConfig
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
