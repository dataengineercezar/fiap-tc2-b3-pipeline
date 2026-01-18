#!/bin/bash
# Script para criar IAM Roles manualmente via CLI com credenciais adequadas
# Execute este script com um usuário que tenha permissões IAM

set -e

echo "=========================================="
echo "Criando IAM Roles para Lambda Functions"
echo "=========================================="

# Trust Policy para Lambda
cat > /tmp/lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

echo "1. Criando role: b3-pipeline-lambda-scraping-dev"
aws iam create-role \
  --role-name b3-pipeline-lambda-scraping-dev \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --tags \
    Key=Project,Value=b3-pipeline \
    Key=Environment,Value=dev \
    Key=ManagedBy,Value=Manual-Then-Terraform \
    Key=Name,Value=b3-pipeline-lambda-scraping-role

echo "2. Anexando AWSLambdaBasicExecutionRole"
aws iam attach-role-policy \
  --role-name b3-pipeline-lambda-scraping-dev \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo "3. Criando policy inline para S3"
cat > /tmp/s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::pos-tech-b3-pipeline-cezar-2026",
        "arn:aws:s3:::pos-tech-b3-pipeline-cezar-2026/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name b3-pipeline-lambda-scraping-dev \
  --policy-name lambda-s3-access \
  --policy-document file:///tmp/s3-policy.json

echo ""
echo "4. Criando role: b3-pipeline-lambda-trigger-glue-dev"
aws iam create-role \
  --role-name b3-pipeline-lambda-trigger-glue-dev \
  --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
  --tags \
    Key=Project,Value=b3-pipeline \
    Key=Environment,Value=dev \
    Key=ManagedBy,Value=Manual-Then-Terraform \
    Key=Name,Value=b3-pipeline-lambda-trigger-role

echo "5. Anexando AWSLambdaBasicExecutionRole"
aws iam attach-role-policy \
  --role-name b3-pipeline-lambda-trigger-glue-dev \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

echo "6. Criando policy inline para Glue"
cat > /tmp/glue-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:StartJobRun",
        "glue:GetJobRun",
        "glue:GetJobRuns"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name b3-pipeline-lambda-trigger-glue-dev \
  --policy-name lambda-start-glue \
  --policy-document file:///tmp/glue-policy.json

echo ""
echo "✅ Roles criadas com sucesso!"
echo ""
echo "Agora importe no Terraform:"
echo "terraform import module.iam.aws_iam_role.lambda_scraping b3-pipeline-lambda-scraping-dev"
echo "terraform import module.iam.aws_iam_role.lambda_trigger_glue b3-pipeline-lambda-trigger-glue-dev"
echo "terraform import module.iam.aws_iam_role_policy.lambda_s3_access b3-pipeline-lambda-scraping-dev:lambda-s3-access"
echo "terraform import module.iam.aws_iam_role_policy.lambda_start_glue b3-pipeline-lambda-trigger-glue-dev:lambda-start-glue"
echo "terraform import module.iam.aws_iam_role_policy_attachment.lambda_logs b3-pipeline-lambda-scraping-dev/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
echo "terraform import module.iam.aws_iam_role_policy_attachment.lambda_trigger_logs b3-pipeline-lambda-trigger-glue-dev/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
