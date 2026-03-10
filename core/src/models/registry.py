"""Model registry containing provider-agnostic model definitions and mappings.

This module defines the single source of truth for all supported models,
their provider-specific identifiers, and regional availability for Bedrock.

To add a new model or update regional availability:
1. Add/update the entry in MODEL_REGISTRY
2. Redeploy the application

References:
- Anthropic API models: https://platform.claude.com/docs/en/about-claude/models/overview
- Bedrock batch inference: https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-supported.html
- Amazon Nova models: https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html
- DeepSeek models: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
"""

from dataclasses import dataclass, field
from enum import Enum


class Provider(str, Enum):
    """Supported batch processing providers."""

    BEDROCK = "bedrock"
    ANTHROPIC = "anthropic"


@dataclass
class ModelMapping:
    """Mapping for a single model across providers.

    Attributes:
        convoy_id: Provider-agnostic model identifier used in API requests.
        anthropic_id: Anthropic API model identifier, or None if not available.
        bedrock_id: AWS Bedrock model identifier, or None if not available.
        bedrock_regions: List of AWS regions where Bedrock batch inference is available.
        description: Human-readable description of the model.
        deprecated: Whether this model is deprecated (still works but not recommended).
        model_family: The model family/provider (e.g., "anthropic", "amazon", "deepseek").
    """

    convoy_id: str
    anthropic_id: str | None
    bedrock_id: str | None
    bedrock_regions: list[str] = field(default_factory=list)
    description: str = ""
    deprecated: bool = False
    model_family: str = "anthropic"


# =============================================================================
# MODEL REGISTRY - Single source of truth for all supported models
# =============================================================================
#
# To update this registry:
# 1. Check Anthropic API docs for latest model identifiers:
#    https://platform.claude.com/docs/en/about-claude/models/overview
# 2. Check AWS Bedrock docs for model IDs and regional availability:
#    https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-supported.html
# 3. Update the entries below
# 4. Redeploy the application
#
# Note: Some models are only available on Anthropic API (bedrock_id=None)
# =============================================================================

