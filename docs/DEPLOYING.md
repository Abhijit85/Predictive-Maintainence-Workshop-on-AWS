# Automated Deployment

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0
- MongoDB Atlas organization with API keys (only when `atlas_create=true`)
- Voyage AI API key
- Docker (for custom image builds)

### AWS IAM Permissions

The deploying IAM user or role needs permissions across several AWS services. You can either attach the AWS managed policies listed below (broader access, simpler setup) or create a custom policy with the specific permissions (least-privilege).

#### Option A: AWS Managed Policies (Recommended for Quick Setup)

Attach these managed policies to your IAM user or role:

| Managed Policy | Covers |
|----------------|--------|
| `AmazonECS_FullAccess` | ECS cluster, services, task definitions, capacity providers |
| `AmazonVPCFullAccess` | VPC, subnets, route tables, internet gateways, security groups, prefix lists, VPC endpoints |
| `ElasticLoadBalancingFullAccess` | ALB, target groups, listeners |
| `AmazonS3FullAccess` | S3 buckets and objects |
| `SecretsManagerReadWrite` | Secrets creation and management |
| `CloudWatchLogsFullAccess` | Log groups and log streams |
| `AmazonEventBridgeFullAccess` | EventBridge rules and targets |
| `AmazonSNSFullAccess` | SNS topics and subscriptions |
| `IAMFullAccess` | IAM roles, policies, and role attachments |
| `AdministratorAccess-Amplify` | Amplify apps, branches, and deployments |
| `CloudFrontFullAccess` | CloudFront distributions (API proxy) |

If using a private ECR image (`app_use_public_ecr=false`), also add:

| Managed Policy | Covers |
|----------------|--------|
| `AmazonEC2ContainerRegistryFullAccess` | ECR repositories and image push/pull |

#### Option B: Custom Least-Privilege Policy

Create a custom IAM policy with these permissions grouped by service:

**Amazon ECS**
```
ecs:CreateCluster, ecs:DeleteCluster, ecs:DescribeClusters
ecs:CreateService, ecs:DeleteService, ecs:UpdateService, ecs:DescribeServices
ecs:RegisterTaskDefinition, ecs:DeregisterTaskDefinition, ecs:DescribeTaskDefinition
ecs:RunTask, ecs:DescribeTasks, ecs:ListTasks
ecs:CreateCapacityProvider, ecs:DescribeCapacityProviders
ecs:PutClusterCapacityProviders
ecs:TagResource
```

**Amazon EC2 / VPC**
```
ec2:CreateVpc, ec2:DeleteVpc, ec2:DescribeVpcs, ec2:ModifyVpcAttribute
ec2:CreateSubnet, ec2:DeleteSubnet, ec2:DescribeSubnets
ec2:CreateSecurityGroup, ec2:DeleteSecurityGroup, ec2:DescribeSecurityGroups
ec2:AuthorizeSecurityGroupIngress, ec2:RevokeSecurityGroupIngress
ec2:AuthorizeSecurityGroupEgress, ec2:RevokeSecurityGroupEgress
ec2:CreateInternetGateway, ec2:DeleteInternetGateway
ec2:AttachInternetGateway, ec2:DetachInternetGateway, ec2:DescribeInternetGateways
ec2:CreateRouteTable, ec2:DeleteRouteTable, ec2:DescribeRouteTables
ec2:CreateRoute, ec2:DeleteRoute
ec2:AssociateRouteTable, ec2:DisassociateRouteTable
ec2:CreateManagedPrefixList, ec2:DeleteManagedPrefixList
ec2:ModifyManagedPrefixList, ec2:DescribeManagedPrefixLists
ec2:GetManagedPrefixListEntries
ec2:DescribeNetworkInterfaces, ec2:DescribeAvailabilityZones
ec2:DescribeAccountAttributes, ec2:DescribeNetworkAcls
ec2:CreateTags, ec2:DeleteTags, ec2:DescribeTags
```

If `atlas_create=true` (PrivateLink), also add:
```
ec2:CreateVpcEndpoint, ec2:DeleteVpcEndpoints
ec2:DescribeVpcEndpoints, ec2:ModifyVpcEndpoint
```

