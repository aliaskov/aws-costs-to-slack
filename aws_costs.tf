# Checks the TTL of your instances, if expired can stop or terminate them.
resource "aws_lambda_function" "AWSCosts" {
  filename         = "./files/AWSCosts.zip"
  function_name    = "AWSCosts2Slack"
  role             = "${aws_iam_role.lambda_get_aws_costs.arn}"
  handler          = "AWSCosts.lambda_handler"
  source_code_hash = "${filesha256("./files/AWSCosts.zip")}"
  runtime          = "python3.7"
  timeout          = "30"
  description      = "Sends AWS costs to slack"
  environment {
    variables = {
      slackChannel = "${var.slack_channel}"
      slackHookUrl = "${var.slack_hook_url}"
    }
  }
}

# Here we create a cloudwatch event rule, essentially a cron job that
# will call our lambda function every day.  Adjust to your schedule.
resource "aws_cloudwatch_event_rule" "send_aws_costs_to_slack" {
  name                = "send_aws_costs_to_slack"
  schedule_expression = "cron(0 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "awscosts_report" {
  rule      = "${aws_cloudwatch_event_rule.send_aws_costs_to_slack.name}"
  target_id = "${aws_lambda_function.AWSCosts.function_name}"
  arn       = "${aws_lambda_function.AWSCosts.arn}"
}

resource "aws_lambda_permission" "allow_cloudwatch_create_aws_costs_report" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.AWSCosts.function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.send_aws_costs_to_slack.arn}"
  depends_on = [
    "aws_lambda_function.AWSCosts"
  ]
}