MODEL_REGISTRY: dict[str, ModelMapping] = {
    # =========================================================================
    # ANTHROPIC CLAUDE MODELS
    # =========================================================================

    # -------------------------------------------------------------------------
    # Claude 3 Models (Available on both Anthropic and Bedrock)
    # -------------------------------------------------------------------------
    "claude-3-haiku": ModelMapping(
        convoy_id="claude-3-haiku",
        anthropic_id="claude-3-haiku-20240307",
        bedrock_id="anthropic.claude-3-haiku-20240307-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "eu-west-3",
            "ap-northeast-1",
            "ap-southeast-2",
        ],
        description="Claude 3 Haiku - Fast and efficient for simple tasks",
        model_family="anthropic",
    ),
    "claude-3-sonnet": ModelMapping(
        convoy_id="claude-3-sonnet",
        anthropic_id="claude-3-sonnet-20240229",
        bedrock_id="anthropic.claude-3-sonnet-20240229-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "ap-northeast-1",
        ],
        description="Claude 3 Sonnet - Balanced performance and capability",
        model_family="anthropic",
    ),
    "claude-3-opus": ModelMapping(
        convoy_id="claude-3-opus",
        anthropic_id="claude-3-opus-20240229",
        bedrock_id="anthropic.claude-3-opus-20240229-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Claude 3 Opus - Most capable Claude 3 model",
        model_family="anthropic",
    ),

    # -------------------------------------------------------------------------
    # Claude 3.5 Models
    # -------------------------------------------------------------------------
    # Claude 3.5 Sonnet v1 - Original version (Anthropic only)
    "claude-3.5-sonnet-v1": ModelMapping(
        convoy_id="claude-3.5-sonnet-v1",
        anthropic_id="claude-3-5-sonnet-20240620",
        bedrock_id=None,  # Not available on Bedrock batch inference
        bedrock_regions=[],
        description="Claude 3.5 Sonnet v1 - Original 3.5 Sonnet (Anthropic only)",
        model_family="anthropic",
    ),
    # Claude 3.5 Haiku (Available on both)
    "claude-3.5-haiku": ModelMapping(
        convoy_id="claude-3.5-haiku",
        anthropic_id="claude-3-5-haiku-20241022",
        bedrock_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "ap-northeast-1",
        ],
        description="Claude 3.5 Haiku - Improved speed and efficiency",
        model_family="anthropic",
    ),
    # Claude 3.5 Sonnet v2 (Available on both)
    "claude-3.5-sonnet": ModelMapping(
        convoy_id="claude-3.5-sonnet",
        anthropic_id="claude-3-5-sonnet-20241022",
        bedrock_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "eu-central-1",
            "ap-northeast-1",
            "ap-southeast-2",
        ],
        description="Claude 3.5 Sonnet v2 - Enhanced reasoning and analysis",
        model_family="anthropic",
    ),

    # -------------------------------------------------------------------------
    # Claude 3.7 Models (Anthropic only - Extended thinking)
    # -------------------------------------------------------------------------
    "claude-3.7-sonnet": ModelMapping(
        convoy_id="claude-3.7-sonnet",
        anthropic_id="claude-3-7-sonnet-20250219",
        bedrock_id=None,  # Not available on Bedrock batch inference
        bedrock_regions=[],
        description="Claude 3.7 Sonnet - Extended thinking capabilities (Anthropic only)",
        model_family="anthropic",
    ),

    # -------------------------------------------------------------------------
    # Claude 4 Models
    # -------------------------------------------------------------------------
    "claude-sonnet-4": ModelMapping(
        convoy_id="claude-sonnet-4",
        anthropic_id="claude-sonnet-4-20250514",
        bedrock_id="anthropic.claude-sonnet-4-20250514-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Claude Sonnet 4 - Latest generation Sonnet model",
        model_family="anthropic",
    ),
    "claude-opus-4": ModelMapping(
        convoy_id="claude-opus-4",
        anthropic_id="claude-opus-4-20250514",
        bedrock_id="anthropic.claude-opus-4-20250514-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Claude Opus 4 - Most capable model available",
        model_family="anthropic",
    ),

    # =========================================================================
    # AMAZON NOVA MODELS (Bedrock only)
    # =========================================================================
    "amazon-nova-micro": ModelMapping(
        convoy_id="amazon-nova-micro",
        anthropic_id=None,  # Amazon model, not available on Anthropic
        bedrock_id="amazon.nova-micro-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
        ],
        description="Amazon Nova Micro - Fastest, lowest cost text-only model",
        model_family="amazon",
    ),
    "amazon-nova-lite": ModelMapping(
        convoy_id="amazon-nova-lite",
        anthropic_id=None,
        bedrock_id="amazon.nova-lite-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
        ],
        description="Amazon Nova Lite - Low cost multimodal model for speed and cost",
        model_family="amazon",
    ),
    "amazon-nova-pro": ModelMapping(
        convoy_id="amazon-nova-pro",
        anthropic_id=None,
        bedrock_id="amazon.nova-pro-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Amazon Nova Pro - Highly capable multimodal model balancing accuracy and speed",
        model_family="amazon",
    ),

    # =========================================================================
    # DEEPSEEK MODELS (Bedrock only)
    # =========================================================================
    "deepseek-r1": ModelMapping(
        convoy_id="deepseek-r1",
        anthropic_id=None,  # DeepSeek model, not available on Anthropic
        bedrock_id="deepseek.r1-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="DeepSeek R1 - Advanced reasoning model with chain-of-thought",
        model_family="deepseek",
    ),

    # =========================================================================
    # META LLAMA MODELS (Bedrock only)
    # =========================================================================
    "llama-3.1-8b-instruct": ModelMapping(
        convoy_id="llama-3.1-8b-instruct",
        anthropic_id=None,  # Meta model, not available on Anthropic
        bedrock_id="meta.llama3-1-8b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
        ],
        description="Llama 3.1 8B Instruct - Efficient instruction-following model",
        model_family="meta",
    ),
    "llama-3.1-70b-instruct": ModelMapping(
        convoy_id="llama-3.1-70b-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-1-70b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.1 70B Instruct - High-capability instruction-following model",
        model_family="meta",
    ),
    "llama-3.1-405b-instruct": ModelMapping(
        convoy_id="llama-3.1-405b-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-1-405b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.1 405B Instruct - Largest Llama model for complex tasks",
        model_family="meta",
    ),
    "llama-3.2-1b-instruct": ModelMapping(
        convoy_id="llama-3.2-1b-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-2-1b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.2 1B Instruct - Lightweight model for edge deployment",
        model_family="meta",
    ),
    "llama-3.2-3b-instruct": ModelMapping(
        convoy_id="llama-3.2-3b-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-2-3b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.2 3B Instruct - Compact model balancing size and capability",
        model_family="meta",
    ),
    "llama-3.2-11b-vision-instruct": ModelMapping(
        convoy_id="llama-3.2-11b-vision-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-2-11b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.2 11B Vision Instruct - Multimodal model with vision capabilities",
        model_family="meta",
    ),
    "llama-3.2-90b-vision-instruct": ModelMapping(
        convoy_id="llama-3.2-90b-vision-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-2-90b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.2 90B Vision Instruct - Large multimodal model with vision",
        model_family="meta",
    ),
    "llama-3.3-70b-instruct": ModelMapping(
        convoy_id="llama-3.3-70b-instruct",
        anthropic_id=None,
        bedrock_id="meta.llama3-3-70b-instruct-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Llama 3.3 70B Instruct - Latest Llama 3.3 instruction model",
        model_family="meta",
    ),

    # =========================================================================
    # MISTRAL AI MODELS (Bedrock only)
    # =========================================================================
    "mistral-7b-instruct": ModelMapping(
        convoy_id="mistral-7b-instruct",
        anthropic_id=None,  # Mistral model, not available on Anthropic
        bedrock_id="mistral.mistral-7b-instruct-v0:2",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
        ],
        description="Mistral 7B Instruct - Efficient instruction-following model",
        model_family="mistral",
    ),
    "mixtral-8x7b-instruct": ModelMapping(
        convoy_id="mixtral-8x7b-instruct",
        anthropic_id=None,
        bedrock_id="mistral.mixtral-8x7b-instruct-v0:1",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
            "eu-west-1",
        ],
        description="Mixtral 8x7B Instruct - Mixture of experts model for diverse tasks",
        model_family="mistral",
    ),
    "mistral-large": ModelMapping(
        convoy_id="mistral-large",
        anthropic_id=None,
        bedrock_id="mistral.mistral-large-2402-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Mistral Large - High-capability model for complex reasoning",
        model_family="mistral",
    ),
    "mistral-large-2407": ModelMapping(
        convoy_id="mistral-large-2407",
        anthropic_id=None,
        bedrock_id="mistral.mistral-large-2407-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Mistral Large 2407 - Latest Mistral Large with improved capabilities",
        model_family="mistral",
    ),
    "mistral-small-2402": ModelMapping(
        convoy_id="mistral-small-2402",
        anthropic_id=None,
        bedrock_id="mistral.mistral-small-2402-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Mistral Small - Cost-effective model for simpler tasks",
        model_family="mistral",
    ),

    # =========================================================================
    # COHERE MODELS (Bedrock only)
    # =========================================================================
    "cohere-command-r": ModelMapping(
        convoy_id="cohere-command-r",
        anthropic_id=None,  # Cohere model, not available on Anthropic
        bedrock_id="cohere.command-r-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Cohere Command R - Optimized for RAG and tool use",
        model_family="cohere",
    ),
    "cohere-command-r-plus": ModelMapping(
        convoy_id="cohere-command-r-plus",
        anthropic_id=None,
        bedrock_id="cohere.command-r-plus-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="Cohere Command R+ - Enhanced model for complex enterprise tasks",
        model_family="cohere",
    ),

    # =========================================================================
    # AI21 LABS MODELS (Bedrock only)
    # =========================================================================
    "ai21-jamba-1.5-mini": ModelMapping(
        convoy_id="ai21-jamba-1.5-mini",
        anthropic_id=None,  # AI21 model, not available on Anthropic
        bedrock_id="ai21.jamba-1-5-mini-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="AI21 Jamba 1.5 Mini - Efficient hybrid SSM-Transformer model",
        model_family="ai21",
    ),
    "ai21-jamba-1.5-large": ModelMapping(
        convoy_id="ai21-jamba-1.5-large",
        anthropic_id=None,
        bedrock_id="ai21.jamba-1-5-large-v1:0",
        bedrock_regions=[
            "us-east-1",
            "us-west-2",
        ],
        description="AI21 Jamba 1.5 Large - High-capability hybrid model",
        model_family="ai21",
    ),
}


