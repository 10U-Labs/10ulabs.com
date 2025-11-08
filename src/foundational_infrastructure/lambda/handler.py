import time
import traceback

import boto3
from botocore.exceptions import ClientError
import cfnresponse

COUNTRY_DIALING_CODES = {
    'US': '1', 'CA': '1', 'GB': '44', 'AU': '61', 'DE': '49', 'FR': '33',
    'IT': '39', 'ES': '34', 'NL': '31', 'BE': '32', 'CH': '41', 'AT': '43',
    'SE': '46', 'NO': '47', 'DK': '45', 'FI': '358', 'IE': '353', 'NZ': '64',
    'JP': '81', 'KR': '82', 'CN': '86', 'IN': '91', 'BR': '55', 'MX': '52'
}


def get_existing_domain_zone(route53domains, route53, domain_name):
    domain_detail = route53domains.get_domain_detail(DomainName=domain_name)
    print(f"Domain {domain_name} is already registered")

    zones = route53.list_hosted_zones_by_name(DNSName=domain_name, MaxItems='10')
    matching_zone = None
    for zone in zones.get('HostedZones', []):
        if zone['Name'] == f"{domain_name}.":
            matching_zone = zone
            break

    if not matching_zone:
        return None, None, f"Domain {domain_name} is registered but no hosted zone found. This should not happen."

    zone_id = matching_zone['Id'].split('/')[-1]
    hz_detail = route53.get_hosted_zone(Id=matching_zone['Id'])
    nameservers = hz_detail['DelegationSet']['NameServers']

    print(f"Found hosted zone {zone_id} with nameservers: {nameservers}")

    return {
        'HostedZoneId': zone_id,
        'NameServers': ','.join(nameservers),
        'DomainStatus': domain_detail['StatusList'][0] if domain_detail.get('StatusList') else 'REGISTERED',
        'AlreadyRegistered': 'true'
    }, None, None


def get_contact_info(account, organizations):
    print("Fetching root account email from Organizations API...")
    org_info = organizations.describe_organization()
    contact_email = org_info['Organization']['MasterAccountEmail']
    print(f"Using root account email: {contact_email}")

    print("Fetching AWS account contact information...")
    contact_info = account.get_contact_information()['ContactInformation']

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

    full_name_parts = contact_info['FullName'].split(maxsplit=1)

    phone = contact_info['PhoneNumber']
    phone_digits = ''.join(c for c in phone if c.isdigit())

    country_iso = contact_info['CountryCode']
    country_dialing_code = COUNTRY_DIALING_CODES.get(country_iso, '1')

    if phone_digits.startswith(country_dialing_code):
        phone_formatted = f"+{country_dialing_code}.{phone_digits[len(country_dialing_code):]}"
    else:
        phone_formatted = f"+{country_dialing_code}.{phone_digits}"

    contact = {
        'FirstName': full_name_parts[0],
        'LastName': full_name_parts[1] if len(full_name_parts) > 1 else full_name_parts[0],
        'ContactType': 'COMPANY' if contact_info.get('CompanyName') else 'PERSON',
        'AddressLine1': contact_info['AddressLine1'],
        'City': contact_info['City'],
        'State': contact_info['StateOrRegion'],
        'CountryCode': contact_info['CountryCode'],
        'ZipCode': contact_info['PostalCode'],
        'PhoneNumber': phone_formatted,
        'Email': contact_email
    }

    if contact_info.get('CompanyName'):
        contact['OrganizationName'] = contact_info['CompanyName']

    return contact


def register_new_domain(route53domains, account, organizations, domain_name):
    domain_availability = route53domains.check_domain_availability(DomainName=domain_name)['Availability']
    if domain_availability != 'AVAILABLE':
        return None, {
            'Error': f"Domain {domain_name} is not available: {domain_availability}"
        }

    registration_contact = get_contact_info(account, organizations)
    print(f"Registering domain {domain_name} with contact: {registration_contact['Email']}")

    registration = route53domains.register_domain(
        DomainName=domain_name,
        DurationInYears=1,
        AutoRenew=True,
        AdminContact=registration_contact,
        RegistrantContact=registration_contact,
        TechContact=registration_contact,
        PrivacyProtectAdminContact=True,
        PrivacyProtectRegistrantContact=True,
        PrivacyProtectTechContact=True
    )

    print(f"Domain registration initiated: {registration['OperationId']}")
    print("AWS will automatically create a hosted zone for this domain")

    print("Checking registration operation status...")
    time.sleep(5)
    operation_detail = route53domains.get_operation_detail(OperationId=registration['OperationId'])
    if operation_detail['Status'] == 'FAILED':
        error_msg = operation_detail.get('Message', 'Domain registration failed')
        print(f"Registration failed: {error_msg}")
        return None, {
            'Error': error_msg,
            'OperationId': registration['OperationId'],
            'Hint': 'Check AWS account payment method and currency settings at https://console.aws.amazon.com/billing/home#/paymentmethods'
        }

    return registration, None


def wait_for_hosted_zone(route53, domain_name, registration):
    max_wait_time = 840
    attempt = 0
    elapsed = 0

    while elapsed < max_wait_time:
        wait_time = 2 ** attempt
        time.sleep(wait_time)
        elapsed += wait_time
        attempt += 1

        print(f"Checking for hosted zone (attempt {attempt}, elapsed {elapsed}s)...")

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

                return {
                    'HostedZoneId': zone_id,
                    'NameServers': ','.join(nameservers),
                    'OperationId': registration['OperationId'],
                    'Message': f"Domain {domain_name} registered successfully"
                }, None

            print(f"Hosted zone not yet available, will retry in {2 ** attempt}s...")

        except ClientError as e:
            print(f"Error checking for hosted zone: {e}")

    print("Domain registration initiated but hosted zone not yet available.")
    print("Re-deploy the stack later to complete setup once zone appears.")

    return None, {
        'Error': 'Hosted zone not created within timeout period',
        'OperationId': registration['OperationId'],
        'Message': 'Domain registration initiated but hosted zone not yet available. Wait a few minutes and re-deploy.'
    }


def handler(event, context):
    route53domains = boto3.client('route53domains', region_name='us-east-1')
    route53 = boto3.client('route53')
    account = boto3.client('account', region_name='us-east-1')
    organizations = boto3.client('organizations', region_name='us-east-1')

    domain_name = event['ResourceProperties']['DomainName']

    try:
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
            return

        try:
            response_data, error_data, error_msg = get_existing_domain_zone(route53domains, route53, domain_name)
            if error_msg:
                print(error_msg)
                cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': error_msg})
                return
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
            return

        except route53domains.exceptions.InvalidInput:
            print(f"Domain {domain_name} not registered, proceeding with registration...")

        registration, reg_error = register_new_domain(route53domains, account, organizations, domain_name)
        if reg_error:
            cfnresponse.send(event, context, cfnresponse.FAILED, reg_error)
            return

        response_data, error_data = wait_for_hosted_zone(route53, domain_name, registration)

        if response_data:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
        else:
            cfnresponse.send(event, context, cfnresponse.FAILED, error_data)

    except (ClientError, ValueError, KeyError) as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        tb = traceback.format_exc()
        print(tb)
        cfnresponse.send(event, context, cfnresponse.FAILED, {
            'Error': error_msg,
            'ErrorType': type(e).__name__,
            'Traceback': tb[:1000]
        })
