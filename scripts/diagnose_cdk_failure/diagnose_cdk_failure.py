#!/usr/bin/env python3
import argparse
import sys
import json
import boto3
from botocore.exceptions import ClientError


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


def validate_resource_reference(ref_type, ref_value, region):
    exists = False
    error_msg = None

    try:
        if ref_type == 'CertificateArn':
            acm = boto3.client('acm', region_name=region)
            try:
                acm.describe_certificate(CertificateArn=ref_value)
                exists = True
            except ClientError as e:
                error_msg = f"Certificate {ref_value} not found: {e.response['Error']['Message']}"

        elif ref_type == 'HostedZoneId':
            route53 = boto3.client('route53', region_name=region)
            try:
                route53.get_hosted_zone(Id=ref_value)
                exists = True
            except ClientError as e:
                error_msg = f"Hosted Zone {ref_value} not found: {e.response['Error']['Message']}"

        elif ref_type == 'VpcId':
            ec2 = boto3.client('ec2', region_name=region)
            try:
                response = ec2.describe_vpcs(VpcIds=[ref_value])
                exists = len(response['Vpcs']) > 0
                if not exists:
                    error_msg = f"VPC {ref_value} not found"
            except ClientError as e:
                error_msg = f"VPC {ref_value} not found: {e.response['Error']['Message']}"

        elif ref_type == 'SubnetId':
            ec2 = boto3.client('ec2', region_name=region)
            try:
                response = ec2.describe_subnets(SubnetIds=[ref_value])
                exists = len(response['Subnets']) > 0
                if not exists:
                    error_msg = f"Subnet {ref_value} not found"
            except ClientError as e:
                error_msg = f"Subnet {ref_value} not found: {e.response['Error']['Message']}"

        elif ref_type == 'SecurityGroupId':
            ec2 = boto3.client('ec2', region_name=region)
            try:
                response = ec2.describe_security_groups(GroupIds=[ref_value])
                exists = len(response['SecurityGroups']) > 0
                if not exists:
                    error_msg = f"Security Group {ref_value} not found"
            except ClientError as e:
                error_msg = f"Security Group {ref_value} not found: {e.response['Error']['Message']}"

    except Exception as e:
        error_msg = f"Error validating {ref_type} {ref_value}: {str(e)}"

    return exists, error_msg


def extract_resource_references(resource_properties):
    references = []

    if not isinstance(resource_properties, dict):
        return references

    ref_types = {
        'CertificateArn': 'CertificateArn',
        'HostedZoneId': 'HostedZoneId',
        'VpcId': 'VpcId',
        'SubnetId': 'SubnetId',
        'SecurityGroupId': 'SecurityGroupId'
    }

    for key, ref_type in ref_types.items():
        if key in resource_properties:
            value = resource_properties[key]
            if isinstance(value, str):
                references.append((ref_type, value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        references.append((ref_type, item))

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
        print("CHECKING RESOURCE REFERENCES")
        print("-" * 80)
        print()

        changes = changeset.get('Changes', [])
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
                            refs = extract_resource_references(props)

                            for ref_type, ref_value in refs:
                                exists, error_msg = validate_resource_reference(ref_type, ref_value, region)
                                if not exists:
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

        if validation_errors:
            print("❌ INVALID RESOURCE REFERENCES FOUND:")
            print()
            for error in validation_errors:
                print(f"   Resource: {error['logical_id']} ({error['resource_type']})")
                print(f"   Action: {error['action']}")
                print(f"   Invalid Reference: {error['ref_type']}")
                print(f"   Value: {error['ref_value']}")
                print(f"   Error: {error['error']}")
                print()

            return True
        else:
            print("   No invalid resource references found in changeset properties")
            print("   (The validation error may be in a nested stack or imported value)")
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
