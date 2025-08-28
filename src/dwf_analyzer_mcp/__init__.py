"""
DWF Analyzer MCP Server

A Model Context Protocol server for analyzing DWF (Design Web Format) files
using Amazon Bedrock's Nova Pro model for visual analysis.
"""

__version__ = "0.1.0"
__author__ = "DWF Analysis Team"
__email__ = "team@example.com"

from .server import mcp

__all__ = ["mcp"]