def get_model_mapping(model_id: str) -> ModelMapping | None:
    """Get the model mapping for a given model ID.

    Args:
        model_id: Provider-agnostic model identifier.

    Returns:
        ModelMapping if found, None otherwise.
    """
    return MODEL_REGISTRY.get(model_id)


def get_supported_models(
    provider: Provider | None = None,
    region: str | None = None,
    include_deprecated: bool = False,
) -> list[str]:
    """Get list of supported model IDs.

    Args:
        provider: Filter by provider availability (optional).
        region: Filter by Bedrock region availability (optional, only for Bedrock).
        include_deprecated: Include deprecated models in the list.

    Returns:
        List of supported model IDs.
    """
    models = []

    for model_id, mapping in MODEL_REGISTRY.items():
        # Skip deprecated models unless explicitly requested
        if mapping.deprecated and not include_deprecated:
            continue

        # Filter by provider if specified
        if provider is not None:
            if provider == Provider.ANTHROPIC and not mapping.anthropic_id:
                continue
            if provider == Provider.BEDROCK and not mapping.bedrock_id:
                continue

        # Filter by region if specified (only applies to Bedrock)
        if region is not None and provider == Provider.BEDROCK:
            if region not in mapping.bedrock_regions:
                continue

        models.append(model_id)

    return sorted(models)


def is_valid_model(model_id: str) -> bool:
    """Check if a model ID is valid.

    Args:
        model_id: Provider-agnostic model identifier.

    Returns:
        True if the model ID is recognized, False otherwise.
    """
    return model_id in MODEL_REGISTRY


def get_model_families() -> list[str]:
    """Get list of unique model families.

    Returns:
        Sorted list of model family names (e.g., "anthropic", "amazon", "meta").
    """
    families = set()
    for mapping in MODEL_REGISTRY.values():
        families.add(mapping.model_family)
    return sorted(families)


def get_models_by_family(family: str) -> list[str]:
    """Get list of model IDs for a specific model family.

    Args:
        family: Model family name (e.g., "anthropic", "amazon", "meta").

    Returns:
        List of model IDs belonging to the specified family.
    """
    return sorted([
        model_id
        for model_id, mapping in MODEL_REGISTRY.items()
        if mapping.model_family == family
    ])
