# Terraform

## Initialize

```bash
terraform init -reconfigure -backend-config="./terraform-backend.hcl"
```

## Plan

```bash
terraform plan -out=tfplan
```

## Apply

```bash
terraform apply tfplan
```

## Destroy

```bash
terraform destroy
```

## Format

```bash
terraform fmt -recursive
```

## Validate

```bash
terraform validate
```

## Show State

```bash
terraform state list
terraform state show <resource>
```

## Import Existing Resource

```bash
terraform import <resource_type>.<name> <id>
```
