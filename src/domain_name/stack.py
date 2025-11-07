"""
Domain Infrastructure: 10uf.org

Creates the foundational Route53 hosted zone for 10uf.org.
Registers the domain if not already registered.
All services (websites, APIs, etc.) reference this zone.
"""
from typing import Dict, Any
from aws_cdk import (
    Stack,
    CfnOutput,
    Fn,
    CustomResource,
    Duration,
    aws_route53 as route53,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct


class DomainStack(Stack):
    """CDK Stack for 10uf.org domain infrastructure."""

    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Lambda function to register domain and find/create hosted zone
        # Note: AWS automatically creates a hosted zone when registering a domain
        # This Lambda either finds the existing zone or registers the domain (which creates one)
        domain_registration_handler = lambda_.Function(
            self, "DomainRegistrationHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import cfnresponse
import time

route53domains = boto3.client('route53domains', region_name='us-east-1')
route53 = boto3.client('route53')
account = boto3.client('account', region_name='us-east-1')

def handler(event, context):
    domain_name = event['ResourceProperties']['DomainName']
    contact_email = event['ResourceProperties']['ContactEmail']

    try:
        if event['RequestType'] == 'Delete':
            # Don't delete domain on stack deletion - too dangerous
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        # Check if domain is already registered
        try:
            domain_detail = route53domains.get_domain_detail(DomainName=domain_name)
            print(f"Domain {domain_name} is already registered")

            # Find the hosted zone for this domain
            zones = route53.list_hosted_zones_by_name(DNSName=domain_name, MaxItems='10')
            matching_zone = None
            for zone in zones.get('HostedZones', []):
                # Zone name has trailing dot, e.g., "10uf.org."
                if zone['Name'] == f"{domain_name}.":
                    matching_zone = zone
                    break

            if not matching_zone:
                error_msg = f"Domain {domain_name} is registered but no hosted zone found. This should not happen."
                print(error_msg)
                cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': error_msg})
                return

            # Extract zone ID (format: /hostedzone/Z1234, we want just Z1234)
            zone_id = matching_zone['Id'].split('/')[-1]
            hz_detail = route53.get_hosted_zone(Id=matching_zone['Id'])
            nameservers = hz_detail['DelegationSet']['NameServers']

            print(f"Found hosted zone {zone_id} with nameservers: {nameservers}")

            cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                'HostedZoneId': zone_id,
                'NameServers': ','.join(nameservers),
                'DomainStatus': domain_detail['StatusList'][0] if domain_detail.get('StatusList') else 'REGISTERED',
                'AlreadyRegistered': 'true'
            })
            return

        except route53domains.exceptions.InvalidInput:
            # Domain not registered yet
            print(f"Domain {domain_name} not registered, proceeding with registration...")

        # Check domain availability
        availability = route53domains.check_domain_availability(DomainName=domain_name)
        if availability['Availability'] != 'AVAILABLE':
            cfnresponse.send(event, context, cfnresponse.FAILED, {
                'Error': f"Domain {domain_name} is not available: {availability['Availability']}"
            })
            return

        # Get AWS account contact information
        print("Fetching AWS account contact information...")
        contact_info = account.get_contact_information()['ContactInformation']

        # Validate required fields
        required_fields = {
            'FullName': contact_info.get('FullName'),
            'AddressLine1': contact_info.get('AddressLine1'),
            'City': contact_info.get('City'),
            'StateOrRegion': contact_info.get('StateOrRegion'),
            'CountryCode': contact_info.get('CountryCode'),
            'PostalCode': contact_info.get('PostalCode'),
            'PhoneNumber': contact_info.get('PhoneNumber')
        }

        missing_fields = [k for k, v in required_fields.items() if not v]
        if missing_fields:
            error_msg = f"AWS account missing contact fields: {', '.join(missing_fields)}. Configure at: https://console.aws.amazon.com/billing/home#/account"
            print(error_msg)
            raise ValueError(error_msg)

        print(f"Using AWS account contact info with email: {contact_email}")

        # Build contact from AWS account info
        full_name_parts = contact_info['FullName'].split(maxsplit=1)
        contact = {
            'FirstName': full_name_parts[0],
            'LastName': full_name_parts[1] if len(full_name_parts) > 1 else full_name_parts[0],
            'ContactType': 'COMPANY' if contact_info.get('CompanyName') else 'PERSON',
            'AddressLine1': contact_info['AddressLine1'],
            'City': contact_info['City'],
            'State': contact_info['StateOrRegion'],
            'CountryCode': contact_info['CountryCode'],
            'ZipCode': contact_info['PostalCode'],
            'PhoneNumber': contact_info['PhoneNumber'],
            'Email': contact_email
        }

        if contact_info.get('CompanyName'):
            contact['OrganizationName'] = contact_info['CompanyName']

        print(f"Registering domain {domain_name} with contact: {contact['Email']}")

        # Register domain - AWS automatically creates a hosted zone
        registration = route53domains.register_domain(
            DomainName=domain_name,
            DurationInYears=1,
            AutoRenew=True,
            AdminContact=contact,
            RegistrantContact=contact,
            TechContact=contact,
            PrivacyProtectAdminContact=True,
            PrivacyProtectRegistrantContact=True,
            PrivacyProtectTechContact=True
        )

        print(f"Domain registration initiated: {registration['OperationId']}")
        print("AWS will automatically create a hosted zone for this domain")

        # Wait for the hosted zone to be created (exponential backoff)
        max_wait_time = 840  # 14 minutes (leave 1 min buffer for 15 min Lambda timeout)
        attempt = 0
        elapsed = 0

        while elapsed < max_wait_time:
            wait_time = 2 ** attempt  # 1, 2, 4, 8, 16, 32, 64, 128, 256, 512
            time.sleep(wait_time)
            elapsed += wait_time
            attempt += 1

            print(f"Checking for hosted zone (attempt {attempt}, elapsed {elapsed}s)...")

            # Look for the hosted zone created by AWS
            try:
                zones = route53.list_hosted_zones_by_name(DNSName=domain_name, MaxItems='10')
                matching_zone = None
                for zone in zones.get('HostedZones', []):
                    if zone['Name'] == f"{domain_name}.":
                        matching_zone = zone
                        break

                if matching_zone:
                    zone_id = matching_zone['Id'].split('/')[-1]
                    hz_detail = route53.get_hosted_zone(Id=matching_zone['Id'])
                    nameservers = hz_detail['DelegationSet']['NameServers']

                    print(f"Found hosted zone {zone_id} created by AWS during registration")
                    print(f"Nameservers: {nameservers}")

                    cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                        'HostedZoneId': zone_id,
                        'NameServers': ','.join(nameservers),
                        'OperationId': registration['OperationId'],
                        'Message': f"Domain {domain_name} registered successfully"
                    })
                    return

                print(f"Hosted zone not yet available, will retry in {2 ** attempt}s...")

            except Exception as e:
                print(f"Error checking for hosted zone: {e}")

        # If we get here, hosted zone wasn't found in time
        # Registration likely succeeded but zone creation is still pending
        print(f"Domain registration initiated but hosted zone not yet available.")
        print(f"Re-deploy the stack later to complete setup once zone appears.")

        cfnresponse.send(event, context, cfnresponse.FAILED, {
            'Error': 'Hosted zone not created within timeout period',
            'OperationId': registration['OperationId'],
            'Message': 'Domain registration initiated but hosted zone not yet available. Wait a few minutes and re-deploy.'
        })

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        import traceback
        tb = traceback.format_exc()
        print(tb)
        cfnresponse.send(event, context, cfnresponse.FAILED, {
            'Error': error_msg,
            'ErrorType': type(e).__name__,
            'Traceback': tb[:1000]
        })
