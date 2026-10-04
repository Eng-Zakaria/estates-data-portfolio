resource "aws_s3_bucket" "lakehouse" {
  bucket        = "${var.project}-${data.aws_caller_identity.current.account_id}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "lakehouse" {
  bucket = aws_s3_bucket.lakehouse.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lakehouse" {
  bucket = aws_s3_bucket.lakehouse.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}

resource "aws_s3_bucket_public_access_block" "lakehouse" {
  bucket                  = aws_s3_bucket.lakehouse.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_caller_identity" "current" {}

resource "aws_glue_catalog_database" "estate" {
  name = "${replace(var.project, "-", "_")}_db"
}

resource "aws_athena_workgroup" "estate" {
  name = "${var.project}-wg"
  configuration {
    result_configuration { output_location = "s3://${aws_s3_bucket.lakehouse.bucket}/athena-results/" }
    bytes_scanned_cutoff_per_query = var.athena_max_scanned_gb * 1073741824
    enforce_workgroup_configuration = true
  }
}

resource "aws_iam_role" "lakehouse_read" {
  name               = "${var.project}-read"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals { type = "Service" identifiers = ["athena.amazonaws.com"] }
  }
}

resource "aws_budgets_budget" "monthly" {
  name         = "${var.project}-monthly"
  budget_type  = "COST"
  limit_amount = "20"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
}
