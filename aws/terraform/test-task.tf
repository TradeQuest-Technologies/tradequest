# Talkative test task to verify CloudWatch Logs integration
resource "aws_ecs_task_definition" "test_logging" {
  family                   = "test-logging"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name  = "talkative"
      image = "public.ecr.aws/amazonlinux/amazonlinux:2023"
      
      command = ["/bin/sh", "-c", "while true; do echo $(date) hello-from-ecs; sleep 1; done"]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "test"
        }
      }
    }
  ])

  tags = local.common_tags
}

