import os
from typing import Dict, Any

from aws_cdk import (
    Stack,
    CfnOutput,
    CustomResource,
    Duration,
    aws_route53 as route53,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct


class DomainStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        lambda_dir = os.path.join(os.path.dirname(__file__), "lambda")

        domain_registration_handler = lambda_.Function(
            self, "DomainRegistrationHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(lambda_dir, exclude=["cfnresponse.py", "cfnresponse.pyi", "py.typed"]),
            timeout=Duration.seconds(900),
            initial_policy=[
                iam.PolicyStatement(
                    actions=[
                        "route53domains:CheckDomainAvailability",
                        "route53domains:GetDomainDetail",
                        "route53domains:RegisterDomain",
                        "route53:ListHostedZonesByName",
                        "route53:GetHostedZone",
                        "route53:CreateHostedZone",
                        "account:GetContactInformation",
                        "organizations:DescribeOrganization"
                    ],
                    resources=["*"]
                )
            ]
        )

        domain_registration = CustomResource(
            self, "DomainRegistration",
            service_token=domain_registration_handler.function_arn,
            properties={
                "DomainName": config["domain_name"]
            }
        )

        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone",
            hosted_zone_id=domain_registration.get_att_string("HostedZoneId"),
            zone_name=config["domain_name"]
        )

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
