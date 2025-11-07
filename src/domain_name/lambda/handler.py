"""Lambda handler for domain registration"""
import boto3
import json
import time
import cfnresponse


def handler(event, context):
    """
    CloudFormation custom resource handler for domain registration.

    Handles:
    - Checking if domain is already registered
    - Registering new domain with AWS account contact info
    - Waiting for hosted zone creation
    - Returning hosted zone details
    """
    route53domains = boto3.client('route53domains', region_name='us-east-1')
    route53 = boto3.client('route53')
    account = boto3.client('account', region_name='us-east-1')
    organizations = boto3.client('organizations', region_name='us-east-1')

    domain_name = event['ResourceProperties']['DomainName']

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

        # Get root account email from Organizations API
        print("Fetching root account email from Organizations API...")
        org_info = organizations.describe_organization()
        contact_email = org_info['Organization']['MasterAccountEmail']
        print(f"Using root account email: {contact_email}")

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
