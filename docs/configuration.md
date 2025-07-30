# Configuration Guide

## Environment Variables

The DWF Analyzer MCP Server uses environment variables for configuration.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

### Optional Variables

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `AWS_DEFAULT_REGION` | `us-west-2` | AWS Region | `us-west-2`, `us-east-1`, `eu-west-1`, `ap-southeast-1` |
| `LOG_LEVEL` | `INFO` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## MCP Client Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dwf-analyzer": {
      "command": "uvx",
      "args": ["dwf-analyzer-mcp"],
      "env": {
        "AWS_ACCESS_KEY_ID": "your-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "your-secret-access-key",
        "AWS_DEFAULT_REGION": "us-west-2",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Configuration File Locations

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Cursor IDE

Add a Command-type server in Cursor settings:

```bash
AWS_ACCESS_KEY_ID=your-key AWS_SECRET_ACCESS_KEY=your-secret AWS_DEFAULT_REGION=us-west-2 uvx dwf-analyzer-mcp
```

### Zed Editor

Add to your MCP settings in Zed:

```json
{
  "dwf-analyzer": {
    "command": "uvx",
    "args": ["dwf-analyzer-mcp"],
    "env": {
      "AWS_ACCESS_KEY_ID": "your-access-key-id",
      "AWS_SECRET_ACCESS_KEY": "your-secret-access-key",
      "AWS_DEFAULT_REGION": "us-west-2"
    }
  }
}
```

## AWS Configuration

### Supported Regions

The following AWS regions are supported:

- `us-west-2` (Oregon) - **Recommended**
- `us-east-1` (N. Virginia)
- `eu-west-1` (Ireland)
- `ap-southeast-1` (Singapore)

### Required AWS Models

Ensure you have access to these Bedrock models:

1. **Claude 3.7 Sonnet**: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
2. **Amazon Nova Pro**: `us.amazon.nova-pro-v1:0`

### IAM Permissions

Minimum required IAM policy:

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

## Analysis Configuration

### Focus Areas

The visual analysis tool supports different focus areas:

| Focus Area | Description | Use Case |
|------------|-------------|----------|
| `general` | Overall drawing analysis | Initial assessment |
| `structural` | Structural elements (walls, columns, beams) | Architectural drawings |
| `dimensions` | Measurements and dimensions | Technical specifications |
| `connectivity` | Line connections and relationships | Circuit diagrams, flow charts |
| `annotations` | Text, labels, and annotations | Documentation review |

### File Format Support

| DWF Version | Support Level | Notes |
|-------------|---------------|-------|
| V00.22 | Full | Most common format |
| V00.30 | Full | Enhanced features |
| V00.55 | Full | Advanced graphics |
| V06.00 | Full | Latest format |

### Image Format Support

Extracted images support:

- PNG (recommended)
- JPEG
- BMP
- GIF
- WEBP

## Performance Tuning

### Logging Configuration

For production environments:

```bash
export LOG_LEVEL="WARNING"  # Reduce log verbosity
```

For debugging:

```bash
export LOG_LEVEL="DEBUG"  # Detailed logging
```

### Resource Limits

- **Maximum file size**: 100MB
- **Maximum images per file**: 50
- **Analysis timeout**: 60 seconds per image

## Security Considerations

### AWS Credentials

- Never commit AWS credentials to version control
- Use IAM roles when possible (EC2, Lambda, etc.)
- Rotate access keys regularly
- Use least-privilege permissions

### Environment Variables

- Store sensitive variables in secure configuration management
- Use encrypted storage for production deployments
- Avoid logging sensitive information

## Advanced Configuration

### Custom Model Configuration

For advanced users, you can modify model parameters by extending the ModelManager class:

```python
from dwf_analyzer_mcp.utils.model_manager import ModelManager

# Custom configuration
manager = ModelManager(aws_region="us-east-1")
manager.analysis_model["temperature"] = 0.1  # More deterministic
manager.orchestration_model["max_tokens"] = 8000  # Longer responses
```

### Health Check Configuration

The health check endpoint can be configured for monitoring:

```python
# Health check returns service status
{
    "status": "healthy",
    "service": "DWF Analyzer MCP Server",
    "version": "0.1.0",
    "aws_bedrock": "connected",
    "image_processing": "available"
}
```

## Troubleshooting Configuration

### Validation Commands

Test your configuration:

```bash
# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_DEFAULT_REGION

# Test AWS connectivity
aws bedrock list-foundation-models --region us-west-2

# Test server startup
dwf-analyzer-mcp --help
```

### Common Configuration Issues

1. **Invalid region**: Ensure the region supports both Claude and Nova models
2. **Missing permissions**: Verify IAM policy includes both models
3. **Expired credentials**: Check if access keys are still valid
4. **Network issues**: Ensure outbound HTTPS access to AWS

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```bash
export LOG_LEVEL="DEBUG"
dwf-analyzer-mcp
```

This will show detailed information about:
- AWS connection attempts
- Model initialization
- Configuration validation
- Request/response details
