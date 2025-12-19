"""CloudWatch utilities for Lambda handlers."""

import logging
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {"cloudwatch_client": None}


def _get_cloudwatch_client() -> Any:
    """Get or create CloudWatch client (singleton)."""
    if _cache["cloudwatch_client"] is None:
        _cache["cloudwatch_client"] = boto3.client("cloudwatch")
    return _cache["cloudwatch_client"]


def publish_metric(
    namespace: str, metric_name: str, value: float, unit: str = "None"
) -> None:
    """Publish a metric to CloudWatch.

    Args:
        namespace: CloudWatch namespace
        metric_name: Name of the metric
        value: Metric value
        unit: Metric unit (default "None")
    """
    try:
        _get_cloudwatch_client().put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                    "Timestamp": datetime.now(timezone.utc),
                }
            ],
        )
    except ClientError as err:
        logger.warning("Failed to publish metric %s: %s", metric_name, str(err))