**Elastic Load Balancing**
```
elasticloadbalancing:CreateLoadBalancer, elasticloadbalancing:DeleteLoadBalancer
elasticloadbalancing:DescribeLoadBalancers, elasticloadbalancing:ModifyLoadBalancerAttributes
elasticloadbalancing:DescribeLoadBalancerAttributes
elasticloadbalancing:CreateTargetGroup, elasticloadbalancing:DeleteTargetGroup
elasticloadbalancing:DescribeTargetGroups, elasticloadbalancing:ModifyTargetGroupAttributes
elasticloadbalancing:DescribeTargetGroupAttributes
elasticloadbalancing:RegisterTargets, elasticloadbalancing:DeregisterTargets
elasticloadbalancing:DescribeTargetHealth
elasticloadbalancing:CreateListener, elasticloadbalancing:DeleteListener
elasticloadbalancing:DescribeListeners
elasticloadbalancing:AddTags, elasticloadbalancing:DescribeTags
```

**Amazon S3**
```
s3:CreateBucket, s3:DeleteBucket, s3:ListBucket
s3:GetBucketVersioning, s3:PutBucketVersioning
s3:GetBucketObjectLockConfiguration, s3:PutBucketObjectLockConfiguration
s3:GetBucketPolicy, s3:PutBucketPolicy, s3:DeleteBucketPolicy
s3:GetBucketPublicAccessBlock, s3:PutBucketPublicAccessBlock
s3:PutObject, s3:GetObject, s3:DeleteObject
s3:GetBucketTagging, s3:PutBucketTagging
```

**AWS Secrets Manager**
```
secretsmanager:CreateSecret, secretsmanager:DeleteSecret
secretsmanager:DescribeSecret, secretsmanager:GetSecretValue
secretsmanager:PutSecretValue, secretsmanager:UpdateSecret
secretsmanager:TagResource
```

**Amazon CloudWatch Logs**
```
logs:CreateLogGroup, logs:DeleteLogGroup
logs:DescribeLogGroups, logs:PutRetentionPolicy
logs:ListTagsForResource, logs:TagResource
```

**Amazon EventBridge**
```
events:PutRule, events:DeleteRule, events:DescribeRule
events:PutTargets, events:RemoveTargets, events:ListTargsByRule
events:ListTagsForResource, events:TagResource
```

**Amazon SNS**
```
sns:CreateTopic, sns:DeleteTopic
sns:GetTopicAttributes, sns:SetTopicAttributes
sns:Subscribe, sns:Unsubscribe
sns:ListTagsForResource, sns:TagResource
```

**AWS IAM**
```
iam:CreateRole, iam:DeleteRole, iam:GetRole
iam:ListRolePolicies, iam:ListAttachedRolePolicies
iam:PutRolePolicy, iam:DeleteRolePolicy
iam:AttachRolePolicy, iam:DetachRolePolicy
iam:CreatePolicy, iam:DeletePolicy, iam:GetPolicy
iam:GetPolicyVersion, iam:CreatePolicyVersion, iam:DeletePolicyVersion
iam:ListPolicyVersions
iam:PassRole
iam:TagRole, iam:TagPolicy
iam:CreateServiceLinkedRole
```

**AWS Amplify**
```
amplify:CreateApp, amplify:DeleteApp, amplify:GetApp, amplify:UpdateApp
amplify:CreateBranch, amplify:DeleteBranch, amplify:UpdateBranch
amplify:CreateDeployment, amplify:StartDeployment
amplify:ListApps
```

**Amazon CloudFront**
```
cloudfront:CreateDistribution, cloudfront:DeleteDistribution
cloudfront:GetDistribution, cloudfront:UpdateDistribution
cloudfront:TagResource, cloudfront:ListTagsForResource
```

**Amazon ECR** (only when `app_use_public_ecr=false`):
```
ecr:CreateRepository, ecr:DeleteRepository, ecr:DescribeRepositories
ecr:GetAuthorizationToken
ecr:BatchCheckLayerAvailability, ecr:PutImage
ecr:InitiateLayerUpload, ecr:UploadLayerPart, ecr:CompleteLayerUpload
ecr:BatchGetImage, ecr:GetDownloadUrlForLayer
```

**AWS STS** (always required):
```
sts:GetCallerIdentity
```