"""),
            timeout=Duration.seconds(900),
            initial_policy=[
                iam.PolicyStatement(
                    actions=[
                        "route53domains:CheckDomainAvailability",
                        "route53domains:GetDomainDetail",
                        "route53domains:RegisterDomain",
                        "route53:ListHostedZonesByName",
                        "route53:GetHostedZone",
                        "account:GetContactInformation"
                    ],
                    resources=["*"]
                )
            ]
        )

        # Custom resource runs first - registers domain or finds existing zone
        domain_registration = CustomResource(
            self, "DomainRegistration",
            service_token=domain_registration_handler.function_arn,
            properties={
                "DomainName": config["domain_name"],
                "ContactEmail": config["domain_contact_email"]
            }
        )

        # Import the hosted zone that AWS created during domain registration
        # (not creating a new one - avoiding duplicate zones)
        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone",
            hosted_zone_id=domain_registration.get_att_string("HostedZoneId"),
            zone_name=config["domain_name"]
        )

        # Outputs
        export_prefix = config['domain_name'].replace('.', '-')

        CfnOutput(
            self, "DomainName",
            value=config["domain_name"],
            description="Registered domain name"
        )

        CfnOutput(
            self, "HostedZoneId",
            value=self.hosted_zone.hosted_zone_id,
            description=f"Route53 Hosted Zone ID for {config['domain_name']}",
            export_name=f"{export_prefix}-HostedZoneId"
        )

        CfnOutput(
            self, "HostedZoneName",
            value=self.hosted_zone.zone_name,
            description=f"Route53 Hosted Zone Name for {config['domain_name']}",
            export_name=f"{export_prefix}-HostedZoneName"
        )

        CfnOutput(
            self, "NameServers",
            value=domain_registration.get_att_string("NameServers"),
            description=f"Name servers for {config['domain_name']}"
        )

        CfnOutput(
            self, "RegistrationStatus",
            value=domain_registration.get_att_string("DomainStatus"),
            description="Domain registration status"
        )
