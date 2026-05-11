#!/usr/bin/env bash
# One-shot AWS deploy: build image -> push to ECR -> deploy CloudFormation stack.
#
# Prereqs (one-time):
#   aws configure
#   aws ssm put-parameter --name /agent-trio/OPENAI_API_KEY --type SecureString --value sk-...
#   aws ssm put-parameter --name /agent-trio/API_AUTH_TOKEN --type SecureString --value $(openssl rand -hex 24)
#
# Required env:
#   AWS_REGION       e.g. us-east-1
#   AWS_ACCOUNT_ID   numeric
#   VPC_ID           vpc-...
#   SUBNET_IDS       comma-separated, two AZs minimum (e.g. subnet-aaa,subnet-bbb)
set -euo pipefail

: "${AWS_REGION:?set AWS_REGION}"
: "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID}"
: "${VPC_ID:?set VPC_ID}"
: "${SUBNET_IDS:?set SUBNET_IDS (comma-separated)}"

REPO=${REPO:-agent-trio}
TAG=${TAG:-latest}
STACK=${STACK:-agent-trio}
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO}:${TAG}"

echo ">> ensuring ECR repo exists"
aws ecr describe-repositories --repository-names "$REPO" --region "$AWS_REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$REPO" --region "$AWS_REGION" >/dev/null

echo ">> docker login"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo ">> build & push $IMAGE_URI"
docker build --platform linux/amd64 -t "$REPO:$TAG" .
docker tag "$REPO:$TAG" "$IMAGE_URI"
docker push "$IMAGE_URI"

echo ">> deploy CloudFormation stack: $STACK"
aws cloudformation deploy \
  --region "$AWS_REGION" \
  --stack-name "$STACK" \
  --template-file deploy/aws/cloudformation.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
      ImageUri="$IMAGE_URI" \
      VpcId="$VPC_ID" \
      SubnetIds="$SUBNET_IDS"

echo ">> waiting for service to stabilize"
aws ecs wait services-stable \
  --region "$AWS_REGION" \
  --cluster agent-trio \
  --services agent-trio || true

URL=$(aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK" \
        --query "Stacks[0].Outputs[?OutputKey=='ServiceUrl'].OutputValue" --output text)
echo ">> deployed: $URL"
echo ">> health: curl $URL/health"
