from pydantic import BaseModel, Field
from typing import Optional, Union

class CacheControl(BaseModel):
    """Cache control settings for content blocks."""
    type: str = Field(default="ephemeral", description="Cache control type (e.g., 'ephemeral')")


class TextContentBlock(BaseModel):
    """Text content block for system or user messages."""
    type: str = Field(default="text", description="Content block type")
    text: str = Field(..., description="The text content")
    cache_control: Optional[CacheControl] = Field(default=None, description="Optional cache control settings")


class Message(BaseModel):
    """A message in the conversation."""
    role: str = Field(..., description="The role of the message sender (e.g., 'user', 'assistant')")
    content: Union[str, list[TextContentBlock]] = Field(..., description="The message content - can be a string or list of content blocks")


class BatchParams(BaseModel):
    """Parameters for batch processing, compatible with AWS Bedrock and Anthropic batch APIs."""
    model: str = Field(..., description="The model to use (e.g., 'claude-sonnet-4-5', 'claude-3-haiku-20240307')")
    max_tokens: int = Field(default=1024, description="Maximum number of tokens to generate")
    system: Optional[Union[str, list[TextContentBlock]]] = Field(
        default=None,
        description="System prompt - can be a string or list of content blocks with optional cache control"
    )
    messages: list[Message] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Sampling temperature (0.0 to 1.0)")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(default=None, ge=0, description="Top-k sampling parameter")
    stop_sequences: Optional[list[str]] = Field(default=None, description="List of sequences that will stop generation")


class CargoLoadRequest(BaseModel):
    """Request model for loading a prompt into the batch processing queue.
    
    Compatible with AWS Bedrock batch processing and Anthropic batch API format.
    The custom_id is handled internally by the convoy app.
    """
    params: BatchParams = Field(..., description="Batch processing parameters including model, messages, and optional settings")
    callback_url: str = Field(..., description="URL to receive notification when processing is complete")
    
class CargoLoadResponse(BaseModel):
    """Response model for the cargo load operation."""
    cargo_id: str = Field(..., description="Unique identifier for the loaded cargo")
    status: str = Field(..., description="Status of the operation (e.g., 'success', 'error')")
    message: str = Field(..., description="Detailed message about the operation result")
