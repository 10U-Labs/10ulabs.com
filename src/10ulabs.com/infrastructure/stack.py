from typing import Dict, Any

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    CfnOutput,
)
from constructs import Construct


class TenULabsComStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config

        self.bucket = s3.Bucket(
            self, "WebsiteBucket",
            bucket_name=config["s3"]["bucket_name"],
            website_index_document=config["cloudfront"]["default_root_object"],
            website_error_document="404.html",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False
        )

        oai = cloudfront.OriginAccessIdentity(
            self, "OAI",
            comment=f"OAI for {config['domain']}"
        )

        self.bucket.grant_read(oai)

        price_class_map = {
            "PriceClass_100": cloudfront.PriceClass.PRICE_CLASS_100,
            "PriceClass_200": cloudfront.PriceClass.PRICE_CLASS_200,
            "PriceClass_All": cloudfront.PriceClass.PRICE_CLASS_ALL
        }

        price_class = price_class_map.get(
            config["cloudfront"]["price_class"],
            cloudfront.PriceClass.PRICE_CLASS_100
        )

        certificate = acm.Certificate.from_certificate_arn(
            self, "Certificate",
            certificate_arn=config["certificate"]["arn"]
        )

        self.distribution = cloudfront.Distribution(
            self, "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.bucket,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True
            ),
            domain_names=[config["domain"]],
            certificate=certificate,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            default_root_object=config["cloudfront"]["default_root_object"],
            price_class=price_class,
            enable_logging=False,
            comment=f"CloudFront distribution for {config['domain']}"
        )

        if config["route53"]["hosted_zone_id"]:
            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
                self, "HostedZone",
                hosted_zone_id=config["route53"]["hosted_zone_id"],
                zone_name=config["domain"]
            )

            route53.ARecord(
                self, "AliasRecord",
                zone=hosted_zone,
                target=route53.RecordTarget.from_alias(
                    targets.CloudFrontTarget(self.distribution)
                ),
                record_name=config["domain"]
            )

            route53.AaaaRecord(
                self, "AliasRecordIPv6",
                zone=hosted_zone,
                target=route53.RecordTarget.from_alias(
                    targets.CloudFrontTarget(self.distribution)
                ),
                record_name=config["domain"]
            )

        CfnOutput(
            self, "BucketName",
            value=self.bucket.bucket_name,
            description="S3 bucket for website content"
        )

        CfnOutput(
            self, "DistributionId",
            value=self.distribution.distribution_id,
            description="CloudFront distribution ID"
        )

        CfnOutput(
            self, "DistributionDomainName",
            value=self.distribution.distribution_domain_name,
            description="CloudFront domain name"
        )

        CfnOutput(
            self, "WebsiteURL",
            value=f"https://{config['domain']}",
            description="Website URL"
        )
