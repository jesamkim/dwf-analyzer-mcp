# Installation Guide

## Prerequisites

Before installing the DWF Analyzer MCP Server, ensure you have:

1. **Python 3.12 or higher**
2. **AWS Account with Bedrock access**
3. **AWS Credentials configured**

## Installation Methods

### Method 1: Using uvx (Recommended)

The easiest way to install and run the DWF Analyzer MCP Server:

```bash
uvx dwf-analyzer-mcp
```

This will automatically install the package and its dependencies in an isolated environment.

### Method 2: Using pip

```bash
pip install dwf-analyzer-mcp
```

Then run with:

```bash
dwf-analyzer-mcp
```

### Method 3: From Source

For development or customization:

```bash
git clone https://github.com/jesamkim/dwf-analyzer-mcp.git
cd dwf-analyzer-mcp
uv install
uv run python -m dwf_analyzer_mcp
```

## AWS Setup

### 1. Create AWS Account

If you don't have an AWS account, create one at [aws.amazon.com](https://aws.amazon.com).

### 2. Enable Bedrock Access

1. Go to the AWS Bedrock console
2. Request access to the following models:
   - Claude 3.7 Sonnet
   - Amazon Nova Pro

### 3. Create IAM User

Create an IAM user with the following policy:

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

### 4. Get Access Keys

1. Go to IAM > Users > [Your User] > Security credentials
2. Create access key
3. Save the Access Key ID and Secret Access Key

## Environment Configuration

Set the following environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-west-2"  # Optional
export LOG_LEVEL="INFO"  # Optional
```

### Persistent Configuration

#### Linux/macOS

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export AWS_ACCESS_KEY_ID="your-access-key-id"' >> ~/.bashrc
echo 'export AWS_SECRET_ACCESS_KEY="your-secret-access-key"' >> ~/.bashrc
echo 'export AWS_DEFAULT_REGION="us-west-2"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows

Set environment variables through System Properties or use PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("AWS_ACCESS_KEY_ID", "your-access-key-id", "User")
[Environment]::SetEnvironmentVariable("AWS_SECRET_ACCESS_KEY", "your-secret-access-key", "User")
[Environment]::SetEnvironmentVariable("AWS_DEFAULT_REGION", "us-west-2", "User")
```

## Verification

Test your installation:

```bash
# Set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Run the server (it should start without errors)
dwf-analyzer-mcp
```

You should see output like:

```
2025-01-30 10:00:00 | INFO | Starting DWF Analyzer MCP Server
2025-01-30 10:00:00 | INFO | Using AWS region: us-west-2
2025-01-30 10:00:00 | INFO | Initializing FastMCP server...
```

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set
   - Check spelling and ensure no extra spaces

2. **"Model access denied"**
   - Verify Bedrock model access in AWS console
   - Check IAM permissions

3. **"Region not supported"**
   - Use supported regions: us-west-2, us-east-1, eu-west-1, ap-southeast-1
   - Ensure the models are available in your chosen region

4. **"Python version error"**
   - Ensure Python 3.12 or higher is installed
   - Use `python --version` to check

### Getting Help

- Check the [main README](../README.md) for usage examples
- Review [configuration guide](configuration.md) for advanced settings
- Open an issue on [GitHub](https://github.com/jesamkim/dwf-analyzer-mcp/issues)
