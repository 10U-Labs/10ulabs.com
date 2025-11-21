#!/usr/bin/env python3
import argparse
import sys
import json
import re
import boto3
from botocore.exceptions import ClientError


ARN_PATTERN = re.compile(r'arn:aws:([^:]+):([^:]*):([^:]*):(.+)')
RESOURCE_ID_PATTERNS = {
    'vpc': re.compile(r'vpc-[a-f0-9]+'),
    'subnet': re.compile(r'subnet-[a-f0-9]+'),
    'sg': re.compile(r'sg-[a-f0-9]+'),
    'instance': re.compile(r'i-[a-f0-9]+'),
    'ami': re.compile(r'ami-[a-f0-9]+'),
    'eni': re.compile(r'eni-[a-f0-9]+'),
    'igw': re.compile(r'igw-[a-f0-9]+'),
    'nat': re.compile(r'nat-[a-f0-9]+'),
    'rtb': re.compile(r'rtb-[a-f0-9]+'),
    'hosted_zone': re.compile(r'Z[A-Z0-9]{12,}'),
}


def get_failed_changeset(cfn_client, stack_name):
    try:
        response = cfn_client.describe_change_set(
            StackName=stack_name,
            ChangeSetName='cdk-deploy-change-set'
        )
        return response
    except ClientError as e:
        print(f"Failed to get changeset: {e}")
        return None


def get_changeset_hooks(cfn_client, stack_name):
    try:
        response = cfn_client.describe_change_set_hooks(
            StackName=stack_name,
            ChangeSetName='cdk-deploy-change-set'
        )
        return response.get('Hooks', [])
    except ClientError:
        return []


def validate_arn(arn, region):
    match = ARN_PATTERN.match(arn)
    if not match:
        return False, f"Invalid ARN format: {arn}"

    service, arn_region, account, resource = match.groups()

    use_region = arn_region if arn_region else region

    validators = {
        'acm': validate_acm_certificate,
        'lambda': validate_lambda_function,
        's3': validate_s3_bucket,
        'dynamodb': validate_dynamodb_table,
        'iam': validate_iam_role,
        'sqs': validate_sqs_queue,
        'sns': validate_sns_topic,
        'ec2': validate_ec2_resource,
    }

    validator = validators.get(service)
    if validator:
        return validator(arn, resource, use_region)

    return None, f"No validator for service: {service}"


def validate_acm_certificate(arn, resource, region):
    try:
        acm = boto3.client('acm', region_name=region)
        acm.describe_certificate(CertificateArn=arn)
        return True, None
    except ClientError as e:
        return False, f"Certificate not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating certificate: {str(e)}"


def validate_lambda_function(arn, resource, region):
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        function_name = resource.split(':')[-1]
        lambda_client.get_function(FunctionName=function_name)
        return True, None
    except ClientError as e:
        return False, f"Lambda function not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating Lambda function: {str(e)}"


def validate_s3_bucket(arn, resource, region):
    try:
        s3 = boto3.client('s3', region_name=region)
        bucket_name = resource
        s3.head_bucket(Bucket=bucket_name)
        return True, None
    except ClientError as e:
        return False, f"S3 bucket not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating S3 bucket: {str(e)}"


def validate_dynamodb_table(arn, resource, region):
    try:
        dynamodb = boto3.client('dynamodb', region_name=region)
        table_name = resource.split('/')[-1]
        dynamodb.describe_table(TableName=table_name)
        return True, None
    except ClientError as e:
        return False, f"DynamoDB table not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating DynamoDB table: {str(e)}"


def validate_iam_role(arn, resource, region):
    try:
        iam = boto3.client('iam')
        role_name = resource.split('/')[-1]
        iam.get_role(RoleName=role_name)
        return True, None
    except ClientError as e:
        return False, f"IAM role not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating IAM role: {str(e)}"


def validate_sqs_queue(arn, resource, region):
    try:
        sqs = boto3.client('sqs', region_name=region)
        queue_name = resource.split(':')[-1]
        sqs.get_queue_url(QueueName=queue_name)
        return True, None
    except ClientError as e:
        return False, f"SQS queue not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating SQS queue: {str(e)}"


def validate_sns_topic(arn, resource, region):
    try:
        sns = boto3.client('sns', region_name=region)
        sns.get_topic_attributes(TopicArn=arn)
        return True, None
    except ClientError as e:
        return False, f"SNS topic not found: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating SNS topic: {str(e)}"


