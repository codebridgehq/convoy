variable "aws_region" {
  description = "The AWS region to deploy in"
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "The AWS CLI profile to use"
}

variable "suffix" {
  description = "Suffix for resource names (e.g. -dev, -prod, or empty string for rebase)"
  type        = string
}
