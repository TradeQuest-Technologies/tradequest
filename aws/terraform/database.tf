# Database infrastructure for TradeQuest

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-postgres"

  # Engine
  engine         = "postgres"
  engine_version = "15.14"
  instance_class = var.db_instance_class

  # Storage
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  # Database
  db_name  = "tradequest"
  username = "tradequest"
  password = random_password.db_password.result

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Backup
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn

  # Performance Insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Deletion protection
  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${local.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres"
  })

  depends_on = [aws_cloudwatch_log_group.rds]
}

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = false  # Avoid special characters that cause RDS issues
  upper   = true
  lower   = true
  numeric = true
}

# ElastiCache Redis Cluster
resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-cache-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cache-subnet-group"
  })
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id         = "${local.name_prefix}-redis"
  description                  = "Redis cluster for TradeQuest"

  # Node configuration
  node_type            = "cache.t3.micro"
  port                 = 6379
  parameter_group_name = "default.redis7"

  # Cluster configuration
  num_cache_clusters = 2

  # Network
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  # Backup
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  # Auth
  auth_token = random_password.redis_password.result

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis"
  })
}

# Random password for Redis
resource "random_password" "redis_password" {
  length  = 32
  special = false
}

# RDS Enhanced Monitoring Role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${local.name_prefix}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/${local.name_prefix}-postgres/postgresql"
  retention_in_days = 7

  tags = local.common_tags
}

# Store database credentials in AWS Secrets Manager
resource "aws_secretsmanager_secret" "database" {
  name        = "${local.name_prefix}/database"
  description = "Database credentials for TradeQuest"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    dbname   = aws_db_instance.main.db_name
  })
}

# Store Redis credentials in AWS Secrets Manager
resource "aws_secretsmanager_secret" "redis" {
  name        = "${local.name_prefix}/redis"
  description = "Redis credentials for TradeQuest"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    host     = aws_elasticache_replication_group.redis.primary_endpoint_address
    port     = aws_elasticache_replication_group.redis.port
    password = random_password.redis_password.result
  })
}
