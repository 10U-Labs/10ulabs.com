# AMI Build Artifacts

This directory contains Packer template and provisioning scripts for building GitHub runner AMIs.

These files should be uploaded to S3 bucket configured in `config.json` (`packer.config_bucket`) under path `ami_for_ec2_runners/`.

## Files

- `template.pkr.hcl` - Packer template for building GitHub runner AMIs
- `install_docker.py/sh` - Docker installation provisioner
- `install_github_runner.py/sh` - GitHub Actions runner installation provisioner
- `wait_for_status_checks.py/sh` - EC2 status check waiter

## Usage

The AMI builder Lambda (handler.py) triggers EC2 Spot instances that download these files from S3 and run Packer to build new AMIs.

Upload to S3:
```bash
aws s3 sync build_artifacts/ s3://10ulabs-packer-configs/ami_for_ec2_runners/
```
