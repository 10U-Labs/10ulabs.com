output "lambda_function_arn" {
  value = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.handler.function_name
}

output "cluster_arn" {
  value = aws_ecs_cluster.runner.arn
}

output "cluster_name" {
  value = aws_ecs_cluster.runner.name
}

output "container_name" {
  value = var.container_name
}

output "execution_role_arn" {
  value = aws_iam_role.ecs_execution_role.arn
}

output "fargate_cpu_architecture" {
  value = var.fargate_cpu_architecture
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.runner.arn
}

output "task_role_arn" {
  value = aws_iam_role.ecs_task_role.arn
}

output "task_role_name" {
  value = aws_iam_role.ecs_task_role.name
}

output "lambda_role_name" {
  value = aws_iam_role.lambda_execution.name
}
