# State Migration Notes

## SSM Parameter Migration

The `aws_ssm_parameter.ec2_runner_ami_latest` resource was moved from
`src/api/endpoints/webhooks/github/jit_runner_requests` to this module.

### First-time deployment

If the SSM parameter already exists (from the old jit_runner_requests deployment),
you need to import it before running terraform apply:

```bash
cd src/api/shared/parameters
terraform init
terraform import aws_ssm_parameter.ec2_runner_ami_latest /ami/ec2-runner/latest
terraform plan  # Should show no changes
```

### After migration

Remove the parameter from the old state (if not already done):

```bash
cd src/api/endpoints/webhooks/github/jit_runner_requests
terraform state rm aws_ssm_parameter.latest_ami
```
