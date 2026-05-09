#!/usr/bin/env bash
# applaunch-api/scripts/setup_aws.sh
# AL-4: Create S3 buckets, KMS key, and IAM role for AppLaunch.
#
# Prerequisites:
#   - AWS CLI installed and configured (aws configure)
#   - Sufficient IAM permissions to create buckets, KMS keys, roles, and policies
#
# Usage:
#   chmod +x scripts/setup_aws.sh
#   AWS_ACCOUNT_ID=123456789012 AWS_REGION=us-east-1 ./scripts/setup_aws.sh

set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:?'Set AWS_ACCOUNT_ID env var'}"
SOURCES_BUCKET="applaunch-sources"
ARTIFACTS_BUCKET="applaunch-artifacts"
IAM_USER="applaunch-api"
KMS_ALIAS="alias/applaunch-credentials"

echo "=== AppLaunch AWS Setup ==="
echo "Region:  $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"
echo ""

# ── 1. S3 Buckets ─────────────────────────────────────────────────────────────
echo "[1/4] Creating S3 buckets..."

for BUCKET in "$SOURCES_BUCKET" "$ARTIFACTS_BUCKET"; do
  if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
    echo "  ✓ $BUCKET already exists"
  else
    if [ "$AWS_REGION" = "us-east-1" ]; then
      aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION"
    else
      aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION"
    fi

    # Block all public access
    aws s3api put-public-access-block --bucket "$BUCKET" \
      --public-access-block-configuration \
      "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

    # Server-side encryption at rest
    aws s3api put-bucket-encryption --bucket "$BUCKET" \
      --server-side-encryption-configuration '{
        "Rules": [{
          "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}
        }]
      }'

    echo "  ✓ $BUCKET created"
  fi
done

# ── 2. KMS Key ────────────────────────────────────────────────────────────────
echo "[2/4] Creating KMS key for credential encryption..."

EXISTING_KEY=$(aws kms list-aliases --query "Aliases[?AliasName=='$KMS_ALIAS'].TargetKeyId" --output text 2>/dev/null || true)

if [ -n "$EXISTING_KEY" ]; then
  KMS_KEY_ID="$EXISTING_KEY"
  echo "  ✓ KMS key already exists: $KMS_KEY_ID"
else
  KMS_KEY_ID=$(aws kms create-key \
    --description "AppLaunch credential encryption key" \
    --query "KeyMetadata.KeyId" --output text)

  aws kms create-alias --alias-name "$KMS_ALIAS" --target-key-id "$KMS_KEY_ID"
  echo "  ✓ KMS key created: $KMS_KEY_ID"
fi

KMS_KEY_ARN="arn:aws:kms:${AWS_REGION}:${AWS_ACCOUNT_ID}:key/${KMS_KEY_ID}"

# ── 3. IAM User + Policy ──────────────────────────────────────────────────────
echo "[3/4] Creating IAM user and scoped policy..."

# Create user
if aws iam get-user --user-name "$IAM_USER" 2>/dev/null; then
  echo "  ✓ IAM user $IAM_USER already exists"
else
  aws iam create-user --user-name "$IAM_USER"
  echo "  ✓ IAM user $IAM_USER created"
fi

# Inline policy with least-privilege S3 + KMS access
POLICY_JSON=$(cat "$(dirname "$0")/iam_policy.json" \
  | sed "s|SOURCES_BUCKET|$SOURCES_BUCKET|g" \
  | sed "s|ARTIFACTS_BUCKET|$ARTIFACTS_BUCKET|g" \
  | sed "s|KMS_KEY_ARN|$KMS_KEY_ARN|g")

aws iam put-user-policy \
  --user-name "$IAM_USER" \
  --policy-name "AppLaunchPolicy" \
  --policy-document "$POLICY_JSON"
echo "  ✓ IAM policy attached"

# ── 4. Access Keys ────────────────────────────────────────────────────────────
echo "[4/4] Creating access keys..."

KEY_OUTPUT=$(aws iam create-access-key --user-name "$IAM_USER" --output json)
ACCESS_KEY_ID=$(echo "$KEY_OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['AccessKey']['AccessKeyId'])")
SECRET_KEY=$(echo "$KEY_OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['AccessKey']['SecretAccessKey'])")

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Add these to your .env file:"
echo ""
echo "AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID"
echo "AWS_SECRET_ACCESS_KEY=$SECRET_KEY"
echo "AWS_REGION=$AWS_REGION"
echo "S3_BUCKET_SOURCES=$SOURCES_BUCKET"
echo "S3_BUCKET_ARTIFACTS=$ARTIFACTS_BUCKET"
echo "KMS_KEY_ARN=$KMS_KEY_ARN"
echo ""
echo "⚠️  Save the secret key now — it won't be shown again."
