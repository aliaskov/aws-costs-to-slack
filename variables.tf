variable "region" {
  default     = "eu-west-1"
  description = "AWS Region"
}

# Set your Slack Webhook URL here.  For extra security you can use AWS KMS to
# encrypt this data in the AWS console.
variable "slack_hook_url" {
  default     = "https://hooks.slack.com/services/XXXXXXXXXXXXXXXXXXX"
  description = "Slack incoming webhook URL, get this from the slack management page."
}

variable "slack_channel" {
  default     = "#aws-costs"
  description = "Slack channel your bot will post messages to."
}
