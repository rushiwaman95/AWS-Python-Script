import boto3

# Input Values
budget_name = 'test-budget'
account_id = '661798055669'  # Replace with your AWS Account ID
notification_threshold = 80  # Set your custom threshold percentage here
budget_limit_amount = '100.0'  # Convert the budget limit amount to a string
email_addresses = ['rushikesh.waman@flentas.com', 'rushiwaman95@gmail.com']  # List of email addresses

# Initialize the AWS SNS client
sns_client = boto3.client('sns')

# Create an SNS topic
sns_topic_response = sns_client.create_topic(Name='MyBudgetTopic')

# Extract the ARN of the created SNS topic
sns_topic_arn = sns_topic_response['TopicArn']

# Subscribe email addresses to the SNS topic
for email in email_addresses:
    sns_client.subscribe(
        TopicArn=sns_topic_arn,
        Protocol='email',
        Endpoint=email
    )

# Initialize the AWS Budgets client
budgets_client = boto3.client('budgets')

# Create a new budget
budget_response = budgets_client.create_budget(
    AccountId=account_id,
    Budget={
        'BudgetName': budget_name,
        'BudgetLimit': {
            'Amount': budget_limit_amount,
            'Unit': 'USD',
        },
        'TimeUnit': 'MONTHLY',
        'BudgetType': 'COST',
    },
    NotificationsWithSubscribers=[
        {
            'Notification': {
                'NotificationType': 'ACTUAL',
                'ComparisonOperator': 'GREATER_THAN',
                'Threshold': notification_threshold,
                'ThresholdType': 'PERCENTAGE'
            },
            'Subscribers': [
                {
                    'SubscriptionType': 'SNS',
                    'Address': sns_topic_arn
                }
            ]
        }
    ]
)

# Print a success message
print("Budget created successfully.")
