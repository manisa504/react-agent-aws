#!/usr/bin/env bash
set -euo pipefail
: "${AWS_PROFILE:?Set AWS_PROFILE to the demo AWS profile}"
: "${AWS_REGION:?Set AWS_REGION to the deployment region}"
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" sts get-caller-identity
printf '\nCloudFormation project stacks (inspect names):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" cloudformation list-stacks --query 'StackSummaries[?contains(StackName, `ReActWorkbench`)].[StackName,StackStatus]' --output table
printf '\nAmplify applications (inspect names/IDs):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" amplify list-apps --query 'apps[].[appId,name]' --output table
printf '\nSQS queues (inspect):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" sqs list-queues --output json
printf '\nDynamoDB tables (inspect):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" dynamodb list-tables --output json
printf '\nLambda functions (inspect):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" lambda list-functions --query 'Functions[].[FunctionName]' --output table
printf '\nCloudWatch log groups (inspect):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" logs describe-log-groups --query 'logGroups[].[logGroupName]' --output table
printf '\nRead-only snapshot complete. This is NOT proof that all resources are gone.\n'
printf '\nProject stack resources (may fail after successful deletion):\n'
if aws --profile "$AWS_PROFILE" --region "$AWS_REGION" cloudformation describe-stacks --stack-name ReActWorkbenchStack >/dev/null 2>&1; then
  aws --profile "$AWS_PROFILE" --region "$AWS_REGION" cloudformation list-stack-resources --stack-name ReActWorkbenchStack --output table
fi
printf '\nHTTP APIs (compare recorded IDs):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" apigatewayv2 get-apis --query 'Items[].[ApiId,Name]' --output table
printf '\nCognito pools (compare recorded pool):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" cognito-idp list-user-pools --max-results 60 --query 'UserPools[].[Id,Name]' --output table
printf '\nCloudWatch alarms (compare recorded names):\n'
aws --profile "$AWS_PROFILE" --region "$AWS_REGION" cloudwatch describe-alarms --alarm-name-prefix ReActWorkbenchStack --query 'MetricAlarms[].[AlarmName,StateValue]' --output table