## One-Click Deployment (Public ECR)

Uses a pre-built public ECR image:

```bash
cd deployment

# Edit Makefile with your AWS credentials or export them:
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_REGION="us-east-1"

make deploy-with-public-ecr
```

### Configuration

Edit `deployment/config/deploy-with-public-ecr.tfvars.json`:

```json
{
  "app_use_public_ecr": true,
  "app_simulation": true,
  "app_indexing": true,
  "app_generate_models": false,
  "atlas_create": true,
  "atlas_public_key": "your-atlas-public-key",
  "atlas_org_id": "your-atlas-org-id",
  "atlas_password": "your-atlas-password",
  "atlas_private_key": "your-atlas-private-key",
  "aws_create": true,
  "voyage_api_key": "your-voyage-api-key",
  "acm_certificate_arn": "",
  "alert_email": "alerts@example.com"
}
```

## Custom Image Deployment

Build your own Docker image and deploy:

```bash
cd deployment
make deploy-with-build
```

Edit `deployment/config/deploy-with-build.tfvars.json` with the same variables.

## What Gets Deployed

| Resource | Description |
|----------|-------------|
| VPC + Subnets | Network infrastructure with public and private subnets |
| ECS Cluster | Fargate cluster for API and Stream services |
| API Service | FastAPI behind ALB (1 task) |
| Stream Service | Change stream processor (1 task) |
| ALB | Application Load Balancer with health checks |
| CloudFront | HTTPS proxy from Amplify to ALB |
| Amplify | React frontend hosting with API proxy rules |
| EventBridge | Simulation scheduler (1/min) |
| MongoDB Atlas | Cluster with PrivateLink connectivity (when `atlas_create=true`) |
| Secrets Manager | MONGODB_URI and VOYAGE_API_KEY |
| CloudWatch | Log group with 30-day retention |
| SNS | Alert topic with optional email subscription |
| S3 | Model and encoder storage |
| ECR | Private Docker repository (when `app_use_public_ecr=false`) |
| IAM | Service roles and policies for all AWS integrations |

## Deploying with an External MongoDB (No Atlas Creation)

If you already have a MongoDB Atlas cluster (or any MongoDB instance with replica set support for change streams), you can skip Atlas provisioning:

1. In your tfvars file, set:
   ```json
   {
     "atlas_create": false,
     "mongodb_uri": "mongodb+srv://user:password@your-cluster.mongodb.net/"
   }
   ```

2. Remove or leave empty the Atlas-specific variables (`atlas_public_key`, `atlas_private_key`, `atlas_org_id`, `atlas_password`).

3. Deploy as usual:
   ```bash
   make deploy-with-public-ecr
   ```

See `deployment/config/deploy-local.tfvars.json` for a template.

> **Note:** When `atlas_create=false`, PrivateLink resources are not created. Your MongoDB instance must be reachable from the VPC (e.g., via Atlas network peering, public endpoint with IP allowlist, or a VPN).

## HTTPS (Optional)

To enable HTTPS on the ALB, set `acm_certificate_arn` to your ACM certificate ARN in the tfvars file.

## Tear Down

```bash
cd deployment
make destroy-with-public-ecr
```

## Network Architecture

### Request Flow

```
Browser
  └─> Amplify (HTTPS, *.amplifyapp.com)
        ├─ Static assets (HTML/JS/CSS) → served directly from Amplify
        └─ /api/* and /health requests → Amplify proxy rewrite rules
              └─> CloudFront (HTTPS, *.cloudfront.net)
                    └─> ALB (HTTP, port 80)
                          └─> ECS Fargate API service (port 5001)
```

Amplify requires HTTPS targets in proxy rewrite rules. Since the ALB only serves HTTP (unless an ACM certificate is provided), a CloudFront distribution sits between Amplify and the ALB to provide the HTTPS termination. CloudFront connects to the ALB over HTTP (`origin_protocol_policy = "http-only"`). All caching is disabled (`default_ttl = 0`) so every API request reaches the backend.

### Security Groups

The ALB uses **two security groups** to stay within the default 60-rules-per-SG limit:

