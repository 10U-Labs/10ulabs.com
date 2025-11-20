#!/usr/bin/env python3
import argparse
import sys
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
