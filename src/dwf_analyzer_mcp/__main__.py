"""
Main entry point for the DWF Analyzer MCP Server.
"""

import sys
import os
from loguru import logger

from .server import mcp


def setup_logging():
    """Configure logging for the MCP server."""
    # Remove default logger
    logger.remove()
    
    # Add console logger with appropriate level
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


def check_environment():
    """Check required environment variables and dependencies."""
    required_env_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please set the following environment variables:")
        logger.info("- AWS_ACCESS_KEY_ID: Your AWS access key")
        logger.info("- AWS_SECRET_ACCESS_KEY: Your AWS secret key")
        logger.info("- AWS_DEFAULT_REGION: AWS region (optional, defaults to us-west-2)")
        return False
    
    # Check optional variables
    aws_region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    logger.info(f"Using AWS region: {aws_region}")
    
    return True


def main():
    """Main entry point for the DWF Analyzer MCP Server."""
    setup_logging()
    
    logger.info("Starting DWF Analyzer MCP Server")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    try:
        # Run the FastMCP server with HTTP transport
        logger.info("Initializing FastMCP server with HTTP transport...")
        port = int(os.getenv("PORT", "8080"))
        host = os.getenv("HOST", "0.0.0.0")
        
        logger.info(f"Server starting on {host}:{port}")
        mcp.run(transport="streamable-http", host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