def validate_ec2_resource(arn, resource, region):
    return None, "EC2 ARN validation not implemented (use resource ID patterns instead)"


def validate_resource_id(resource_id, region):
    ec2 = boto3.client('ec2', region_name=region)
    route53 = boto3.client('route53')

    try:
        if RESOURCE_ID_PATTERNS['vpc'].match(resource_id):
            response = ec2.describe_vpcs(VpcIds=[resource_id])
            exists = len(response['Vpcs']) > 0
            return exists, None if exists else f"VPC {resource_id} not found"

        elif RESOURCE_ID_PATTERNS['subnet'].match(resource_id):
            response = ec2.describe_subnets(SubnetIds=[resource_id])
            exists = len(response['Subnets']) > 0
            return exists, None if exists else f"Subnet {resource_id} not found"

        elif RESOURCE_ID_PATTERNS['sg'].match(resource_id):
            response = ec2.describe_security_groups(GroupIds=[resource_id])
            exists = len(response['SecurityGroups']) > 0
            return exists, None if exists else f"Security Group {resource_id} not found"

        elif RESOURCE_ID_PATTERNS['ami'].match(resource_id):
            response = ec2.describe_images(ImageIds=[resource_id])
            exists = len(response['Images']) > 0
            return exists, None if exists else f"AMI {resource_id} not found"

        elif RESOURCE_ID_PATTERNS['hosted_zone'].match(resource_id):
            try:
                route53.get_hosted_zone(Id=resource_id)
                return True, None
            except ClientError as e:
                return False, f"Hosted Zone {resource_id} not found: {e.response['Error']['Message']}"

    except ClientError as e:
        return False, f"Error validating {resource_id}: {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"Error validating {resource_id}: {str(e)}"

    return None, f"Unknown resource ID format: {resource_id}"


def extract_all_references(obj, references=None):
    if references is None:
        references = set()

    if isinstance(obj, str):
        arn_match = ARN_PATTERN.match(obj)
        if arn_match:
            references.add(('arn', obj))
        else:
            for pattern_name, pattern in RESOURCE_ID_PATTERNS.items():
                if pattern.match(obj):
                    references.add(('resource_id', obj))
                    break

    elif isinstance(obj, list):
        for item in obj:
            extract_all_references(item, references)

    elif isinstance(obj, dict):
        for value in obj.values():
            extract_all_references(value, references)

    return references


def analyze_early_validation_failure(cfn_client, changeset, region):
    print("=" * 80)
    print("EARLY VALIDATION FAILURE ANALYSIS")
    print("=" * 80)
    print()

    status_reason = changeset.get('StatusReason', '')
    if 'EarlyValidation' in status_reason or 'ResourceExistenceCheck' in status_reason:
        print("⚠️  AWS Early Validation detected resource existence issues")
        print()

        hooks = get_changeset_hooks(cfn_client, changeset.get('StackName', ''))
        if hooks:
            print("Hook Execution Details:")
            for hook in hooks:
                print(f"   Hook: {hook.get('TypeName', 'Unknown')}")
                print(f"   Status: {hook.get('Status', 'Unknown')}")
                if hook.get('FailureMode'):
                    print(f"   Failure Mode: {hook.get('FailureMode')}")
                if hook.get('StatusReason'):
                    print(f"   Reason: {hook.get('StatusReason')}")
                print()

        print("-" * 80)
        print("SCANNING FOR ALL AWS RESOURCE REFERENCES")
        print("-" * 80)
        print()

        changes = changeset.get('Changes', [])
        all_references = set()
        validation_errors = []

        for change in changes:
            resource_change = change.get('ResourceChange', {})
            logical_id = resource_change.get('LogicalResourceId')
            resource_type = resource_change.get('ResourceType')
            action = resource_change.get('Action')

            details = resource_change.get('Details', [])
            for detail in details:
                if detail.get('Target', {}).get('Attribute') == 'Properties':
                    after_value = detail.get('Target', {}).get('AfterValue')
                    if after_value:
                        try:
                            props = json.loads(after_value) if isinstance(after_value, str) else after_value
                            refs = extract_all_references(props)

                            for ref_type, ref_value in refs:
                                all_references.add((ref_type, ref_value))

                                exists = None
                                error_msg = None

                                if ref_type == 'arn':
                                    exists, error_msg = validate_arn(ref_value, region)
                                elif ref_type == 'resource_id':
                                    exists, error_msg = validate_resource_id(ref_value, region)

                                if exists is False:
                                    validation_errors.append({
                                        'logical_id': logical_id,
                                        'resource_type': resource_type,
                                        'action': action,
                                        'ref_type': ref_type,
                                        'ref_value': ref_value,
                                        'error': error_msg
                                    })

                        except (json.JSONDecodeError, TypeError):
                            pass

        print(f"Detected {len(all_references)} AWS resource references in changeset")
        print()

        if validation_errors:
            print("❌ INVALID RESOURCE REFERENCES FOUND:")
            print()
            for error in validation_errors:
                print(f"   Resource: {error['logical_id']} ({error['resource_type']})")
                print(f"   Action: {error['action']}")
                print(f"   Reference Type: {error['ref_type']}")
                print(f"   Value: {error['ref_value']}")
                print(f"   Error: {error['error']}")
                print()

            return True
        else:
            print("   ✓ All detected resource references appear to be valid")
            print("   (Note: Some references may not be validated if validators are not implemented)")
            print()

    return False


