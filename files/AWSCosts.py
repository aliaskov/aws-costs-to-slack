#!/usr/bin/env python3

# import argparse
import boto3
from botocore.exceptions import ClientError
import datetime
import json
import logging
#remove
import os

# Required if you want to encrypt your Slack Hook URL in the AWS console
# from base64 import b64decode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SLACK_CHANNEL = os.environ['slackChannel']
# Required if you want to encrypt your Slack Hook URL in the AWS console
# ENCRYPTED_HOOK_URL = os.environ['slackHookUrl']
# HOOK_URL = boto3.client('kms').decrypt(CiphertextBlob=b64decode(os.environ['slackHookUrl']))['Plaintext'].decode('utf-8')
HOOK_URL = os.environ['slackHookUrl']

############################################################################

# This is used as the subject for Slack messages
SUBJECT = "$Top 5 accounts yesterday:"
############################################################################

logger = logging.getLogger()
logger.setLevel(logging.INFO)
lam = boto3.client('lambda')

def lambda_handler(event, context):
    """Sends out a formatted slack message.  Edit to your liking."""

    msg_text = 'Good morning humanoids. Here is your AWS accounts usage report:'

    report = generate_cost_report()
    # print(report)
    # Uncomment send_email to use email instead of slack
    # send_email(
    #     SENDER,
    #     RECIPIENT,
    #     AWS_REGION,
    #     SUBJECT,
    #     report,
    #     CHARSET)

    send_slack_message(
        msg_text,
        title=SUBJECT,
        text="```\n"+report+"\n```",
        fallback=SUBJECT,
        color='warning',
        actions = [
            {
                "type": "button",
                "text": ":moneybag: AWS Cost Explorer",
                "url": "http://amzn.to/2EBAfQu"
            },
            {
                "type": "button",
                "text": ":chart: AWS Console",
                "url": "https://console.aws.amazon.com/ec2/v2/home"
            },
        ]
    )


def generate_cost_report():
    report = ''
    now = datetime.datetime.utcnow()
    start = (now - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    # end = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    end = now.strftime('%Y-%m-%d')

    cd = boto3.client('ce', 'us-east-1')

    results = []

    # summary
    results = []

    token = None
    while True:
        if token:
            kwargs = {'NextPageToken': token}
        else:
            kwargs = {}
        data = cd.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end}, Granularity='DAILY', Metrics=['UnblendedCost'], GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}], **kwargs)
        # data = cd.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end}, Granularity='DAILY', Metrics=['UnblendedCost'], **kwargs)
        results += data["ResultsByTime"]
        # print(data["ResultsByTime"])
        token = data.get('NextPageToken')
        if not token:
            break

    total_results = []

    token = None
    while True:
        if token:
            kwargs = {'NextPageToken': token}
        else:
            kwargs = {}
        data = cd.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end}, Granularity='DAILY', Metrics=['UnblendedCost'], **kwargs)
        total_results += data["ResultsByTime"]
        token = data.get('NextPageToken')
        if not token:
            break

    summary = {}
    for i in [0,1]:
        result_by_time = results[i]
        summary[i] = {}
        for group in result_by_time['Groups']:
            account = group['Keys'][0]
            amount = group['Metrics']['UnblendedCost']['Amount']
            summary[i][account] = amount
    # report += '$Top 5 accounts yesterday:\n'
    for j in sorted(summary[1], key=lambda a: float(summary[1][a]),reverse=True)[0:5]:
        account_name =   boto3.client('organizations').describe_account(AccountId=j).get('Account').get('Name')
        report += '{0}\t{1:.2f} USD ({2:.0f}%)\n'.format(account_name,float(summary[1][j]), 100-float(summary[0][j])/float(summary[1][j])*100)


    report += 'All accounts:\t{0:.2f} USD ({1:.0f}%)'.format(float(total_results[1]['Total']['UnblendedCost']['Amount']), 100-float(total_results[0]['Total']['UnblendedCost']['Amount'])/float(total_results[1]['Total']['UnblendedCost']['Amount'])*100)
    return report
    # print(results)
    # print(json.dumps(summary))



def send_slack_message(msg_text, **kwargs):
    """Sends a slack message to the slackChannel you specify. The only parameter
    required here is msg_text, or the main message body text. If you want to
    format your message use the attachment feature which is documented here:
    https://api.slack.com/docs/messages.  You simply pass in your attachment
    parameters as keyword arguments, or key-value pairs. This function currently
    only supports a single attachment for simplicity's sake.
    """
    slack_message = {
        'channel': SLACK_CHANNEL,
        'text': msg_text,
        'attachments': [ kwargs ]
    }

    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)

if __name__ == '__main__':
    lambda_handler({}, {})
