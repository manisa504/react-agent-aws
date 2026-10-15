# Complete AWS teardown checkpoint

Teardown is destructive and requires explicit owner approval for the named resources. No cleanup runs automatically on page close, merge, or application shutdown.

## Confirm the target and save inventory

```sh
export AWS_PROFILE=research AWS_REGION=us-east-1
aws sts get-caller-identity
# Confirm Account/Arn with the owner before any deletion.
aws cloudformation describe-stacks --stack-name ReActWorkbenchStack
aws cloudformation list-stack-resources --stack-name ReActWorkbenchStack > .build/pre-teardown-resources.json
bash scripts/check-aws-resources.sh
```

Record the confirmed account, region, stack name, Amplify App ID/branch/domain, table name, SQS/DLQ URLs, functions, log groups, Cognito pool/client, API ID and alarm names. Use `.build/aws-outputs.json` and CloudFormation's resource inventory. Save the specific IDs before destroying the stack. Do not publish account inventory or credentials in Git.

Stop new requests and disable Amplify auto-builds. Save screenshots and any run data that should survive. Explain that the DynamoDB table is retained intentionally and ask whether its data should be exported or deleted.

## Remove separately managed Amplify

Inspect `aws amplify get-app --app-id "$AMPLIFY_APP_ID"`. Match its repository, name, branch and region to this project. List branches and custom domains; remove custom domains and associated DNS records deliberately if they were created solely for this demo. After confirming the app ID with the owner:

```sh
aws amplify delete-app --app-id "$AMPLIFY_APP_ID"
```

Verify the app is absent with `get-app` and list-apps; distinguish a NotFound result from access denial. A CDK destroy cannot delete this manually created Amplify app. Check separately managed DNS/custom-domain resources before declaring complete cleanup.

## Destroy this backend stack

From `infra`, after confirmation:

```sh
npx cdk destroy ReActWorkbenchStack --profile "$AWS_PROFILE"
```

This stack's Lambda functions, queues/DLQ, log groups, alarms, API Gateway and Cognito resources use deletion behavior. Confirm successful CloudFormation deletion; a failed destroy is not successful cleanup.

**The DynamoDB table uses RETAIN.** Verify its name and `Project=ReActWorkbench` tag using the saved inventory, confirm backup/export requirements, and obtain specific approval before deletion:

```sh
aws dynamodb describe-table --table-name "$TABLE_NAME"
aws dynamodb list-backups --table-name "$TABLE_NAME"
# Only after confirming this exact table and approving data loss:
aws dynamodb delete-table --table-name "$TABLE_NAME"
aws dynamodb wait table-not-exists --table-name "$TABLE_NAME"
```

Delete any on-demand backups separately only if created for this project and specifically approved. TTL is asynchronous expiration, not a substitute for deleting a retained table.

## Verify actual absence

Run `bash scripts/check-aws-resources.sh` again in the same confirmed account and region. Cross-check every ID in `.build/pre-teardown-resources.json`:

- CloudFormation: project stack is DELETE_COMPLETE or absent.
- Amplify: recorded app, branches and custom domains are absent.
- DynamoDB: retained table and consciously selected backups are gone, or explicitly recorded as intentionally retained.
- SQS: get-queue-attributes for both saved URLs returns NonExistentQueue.
- Lambda: get-function for both saved names returns ResourceNotFound.
- CloudWatch: saved log groups and both alarms are absent.
- API Gateway: get-api for the saved API ID returns NotFound.
- Cognito: describe-user-pool for the saved pool returns ResourceNotFound.

A permissions error is not proof of absence. Investigate each leftover through its saved project identity before deleting it. The read-only helper also inventories account resources for manual comparison; it never deletes them.

Only check additional regions if resources were actually deployed there. This project creates no provisioned Bedrock throughput, knowledge base, secret, or VPC; do not delete unrelated existing resources. **Never remove shared CDKToolkit, bootstrap S3/ECR assets, shared IAM roles, or unrelated budget alerts.**

Revisit actual billing after usage appears; cost reporting can lag. Budget alerts are notifications, not caps. Document any intentional retention, its purpose, and the responsible owner.

## Static documentation deployment

Run `make docs-build` (or `npm run docs:build`) and publish the contents of `docs/dist` as the static site root. The build copies referenced diagrams, screenshots, Markdown, and the executed evaluation report, rebases links, and validates local targets. Serving the raw `/docs` directory would break parent-relative assets.