def check_resource_exists(resource_type, resource_name, region):
    exists = False
    details = None

    try:
        if resource_type == 'AWS::DynamoDB::Table':
            dynamodb = boto3.client('dynamodb', region_name=region)
            try:
                response = dynamodb.describe_table(TableName=resource_name)
                exists = True
                details = {
                    'Status': response['Table']['TableStatus'],
                    'Arn': response['Table']['TableArn']
                }
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    details = {'Error': str(e)}

        elif resource_type == 'AWS::Lambda::Function':
            lambda_client = boto3.client('lambda', region_name=region)
            try:
                response = lambda_client.get_function(FunctionName=resource_name)
                exists = True
                details = {
                    'State': response['Configuration']['State'],
                    'Arn': response['Configuration']['FunctionArn']
                }
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    details = {'Error': str(e)}

        elif resource_type == 'AWS::SSM::Parameter':
            ssm = boto3.client('ssm', region_name=region)
            try:
                response = ssm.get_parameter(Name=resource_name)
                exists = True
                details = {
                    'Type': response['Parameter']['Type'],
                    'Version': response['Parameter']['Version']
                }
            except ClientError as e:
                if e.response['Error']['Code'] != 'ParameterNotFound':
                    details = {'Error': str(e)}

        elif resource_type == 'AWS::SQS::Queue':
            sqs = boto3.client('sqs', region_name=region)
            try:
                response = sqs.get_queue_url(QueueName=resource_name)
                exists = True
                details = {'QueueUrl': response['QueueUrl']}
            except ClientError as e:
                if 'NonExistentQueue' not in str(e):
                    details = {'Error': str(e)}

    except Exception as e:
        details = {'Error': str(e)}

    return exists, details


def extract_resource_name(resource_type, changeset_change):
    resource_properties = changeset_change.get('ResourceChange', {})
    physical_id = resource_properties.get('PhysicalResourceId')

    if physical_id:
        return physical_id

    return None


def check_stack_drift(cfn_client, stack_name):
    try:
        response = cfn_client.describe_stack_resource_drifts(
            StackName=stack_name,
            StackResourceDriftStatusFilters=['MODIFIED', 'DELETED', 'NOT_CHECKED']
        )
        return response.get('StackResourceDrifts', [])
    except ClientError:
        return []


def get_recent_stack_events(cfn_client, stack_name, max_events=30):
    try:
        response = cfn_client.describe_stack_events(
            StackName=stack_name
        )
        events = response.get('StackEvents', [])
        return events[:max_events]
    except ClientError:
        return []


