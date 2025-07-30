# DWF Analyzer MCP Server

[![smithery badge](https://smithery.ai/badge/@jesamkim/dwf-analyzer-mcp)](https://smithery.ai/server/@jesamkim/dwf-analyzer-mcp)

A Model Context Protocol (MCP) server for analyzing DWF (Design Web Format) files using Amazon Bedrock's Nova Pro model for visual analysis.

## Features

- **DWF File Parsing**: Extract metadata, layers, and object information from DWF files
- **Image Extraction**: Extract embedded images from DWF files with format detection and conversion
- **Visual Analysis**: Analyze drawings using Amazon Nova Pro multimodal AI model
- **Comprehensive Analysis**: Combined metadata extraction, image processing, and visual analysis
- **Multiple Focus Areas**: Support for general, structural, dimensional, connectivity, and annotation analysis

## Installation

### Installing via Smithery

To install DWF Analyzer for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@jesamkim/dwf-analyzer-mcp):

```bash
npx -y @smithery/cli install @jesamkim/dwf-analyzer-mcp --client claude
```

### Prerequisites

- Python 3.12 or higher
- AWS account with Bedrock access
- AWS credentials configured

### Install from Source

```bash
git clone https://github.com/jesamkim/dwf-analyzer-mcp.git
cd dwf-analyzer-mcp
uv install
```

### Using uvx (Recommended)

```bash
uvx dwf-analyzer-mcp
```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"  # Optional, defaults to us-west-2
export LOG_LEVEL="INFO"  # Optional, defaults to INFO
```

### AWS Permissions

Your AWS credentials need the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                "arn:aws:bedrock:*::foundation-model/us.amazon.nova-pro-v1:0"
            ]
        }
    ]
}
```

## Usage

### Running the Server

```bash
# Using the installed package
dwf-analyzer-mcp

# Using uvx
uvx dwf-analyzer-mcp

# Using FastMCP directly
fastmcp run dwf_analyzer_mcp.server:mcp
```

### MCP Client Configuration

#### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dwf-analyzer": {
      "command": "uvx",
      "args": ["dwf-analyzer-mcp"],
      "env": {
        "AWS_ACCESS_KEY_ID": "your-access-key",
        "AWS_SECRET_ACCESS_KEY": "your-secret-key",
        "AWS_DEFAULT_REGION": "us-west-2"
      }
    }
  }
}
```

#### Cursor IDE

Add a Command-type server:

```bash
AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret uvx dwf-analyzer-mcp
```

#### Zed Editor

Add to your MCP settings:

```json
{
  "dwf-analyzer": {
    "command": "uvx",
    "args": ["dwf-analyzer-mcp"],
    "env": {
      "AWS_ACCESS_KEY_ID": "your-access-key",
      "AWS_SECRET_ACCESS_KEY": "your-secret-key"
    }
  }
}
```

## Available Tools

### `extract_dwf_metadata`

Extract metadata and basic information from a DWF file.

**Parameters:**
- `file_path` (string): Path to the DWF file

**Returns:** Dictionary containing file metadata, layers, and object summary

### `extract_dwf_images`

Extract embedded images from a DWF file.

**Parameters:**
- `file_path` (string): Path to the DWF file
- `output_dir` (string, optional): Directory to save extracted images

**Returns:** Dictionary containing extraction results and image information

### `analyze_dwf_visual`

Perform visual analysis of a DWF file using Amazon Nova Pro.

**Parameters:**
- `file_path` (string): Path to the DWF file
- `focus_area` (string): Analysis focus area (general, structural, dimensions, connectivity, annotations)
- `include_metadata` (boolean): Whether to include file metadata in results

**Returns:** Dictionary containing visual analysis results

### `analyze_dwf_comprehensive`

Perform comprehensive analysis including metadata, images, and visual analysis.

**Parameters:**
- `file_path` (string): Path to the DWF file

**Returns:** Dictionary containing complete analysis results

### `health_check`

Perform a health check of the service.

**Returns:** Dictionary containing service health status

## Available Resources

### `dwf://analysis/config`

Get the current analysis configuration schema.

### `dwf://analysis/supported-formats`

Get information about supported DWF formats and capabilities.

## Supported Formats

- **DWF Versions**: V00.22, V00.30, V00.55, V06.00
- **Image Formats**: PNG, JPEG, BMP, GIF, WEBP
- **Max File Size**: 100MB
- **AWS Regions**: us-west-2, us-east-1, eu-west-1, ap-southeast-1

## Analysis Focus Areas

- **general**: Overall drawing analysis
- **structural**: Focus on structural elements (walls, columns, beams)
- **dimensions**: Focus on measurements and dimensions
- **connectivity**: Focus on line connections and relationships
- **annotations**: Focus on text, labels, and annotations

## Development

### Setup Development Environment

```bash
git clone https://github.com/jesamkim/dwf-analyzer-mcp.git
cd dwf-analyzer-mcp
uv install --dev
```

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black src tests
uv run ruff check src tests
```

### Type Checking

```bash
uv run mypy src
```

## Examples

### Basic Usage

```python
# Extract metadata from a DWF file
result = extract_dwf_metadata("/path/to/drawing.dwf")
print(result["metadata"]["header"]["version"])

# Extract images
images = extract_dwf_images("/path/to/drawing.dwf", "/output/directory")
print(f"Extracted {images['extracted_images']} images")

# Perform visual analysis
analysis = analyze_dwf_visual("/path/to/drawing.dwf", focus_area="structural")
print(analysis["visual_analysis"])
```

### Comprehensive Analysis

```python
# Perform complete analysis
result = analyze_dwf_comprehensive("/path/to/drawing.dwf")

# Access different parts of the analysis
metadata = result["metadata"]
images = result["image_extraction"]
visual = result["visual_analysis"]
```

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   - Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set
   - Verify your AWS account has Bedrock access

2. **Model Access Error**
   - Check if Nova Pro model is available in your AWS region
   - Verify your AWS permissions include bedrock:InvokeModel

3. **Image Processing Error**
   - Ensure Pillow is installed: `pip install pillow`
   - Check if the DWF file contains extractable images

4. **File Not Found Error**
   - Verify the DWF file path is correct and accessible
   - Check file permissions

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
dwf-analyzer-mcp
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.


## Changelog

### v0.1.0

- Initial release
- Basic DWF parsing functionality
- Image extraction capabilities
- Amazon Nova Pro integration
- FastMCP server implementation
- Comprehensive analysis tools
