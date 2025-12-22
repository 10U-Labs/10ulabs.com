"""Common utilities for Lambda handlers."""

from common.aws_clients import (
    get_dynamodb_client,
    get_ec2_client,
    get_ecs_client,
    get_s3_client,
    get_sns_client,
    get_sqs_client,
    get_ssm_client,
)
from common.cloudwatch import publish_metric
from common.github_api import get_github_token, clear_token_cache, github_api_request
from common.runner_labels import (
    LabelParseError,
    LabelValidationError,
    parse_labels,
    validate_labels,
    get_instance_type,
    get_ecs_config,
    get_task_architecture,
    is_spot,
    get_runner_id_number,
    get_runner_type_from_labels,
    PLATFORMS,
    PRICING_MODELS,
    ECS_COMPUTE,
    ECS_ARCHITECTURES,
    EC2_COMPUTE,
    EC2_ARCHITECTURES,
    COMPUTE_TYPES,
    ALL_ARCHITECTURES,
)
from common.ec2_utils import (
    terminate_ec2_instance,
    find_instances_by_tags,
)
from common.ecs_utils import (
    list_running_task_arns,
    describe_tasks_with_tags,
    extract_task_tags,
    stop_ecs_task,
    get_cluster_from_env,
)
from common.circuit_breaker_utils import (
    enable_event_source_mappings,
    disable_event_source_mappings,
    update_circuit_breaker_state,
)
from common.lambda_utils import get_sqs_records, empty_records_response, count_results
from common.webhook_ingress import (
    get_message_attribute,
    is_webhook_ingress_queue,
    IngressHandler,
)

__all__ = [
    # aws_clients
    "get_dynamodb_client",
    "get_ec2_client",
    "get_ecs_client",
    "get_s3_client",
    "get_sns_client",
    "get_sqs_client",
    "get_ssm_client",
    # cloudwatch
    "publish_metric",
    # github_api
    "get_github_token",
    "clear_token_cache",
    "github_api_request",
    # runner_labels
    "LabelParseError",
    "LabelValidationError",
    "parse_labels",
    "validate_labels",
    "get_instance_type",
    "get_ecs_config",
    "get_task_architecture",
    "is_spot",
    "get_runner_id_number",
    "get_runner_type_from_labels",
    "PLATFORMS",
    "PRICING_MODELS",
    "ECS_COMPUTE",
    "ECS_ARCHITECTURES",
    "EC2_COMPUTE",
    "EC2_ARCHITECTURES",
    "COMPUTE_TYPES",
    "ALL_ARCHITECTURES",
    # ec2_utils
    "terminate_ec2_instance",
    "find_instances_by_tags",
    # ecs_utils
    "list_running_task_arns",
    "describe_tasks_with_tags",
    "extract_task_tags",
    "stop_ecs_task",
    "get_cluster_from_env",
    # circuit_breaker_utils
    "enable_event_source_mappings",
    "disable_event_source_mappings",
    "update_circuit_breaker_state",
    # lambda_utils
    "get_sqs_records",
    "empty_records_response",
    "count_results",
    # webhook_ingress
    "get_message_attribute",
    "is_webhook_ingress_queue",
    "IngressHandler",
]