def diagnose_deployment_failure(stack_name, region):
    cfn_client = boto3.client('cloudformation', region_name=region)

    print("=" * 80)
    print(f"CDK DEPLOYMENT FAILURE DIAGNOSTICS")
    print(f"Stack: {stack_name}")
    print(f"Region: {region}")
    print("=" * 80)
    print()

    changeset = get_failed_changeset(cfn_client, stack_name)
    if not changeset:
        print("ERROR: Could not retrieve changeset information")
        return

    print(f"Changeset Status: {changeset.get('Status')}")
    print(f"Status Reason: {changeset.get('StatusReason')}")
    print()

    changes = changeset.get('Changes', [])
    if not changes:
        print("No changes found in changeset")
        return

    status_reason = changeset.get('StatusReason', '')
    is_early_validation = 'EarlyValidation' in status_reason or 'ResourceExistenceCheck' in status_reason

    if is_early_validation:
        found_issue = analyze_early_validation_failure(cfn_client, changeset, region)
        if found_issue:
            print("=" * 80)
            print("RECOMMENDATIONS")
            print("=" * 80)
            print()
            print("1. Verify the referenced resources exist in your AWS account and region")
            print("2. Check if you're referencing resources from a different region")
            print("3. Ensure cross-stack exports are available if using Fn::ImportValue")
            print("4. Verify resource IDs/ARNs are correct and haven't been deleted")
            print()
            return

    print("-" * 80)
    print("RESOURCE CONFLICT ANALYSIS")
    print("-" * 80)
    print()

    conflicts_found = False
    resources_to_add = [c for c in changes if c.get('ResourceChange', {}).get('Action') == 'Add']

    if resources_to_add:
        print(f"Checking {len(resources_to_add)} resources being added...")
        print()

        for change in resources_to_add:
            resource_change = change.get('ResourceChange', {})
            logical_id = resource_change.get('LogicalResourceId')
            resource_type = resource_change.get('ResourceType')

            resource_name = extract_resource_name(resource_type, change)
            if not resource_name:
                continue

            exists, details = check_resource_exists(resource_type, resource_name, region)

            if exists:
                conflicts_found = True
                print(f"⚠️  CONFLICT DETECTED")
                print(f"   Logical ID: {logical_id}")
                print(f"   Type: {resource_type}")
                print(f"   Name: {resource_name}")
                print(f"   Status: Resource already exists in AWS")
                if details:
                    for key, value in details.items():
                        print(f"   {key}: {value}")
                print()

    if not conflicts_found:
        print("No obvious resource conflicts detected")
        print()

    print("-" * 80)
    print("STACK DRIFT ANALYSIS")
    print("-" * 80)
    print()

    drifted_resources = check_stack_drift(cfn_client, stack_name)
    if drifted_resources:
        print(f"Found {len(drifted_resources)} drifted resources:")
        print()
        for drift in drifted_resources:
            print(f"   Resource: {drift.get('LogicalResourceId')}")
            print(f"   Type: {drift.get('ResourceType')}")
            print(f"   Drift Status: {drift.get('StackResourceDriftStatus')}")
            print()
    else:
        print("No stack drift detected")
        print()

    print("-" * 80)
    print("RECENT STACK EVENTS")
    print("-" * 80)
    print()

    events = get_recent_stack_events(cfn_client, stack_name, max_events=20)
    if events:
        for event in events:
            status = event.get('ResourceStatus', '')
            if any(keyword in status for keyword in ['FAILED', 'ROLLBACK', 'DELETE']):
                print(f"   Time: {event.get('Timestamp')}")
                print(f"   Resource: {event.get('LogicalResourceId')}")
                print(f"   Status: {status}")
                if event.get('ResourceStatusReason'):
                    print(f"   Reason: {event.get('ResourceStatusReason')}")
                print()
    else:
        print("No recent stack events found")
        print()

    print("-" * 80)
    print("CHANGESET SUMMARY")
    print("-" * 80)
    print()

    add_count = len([c for c in changes if c.get('ResourceChange', {}).get('Action') == 'Add'])
    modify_count = len([c for c in changes if c.get('ResourceChange', {}).get('Action') == 'Modify'])
    remove_count = len([c for c in changes if c.get('ResourceChange', {}).get('Action') == 'Remove'])

    print(f"Resources to add: {add_count}")
    print(f"Resources to modify: {modify_count}")
    print(f"Resources to remove: {remove_count}")
    print()

    if conflicts_found:
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print()
        print("1. Check if conflicting resources were created outside CloudFormation")
        print("2. Consider importing existing resources into the stack")
        print("3. Review recent manual changes to AWS resources")
        print("4. Verify that previous stack operations completed successfully")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Diagnose CDK/CloudFormation deployment failures'
    )
    parser.add_argument(
        '--stack-name',
        required=True,
        help='CloudFormation stack name'
    )
    parser.add_argument(
        '--region',
        required=True,
        help='AWS region'
    )

    args = parser.parse_args()

    try:
        diagnose_deployment_failure(args.stack_name, args.region)
    except Exception as e:
        print(f"Diagnostic script failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
