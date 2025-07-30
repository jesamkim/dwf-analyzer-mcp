"""
Model manager for AWS Bedrock integration.
Handles both orchestration (Claude 3.7 Sonnet) and analysis (Nova Pro) models.
"""

import boto3
import json
import base64
from typing import Dict, Any, Optional
from loguru import logger


class ModelManager:
    """Manages AWS Bedrock model interactions for DWF analysis."""
    
    def __init__(self, aws_region: str = "us-west-2"):
        """Initialize the model manager with AWS Bedrock client."""
        self.aws_region = aws_region
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=aws_region
        )
        
        # Model configurations
        self.orchestration_model = {
            "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            "max_tokens": 4000,
            "temperature": 0.1
        }
        
        self.analysis_model = {
            "model_id": "us.amazon.nova-pro-v1:0",
            "max_tokens": 2000,
            "temperature": 0.3
        }
        
        logger.info(f"ModelManager initialized with region: {aws_region}")
    
    async def invoke_orchestration_model(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Invoke the orchestration model (Claude 3.7 Sonnet).
        
        Args:
            prompt: User prompt for orchestration
            context: Additional context information
            
        Returns:
            Model response as string
        """
        try:
            logger.info("Invoking Claude 3.7 Sonnet orchestration model")
            
            # Prepare the full prompt
            full_prompt = self._prepare_orchestration_prompt(prompt, context)
            
            # Call Claude 3.7 Sonnet
            response = self.bedrock_client.invoke_model(
                modelId=self.orchestration_model["model_id"],
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.orchestration_model["max_tokens"],
                    "temperature": self.orchestration_model["temperature"],
                    "messages": [
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text']
            
            logger.info(f"Orchestration model response length: {len(content)} characters")
            return content
            
        except Exception as e:
            error_msg = f"Orchestration model invocation error: {str(e)}"
            logger.error(error_msg)
            return self._fallback_orchestration_response(prompt)
    
    async def invoke_analysis_model_with_image(self, prompt: str, image_base64: str) -> str:
        """
        Invoke the analysis model (Nova Pro) with image input.
        
        Args:
            prompt: Analysis prompt
            image_base64: Base64 encoded image data
            
        Returns:
            Analysis result as string
        """
        try:
            logger.info("Invoking Amazon Nova Pro image analysis model")
            
            # Nova Pro multimodal API call (correct format for Invoke API)
            response = self.bedrock_client.invoke_model(
                modelId=self.analysis_model["model_id"],
                body=json.dumps({
                    "schemaVersion": "messages-v1",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": {
                                        "format": "png",
                                        "source": {
                                            "bytes": image_base64  # Invoke API uses base64 string
                                        }
                                    }
                                },
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": self.analysis_model["max_tokens"],
                        "temperature": self.analysis_model["temperature"]
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            # Nova Pro response structure
            if 'output' in result and 'message' in result['output']:
                content = result['output']['message']['content'][0]['text']
            else:
                content = str(result)
            
            logger.info(f"Image analysis model response length: {len(content)} characters")
            return content
            
        except Exception as e:
            error_msg = f"Image analysis model invocation error: {str(e)}"
            logger.error(error_msg)
            return self._fallback_image_analysis(prompt, len(image_base64))
    
    def _prepare_orchestration_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Prepare the orchestration prompt with system instructions."""
        system_prompt = """You are an expert DWF (Design Web Format) file analysis orchestrator.
Your role is to coordinate the analysis of DWF files by planning analysis steps and interpreting results.

Key responsibilities:
1. Create structured analysis plans for DWF files
2. Coordinate metadata extraction, image extraction, and visual analysis
3. Synthesize results from multiple analysis tools
4. Provide comprehensive summaries and insights

Always respond in a structured, professional manner with clear analysis steps and findings."""
        
        full_prompt = system_prompt
        if context:
            full_prompt += f"\n\nContext:\n{context}"
        full_prompt += f"\n\nUser Request:\n{prompt}"
        
        return full_prompt
    
    def _fallback_orchestration_response(self, prompt: str) -> str:
        """Fallback response when orchestration model fails."""
        logger.warning("Using fallback orchestration response")
        return json.dumps({
            "analysis_method": "fallback_orchestration",
            "note": "Orchestration model failed, using basic analysis plan",
            "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "recommendation": "Check AWS Bedrock configuration and try again."
        }, indent=2, ensure_ascii=False)
    
    def _fallback_image_analysis(self, prompt: str, image_size: int) -> str:
        """Fallback response when Nova Pro image analysis fails."""
        logger.warning("Nova Pro image analysis failed, using fallback analysis")
        
        fallback_result = {
            "analysis_method": "fallback_image_analysis",
            "note": "Nova Pro image analysis failed, using basic analysis",
            "prompt": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "image_available": True,
            "image_size_base64": image_size,
            "recommendation": "Check Nova Pro image analysis API configuration and try again.",
            "basic_analysis": {
                "image_detected": True,
                "analysis_possible": "Image successfully extracted, detailed analysis available after Nova Pro connection",
                "suggested_analysis": [
                    "Drawing type identification",
                    "Structural element recognition", 
                    "Dimension and numerical information extraction",
                    "Text and label recognition",
                    "Line connectivity analysis"
                ]
            }
        }
        
        return json.dumps(fallback_result, indent=2, ensure_ascii=False)
