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

        # Create Route53 Hosted Zone for 10uf.org
        self.hosted_zone = route53.HostedZone(
            self, "HostedZone",
            zone_name=config["domain_name"],
            comment=f"Hosted zone for {config['domain_name']}"
        )

        # Lambda function to check/register domain
        domain_registration_handler = lambda_.Function(
            self, "DomainRegistrationHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import cfnresponse

route53domains = boto3.client('route53domains', region_name='us-east-1')  # Route53 Domains is only in us-east-1
account = boto3.client('account', region_name='us-east-1')

def handler(event, context):
    domain_name = event['ResourceProperties']['DomainName']
    hosted_zone_id = event['ResourceProperties']['HostedZoneId']

    try:
        if event['RequestType'] == 'Delete':
            # Don't delete domain on stack deletion - too dangerous
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        # Check if domain is already registered
        try:
            response = route53domains.get_domain_detail(DomainName=domain_name)
            print(f"Domain {domain_name} is already registered")

            # Update nameservers to match hosted zone
            route53 = boto3.client('route53')
            hz = route53.get_hosted_zone(Id=hosted_zone_id)
            nameservers = [{'Name': ns} for ns in hz['DelegationSet']['NameServers']]

            try:
                route53domains.update_domain_nameservers(
                    DomainName=domain_name,
                    Nameservers=nameservers
                )
                print(f"Updated nameservers for {domain_name}")
            except Exception as e:
                print(f"Could not update nameservers: {e}")

            cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                'DomainStatus': response['StatusList'][0] if response.get('StatusList') else 'REGISTERED',
                'AlreadyRegistered': 'true'
            })
            return
        except route53domains.exceptions.InvalidInput:
            # Domain not registered, proceed with registration
            print(f"Domain {domain_name} is not registered, checking availability...")

        # Check domain availability
        availability = route53domains.check_domain_availability(DomainName=domain_name)

        if availability['Availability'] != 'AVAILABLE':
            cfnresponse.send(event, context, cfnresponse.FAILED, {
                'Error': f"Domain {domain_name} is not available for registration: {availability['Availability']}"
            })
            return

        # Get AWS account contact information
        print("Fetching AWS account contact information...")
        contact_info = account.get_contact_information()['ContactInformation']

        # Build registrant contact from AWS account info
        contact = {
            'FirstName': contact_info.get('FullName', 'Administrator').split()[0],
            'LastName': ' '.join(contact_info.get('FullName', 'Administrator').split()[1:]) or 'Account',
            'ContactType': 'COMPANY' if contact_info.get('CompanyName') else 'PERSON',
            'AddressLine1': contact_info.get('AddressLine1', '123 Main St'),
            'City': contact_info.get('City', 'Seattle'),
            'State': contact_info.get('StateOrRegion', 'WA'),
            'CountryCode': contact_info.get('CountryCode', 'US'),
            'ZipCode': contact_info.get('PostalCode', '98101'),
            'PhoneNumber': contact_info.get('PhoneNumber', '+1.2065551234'),
            'Email': contact_info.get('EmailAddress', 'admin@example.com')
        }

        if contact_info.get('CompanyName'):
            contact['OrganizationName'] = contact_info['CompanyName']

        print(f"Registering domain {domain_name} with contact: {contact['Email']}")

        # Register domain (nameservers must be set AFTER registration, not during)
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

        # Note: Nameservers will need to be updated after registration completes
        # This can be done manually or through a separate process that polls for completion
        print("Note: Domain registered with default nameservers. Update nameservers after registration completes.")

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {
            'OperationId': registration['OperationId'],
            'Message': f"Domain {domain_name} registration initiated"
        })

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        import traceback
        tb = traceback.format_exc()
        print(tb)
        # Include full error and traceback in CloudFormation response
        cfnresponse.send(event, context, cfnresponse.FAILED, {
            'Error': error_msg,
            'ErrorType': type(e).__name__,
            'Traceback': tb[:1000]  # Limit to 1000 chars to avoid CloudFormation size limits
        })
"""),
            timeout=Duration.seconds(300),
            initial_policy=[
                iam.PolicyStatement(
                    actions=[
                        "route53domains:CheckDomainAvailability",
                        "route53domains:GetDomainDetail",
                        "route53domains:RegisterDomain",
                        "route53domains:UpdateDomainNameservers",
                        "route53:GetHostedZone",
                        "account:GetContactInformation"
                    ],
                    resources=["*"]
                )
            ]
        )

        # Custom resource to trigger domain registration check
        domain_registration = CustomResource(
            self, "DomainRegistration",
            service_token=domain_registration_handler.function_arn,
            properties={
                "DomainName": config["domain_name"],
                "HostedZoneId": self.hosted_zone.hosted_zone_id
            }
        )
        domain_registration.node.add_dependency(self.hosted_zone)

        # Outputs
        export_prefix = config['domain_name'].replace('.', '-')

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
            value=Fn.join(",", self.hosted_zone.hosted_zone_name_servers or []),
            description=f"Name servers for {config['domain_name']} - configure these at your domain registrar"
        )
