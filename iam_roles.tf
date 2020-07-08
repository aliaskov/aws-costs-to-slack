# IAM roles to allow Lambda functions to access different AWS resources.

# Fetch our own account id and region. Used in our IAM policy templates.
data "aws_caller_identity" "current" {}


# Role for our 'get_aws_costs' lambda to assume.
# This is used by lambdas that manage instance lifecycles.
resource "aws_iam_role" "lambda_get_aws_costs" {
  name               = "lambda_get_aws_costs"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      }
    }
  ]
}
EOF
}

# Here we ingest the template and create the role policies
# Template for our 'stop_and_terminate_instances' lambda IAM policy



data "template_file" "iam_lambda_get_aws_costs_policy" {
  template = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
              "logs:CreateLogStream",
              "budgets:ViewBudget",
              "aws-portal:*Usage",
              "organizations:DescribeOrganization",
              "aws-portal:*PaymentMethods",
              "aws-portal:*",
              "cur:*",
              "aws-portal:*Billing",
              "ce:*",
              "logs:CreateLogGroup",
              "logs:PutLogEvents",
              "budgets:ModifyBudget"
            ],
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": "organizations:DescribeAccount",
            "Resource": "arn:aws:organizations::*:account/o-*/*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy" "lambda_get_aws_costs" {
  name   = "lambda_get_aws_costs"
  policy = "${data.template_file.iam_lambda_get_aws_costs_policy.rendered}"
  role   = "${aws_iam_role.lambda_get_aws_costs.id}"
}
