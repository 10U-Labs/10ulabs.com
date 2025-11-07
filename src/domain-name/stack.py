"""
Domain Infrastructure: 10uf.org

Creates the foundational Route53 hosted zone for 10uf.org.
All services (websites, APIs, etc.) reference this zone.
"""
from typing import Dict, Any
from aws_cdk import (
    Stack,
    CfnOutput,
    Fn,
    aws_route53 as route53,
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
            value=Fn.join(",", self.hosted_zone.hosted_zone_name_servers),
            description=f"Name servers for {config['domain_name']} - configure these at your domain registrar"
        )
