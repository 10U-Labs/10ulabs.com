from typing import Dict, Any

from aws_cdk import (
    Stack,
    CfnOutput,
    Fn,
    Duration,
    aws_route53 as route53,
)
from constructs import Construct


class GmailEmailProviderStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        domain_name = config["domain_name"]
        export_prefix = domain_name.replace('.', '-')

        hosted_zone_id = Fn.import_value(f"{export_prefix}-HostedZoneId")
        hosted_zone_name = Fn.import_value(f"{export_prefix}-HostedZoneName")

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "ImportedHostedZone",
            hosted_zone_id=hosted_zone_id,
            zone_name=hosted_zone_name
        )

        google_site_verification = config.get("google_site_verification")
        if not google_site_verification:
            raise ValueError("google_site_verification is required in config")

        google_verification_record = route53.TxtRecord(
            self, "GoogleSiteVerification",
            zone=hosted_zone,
            record_name=domain_name,
            values=[f"google-site-verification={google_site_verification}"],
            ttl=Duration.seconds(config.get("ttl", 300))
        )

        CfnOutput(
            self, "GoogleVerificationRecord",
            value=google_verification_record.domain_name,
            description=f"Google site verification TXT record for {domain_name}"
        )

        CfnOutput(
            self, "GoogleVerificationValue",
            value=f"google-site-verification={google_site_verification}",
            description="Google site verification value"
        )