| Security Group | Purpose | Entries |
|---------------|---------|---------|
| `*-alb-sg` | HTTP/HTTPS from `aws_allowed_ips` prefix list | ~32 CIDRs |
| `*-alb-amp-sg` | HTTP from Amplify proxy (CloudFront origin-facing IPs) | ~45 CIDRs |

AWS counts each prefix list entry as a separate rule. The combined ~77 entries would exceed the 60-rule limit in a single SG, so they are split across two SGs both attached to the ALB.

### NAT Gateway

NAT gateway is **disabled**. ECS services run in public subnets with `assign_public_ip = true`, so they reach the internet directly for pulling Docker images, connecting to MongoDB Atlas (when not using PrivateLink), and calling external APIs (Voyage AI, Bedrock). Private subnets are only used for PrivateLink VPC endpoints when `atlas_create=true`.

### Frontend URL Strategy

The React frontend is built with **relative API URLs** (no hardcoded host/port). When `REACT_APP_FASTAPI_HOST` is not set at build time, all API calls go to `/api/*` on the same origin. Amplify's proxy rewrite rules intercept these paths and forward them through CloudFront to the ALB. This eliminates mixed-content issues (HTTPS frontend calling HTTP API) and CORS configuration.

For local development, set `REACT_APP_FASTAPI_HOST=127.0.0.1` and `REACT_APP_FASTAPI_PORT=5001` before `npm start`.

## Deployment Notes

### Startup Order

The entrypoint script (`entrypoint.sh`) handles startup order automatically:

1. **S3 sync** — pulls pre-trained models/encoders (ECS only)
2. **Indexing** (`INDEXING=true`) — creates info collection + search indexes. Must run before predictions.
3. **Model training** (`GENERATE_MODELS=true`) — trains models from 6 CSV datasets. Only needed if models aren't pre-built.
4. **CMD** — starts the API server or stream processor

### Idempotent Operations

- **`indexing.py`** is safe to re-run. Info records are upserted (not duplicated), and chunks are cleared and re-indexed.
- **`simulation.py`** automatically creates MongoDB collections for any dataset that doesn't have a corresponding collection yet — works on both fresh and existing databases.
- **`generate_models.py`** overwrites existing model files with freshly trained ones.

### Stream Processor

The stream processor (`stream.py`) discovers sensor collections **once at startup**. If new sensor types are added after it's running, restart the stream processor to pick them up.

## Troubleshooting

### Amplify Rejects HTTP Proxy Targets

Amplify enforces HTTPS-only targets in proxy rewrite rules (`BadRequestException: HTTP URLs cannot be used in custom rules`). This is why the architecture includes a CloudFront distribution between Amplify and the ALB — CloudFront provides HTTPS termination so Amplify can proxy to it, and CloudFront connects to the ALB over HTTP. **Do not attempt to remove CloudFront and proxy Amplify directly to the ALB.**

### Non-ASCII Characters in Security Group Descriptions

AWS rejects non-ASCII characters (em dashes `—`, smart quotes, etc.) in security group `description` fields with `InvalidParameterValue: Character sets beyond ASCII are not supported`. Always use standard ASCII hyphens (`-`) in SG descriptions. Comments in `.tf` files can use any characters.

### Security Group Description Changes Force Replacement

Changing a security group's `description` field forces Terraform to destroy and recreate the SG (`create_before_destroy`). The create step fails with `InvalidGroup.Duplicate` if the old SG (with the same `name`) hasn't been deleted yet. To avoid this:
- Do not change SG descriptions on deployed infrastructure unless necessary.
- If you must change a description, also change the SG `name` to avoid the duplicate name conflict.

### Orphaned Resources After Failed Applies

If `terraform apply` partially fails (e.g., some resources created, others errored), the successfully created resources remain in AWS but may not be in Terraform state. After fixing the root cause and re-running apply, Terraform may create duplicates. To clean up:
1. Check for orphaned resources: `aws ec2 describe-security-groups`, `aws cloudfront list-distributions`, etc.
2. Either import them into state (`terraform import`) or delete them manually.
3. CloudFront distributions must be disabled before deletion (disable → wait for deploy → delete).

## Terraform Validation

```bash
cd deployment/one-click/terraform
terraform init
terraform validate
terraform plan -var-file="../../../deployment/config/deploy-with-public-ecr.tfvars.json"
```
