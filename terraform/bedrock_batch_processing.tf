# =============================================================================
# Bedrock Batch Processing Infrastructure
# =============================================================================
# This file creates the AWS resources required for Bedrock batch inference:
# - S3 bucket for batch input/output data
# - IAM role for Bedrock to assume during batch processing
# - IAM policies for Bedrock model invocation and S3 access
#
# Documentation: https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html
# =============================================================================

locals {
  bedrock_batch_bucket_name = "convoy-bedrock-batch${var.suffix}"
  bedrock_batch_role_name   = "convoy-bedrock-batch-role${var.suffix}"
}

# =============================================================================
# S3 Bucket for Batch Data
# =============================================================================

resource "aws_s3_bucket" "bedrock_batch" {
  bucket = local.bedrock_batch_bucket_name

  tags = {
    Name        = local.bedrock_batch_bucket_name
    Purpose     = "Bedrock batch inference input/output storage"
    ManagedBy   = "Terraform"
  }
}

# Server-side encryption with SSE-S3
resource "aws_s3_bucket_server_side_encryption_configuration" "bedrock_batch" {
  bucket = aws_s3_bucket.bedrock_batch.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block all public access
resource "aws_s3_bucket_public_access_block" "bedrock_batch" {
  bucket = aws_s3_bucket.bedrock_batch.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# =============================================================================
# IAM Role for Bedrock Batch Inference
# =============================================================================

# Trust policy allowing Bedrock service to assume this role
data "aws_iam_policy_document" "bedrock_batch_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]

    # Security: Restrict to same account and batch inference jobs only
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:model-invocation-job/*"]
    }
  }
}

resource "aws_iam_role" "bedrock_batch" {
  name               = local.bedrock_batch_role_name
  assume_role_policy = data.aws_iam_policy_document.bedrock_batch_assume_role.json

  tags = {
    Name      = local.bedrock_batch_role_name
    Purpose   = "Bedrock batch inference execution role"
    ManagedBy = "Terraform"
  }
}

# =============================================================================
# IAM Policy for Bedrock Model Invocation
# =============================================================================
# Allows invoking all batch-supported foundation models
# Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-supported.html

data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid    = "BedrockModelInvocation"
    effect = "Allow"

    actions = [
      "bedrock:InvokeModel"
    ]

    # All batch-supported foundation models:
    # - Amazon Titan (Text, Embeddings)
    # - Amazon Nova (Pro, Lite, Micro)
    # - Anthropic Claude (3.5 Sonnet, 3.5 Haiku, 3 Opus, 3 Sonnet, 3 Haiku)
    # - Cohere (Command R, Command R+, Embed)
    # - Meta Llama (3.1, 3.2, 3.3)
    # - Mistral AI (Large, Small, Mixtral)
    # - AI21 Labs (Jamba 1.5)
    resources = [
      "arn:aws:bedrock:*::foundation-model/amazon.titan-*",
      "arn:aws:bedrock:*::foundation-model/amazon.nova-*",
      "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
      "arn:aws:bedrock:*::foundation-model/cohere.*",
      "arn:aws:bedrock:*::foundation-model/meta.llama*",
      "arn:aws:bedrock:*::foundation-model/mistral.*",
      "arn:aws:bedrock:*::foundation-model/ai21.jamba-*"
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_invoke" {
  name   = "bedrock-model-invocation"
  role   = aws_iam_role.bedrock_batch.id
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}

# =============================================================================
# IAM Policy for S3 Access
# =============================================================================
# Allows Bedrock to read input files and write output files

data "aws_iam_policy_document" "bedrock_s3" {
  # Read access to the bucket (for listing)
  statement {
    sid    = "S3ListBucket"
    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.bedrock_batch.arn
    ]
  }

  # Read access to input files
  statement {
    sid    = "S3ReadInputs"
    effect = "Allow"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.bedrock_batch.arn}/batch-inputs/*"
    ]
  }

  # Write access to output files
  statement {
    sid    = "S3WriteOutputs"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.bedrock_batch.arn}/batch-outputs/*"
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_s3" {
  name   = "bedrock-s3-access"
  role   = aws_iam_role.bedrock_batch.id
  policy = data.aws_iam_policy_document.bedrock_s3.json
}

# =============================================================================
# Outputs
# =============================================================================

output "bedrock_batch_bucket_name" {
  description = "Name of the S3 bucket for Bedrock batch input/output"
  value       = aws_s3_bucket.bedrock_batch.id
}

output "bedrock_batch_bucket_arn" {
  description = "ARN of the S3 bucket for Bedrock batch input/output"
  value       = aws_s3_bucket.bedrock_batch.arn
}

output "bedrock_batch_role_arn" {
  description = "ARN of the IAM role for Bedrock batch inference"
  value       = aws_iam_role.bedrock_batch.arn
}

output "bedrock_batch_role_name" {
  description = "Name of the IAM role for Bedrock batch inference"
  value       = aws_iam_role.bedrock_batch.name
}
