# Infrastructure as Code (IaC) Reference

AWS CDK, Terraform, CloudFormation을 활용한 인프라 코드화 가이드입니다.

## MCP 서버 설정

IaC 작업을 위해 다음 MCP 서버들을 활용합니다.

### 필수 MCP 서버

```json
{
  "mcpServers": {
    "aws-cdk": {
      "command": "uvx",
      "args": ["awslabs.cdk-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    },
    "aws-terraform": {
      "command": "uvx",
      "args": ["awslabs.terraform-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    },
    "aws-cfn": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    }
  }
}
```

### MCP 도구 우선순위

| 작업 | 우선 사용 | 보조 |
|------|----------|------|
| CDK 프로젝트 관리 | `aws-cdk` MCP | CLI (`cdk`) |
| Terraform 관리 | `aws-terraform` MCP | CLI (`terraform`) |
| CloudFormation 스택 | `aws-cfn` MCP | CLI (`aws cloudformation`) |
| 리소스 조회 | `aws-core` MCP | AWS CLI |

---

## IaC 도구 비교

| 항목 | CloudFormation | AWS CDK | Terraform |
|------|----------------|---------|-----------|
| **언어** | YAML/JSON | TypeScript, Python, Java 등 | HCL |
| **범위** | AWS 전용 | AWS 전용 | 멀티 클라우드 |
| **상태 관리** | AWS 관리 | AWS 관리 (CFn 기반) | 로컬/원격 상태 파일 |
| **추상화 수준** | 낮음 | 높음 (Constructs) | 중간 |
| **학습 곡선** | 중간 | 낮음 (프로그래머용) | 중간 |

---

## 1. AWS CDK (Cloud Development Kit)

### 1.1 CDK 개요

CDK는 익숙한 프로그래밍 언어로 AWS 인프라를 정의할 수 있는 프레임워크입니다.

```
CDK 코드 (TypeScript/Python)
        ↓ cdk synth
CloudFormation 템플릿
        ↓ cdk deploy
AWS 리소스 생성
```

### 1.2 CDK 설치 및 초기화

```bash
# CDK CLI 설치
npm install -g aws-cdk

# 버전 확인
cdk --version

# 새 프로젝트 초기화
mkdir my-cdk-app && cd my-cdk-app
cdk init app --language typescript

# Python 프로젝트
cdk init app --language python

# CDK Bootstrap (최초 1회)
cdk bootstrap aws://ACCOUNT_ID/ap-northeast-2
```

### 1.3 CDK 프로젝트 구조

```
my-cdk-app/
├── bin/
│   └── my-cdk-app.ts      # 앱 진입점
├── lib/
│   └── my-cdk-app-stack.ts # 스택 정의
├── test/
│   └── my-cdk-app.test.ts  # 테스트
├── cdk.json                # CDK 설정
├── package.json
└── tsconfig.json
```

### 1.4 CDK 기본 명령어

| 명령어 | 설명 |
|--------|------|
| `cdk init` | 새 프로젝트 초기화 |
| `cdk synth` | CloudFormation 템플릿 생성 |
| `cdk diff` | 변경사항 비교 |
| `cdk deploy` | 스택 배포 |
| `cdk destroy` | 스택 삭제 |
| `cdk list` | 스택 목록 |
| `cdk doctor` | 환경 진단 |

### 1.5 CDK 코드 예시

#### VPC 생성 (TypeScript)

```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export class VpcStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC 생성
    this.vpc = new ec2.Vpc(this, 'MyVpc', {
      maxAzs: 2,
      cidr: '10.0.0.0/16',
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
      ],
    });

    // 출력
    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      exportName: 'VpcId',
    });
  }
}
```

#### EC2 인스턴스 (TypeScript)

```typescript
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';

// EC2 인스턴스 생성
const instance = new ec2.Instance(this, 'MyInstance', {
  vpc: vpc,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
  instanceType: ec2.InstanceType.of(
    ec2.InstanceClass.T3,
    ec2.InstanceSize.MEDIUM
  ),
  machineImage: ec2.MachineImage.latestAmazonLinux2023(),

  // IMDSv2 필수 (보안 모범사례)
  requireImdsv2: true,

  // SSM 접근용 역할
  role: new iam.Role(this, 'InstanceRole', {
    assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
    managedPolicies: [
      iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'),
    ],
  }),
});

// EBS 암호화
instance.instance.addPropertyOverride('BlockDeviceMappings', [{
  DeviceName: '/dev/xvda',
  Ebs: {
    Encrypted: true,
    VolumeSize: 30,
    VolumeType: 'gp3',
  },
}]);
```

#### Lambda 함수 (TypeScript)

```typescript
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path';

const fn = new lambda.Function(this, 'MyFunction', {
  runtime: lambda.Runtime.PYTHON_3_12,
  handler: 'index.handler',
  code: lambda.Code.fromAsset(path.join(__dirname, 'lambda')),
  timeout: cdk.Duration.seconds(30),
  memorySize: 256,
  environment: {
    TABLE_NAME: table.tableName,
  },
});

// DynamoDB 권한 부여
table.grantReadWriteData(fn);
```

### 1.6 CDK Constructs 레벨

| 레벨 | 설명 | 예시 |
|------|------|------|
| **L1 (Cfn)** | CloudFormation 리소스 1:1 매핑 | `CfnBucket`, `CfnInstance` |
| **L2 (Default)** | 합리적인 기본값 포함 | `Bucket`, `Function` |
| **L3 (Patterns)** | 여러 리소스 조합 | `ApplicationLoadBalancedFargateService` |

### 1.7 CDK 모범사례

```typescript
// 1. 환경별 설정 분리
const app = new cdk.App();

new MyStack(app, 'Dev', {
  env: { account: '111111111111', region: 'ap-northeast-2' },
  stage: 'dev',
});

new MyStack(app, 'Prod', {
  env: { account: '222222222222', region: 'ap-northeast-2' },
  stage: 'prod',
});

// 2. 태그 일괄 적용
cdk.Tags.of(app).add('Project', 'MyProject');
cdk.Tags.of(app).add('Environment', props.stage);

// 3. Aspects로 정책 강제
import { Aspects, IAspect } from 'aws-cdk-lib';

class EncryptionChecker implements IAspect {
  public visit(node: IConstruct): void {
    if (node instanceof s3.Bucket) {
      if (!node.encryptionKey) {
        Annotations.of(node).addError('S3 버킷은 반드시 암호화되어야 합니다');
      }
    }
  }
}

Aspects.of(app).add(new EncryptionChecker());
```

---

## 2. Terraform

### 2.1 Terraform 개요

Terraform은 HashiCorp의 멀티 클라우드 IaC 도구입니다.

```
Terraform 코드 (.tf)
        ↓ terraform plan
실행 계획 생성
        ↓ terraform apply
클라우드 리소스 생성
        ↓
상태 파일 (terraform.tfstate)
```

### 2.2 Terraform 설치

```bash
# macOS (Homebrew)
brew install terraform

# Linux (Ubuntu/Debian)
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# 버전 확인
terraform --version
```

### 2.3 Terraform 프로젝트 구조

```
my-terraform/
├── main.tf           # 주요 리소스 정의
├── variables.tf      # 변수 선언
├── outputs.tf        # 출력 정의
├── terraform.tfvars  # 변수 값 (gitignore)
├── providers.tf      # 프로바이더 설정
├── versions.tf       # 버전 제약
├── modules/          # 재사용 모듈
│   └── vpc/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/     # 환경별 설정
    ├── dev/
    └── prod/
```

### 2.4 Terraform 기본 명령어

| 명령어 | 설명 |
|--------|------|
| `terraform init` | 프로젝트 초기화, 프로바이더 다운로드 |
| `terraform plan` | 실행 계획 생성 |
| `terraform apply` | 변경사항 적용 |
| `terraform destroy` | 리소스 삭제 |
| `terraform fmt` | 코드 포맷팅 |
| `terraform validate` | 구문 검증 |
| `terraform state list` | 상태 파일 리소스 목록 |
| `terraform import` | 기존 리소스 가져오기 |

### 2.5 Terraform 코드 예시

#### 프로바이더 설정

```hcl
# versions.tf
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # 원격 상태 저장소 (권장)
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# providers.tf
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
```

#### VPC 생성

```hcl
# variables.tf
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-northeast-2a", "ap-northeast-2b"]
}

# main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
    Tier = "Public"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-private-${count.index + 1}"
    Tier = "Private"
  }
}

# outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}
```

#### EC2 인스턴스

```hcl
# 최신 Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

# Security Group
resource "aws_security_group" "instance" {
  name        = "${var.project_name}-instance-sg"
  description = "Security group for EC2 instance"
  vpc_id      = aws_vpc.main.id

  # 아웃바운드만 허용 (인바운드는 필요시 추가)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-instance-sg"
  }
}

# IAM Role
resource "aws_iam_role" "instance" {
  name = "${var.project_name}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instance" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.instance.name
}

# EC2 Instance
resource "aws_instance" "main" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.private[0].id
  vpc_security_group_ids = [aws_security_group.instance.id]
  iam_instance_profile   = aws_iam_instance_profile.instance.name

  # IMDSv2 필수 (보안 모범사례)
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
    http_endpoint               = "enabled"
  }

  # EBS 암호화
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${var.project_name}-instance"
  }
}
```

### 2.6 Terraform 모듈

```hcl
# modules/vpc/main.tf
variable "name" {}
variable "cidr" {}
variable "azs" { type = list(string) }

resource "aws_vpc" "this" {
  cidr_block = var.cidr
  tags       = { Name = var.name }
}

output "vpc_id" {
  value = aws_vpc.this.id
}

# 모듈 사용
module "vpc" {
  source = "./modules/vpc"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["ap-northeast-2a", "ap-northeast-2b"]
}

# 공개 모듈 사용
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["ap-northeast-2a", "ap-northeast-2b"]

  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}
```

### 2.7 Terraform 모범사례

```hcl
# 1. 변수 검증
variable "environment" {
  type        = string
  description = "Environment name"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# 2. 조건부 리소스 생성
resource "aws_nat_gateway" "main" {
  count = var.environment == "prod" ? length(var.azs) : 1

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}

# 3. 로컬 값 활용
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# 4. 데이터 소스 활용
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# 5. 민감한 값 보호
variable "db_password" {
  type      = string
  sensitive = true
}
```

---

## 3. AWS CloudFormation

### 3.1 CloudFormation 개요

CloudFormation은 AWS의 네이티브 IaC 서비스입니다.

```
CloudFormation 템플릿 (YAML/JSON)
        ↓ create-stack / update-stack
스택 생성/업데이트
        ↓
AWS 리소스 프로비저닝
        ↓
스택 상태 관리 (AWS 내부)
```

### 3.2 템플릿 구조

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CloudFormation 템플릿 예시'

# 파라미터 정의
Parameters:
  Environment:
    Type: String
    AllowedValues: [dev, staging, prod]
    Default: dev
  VpcCidr:
    Type: String
    Default: '10.0.0.0/16'

# 조건 정의
Conditions:
  IsProd: !Equals [!Ref Environment, prod]

# 매핑 정의
Mappings:
  RegionMap:
    ap-northeast-2:
      AMI: ami-0c55b159cbfafe1f0
    us-east-1:
      AMI: ami-0947d2ba12ee1ff75

# 리소스 정의
Resources:
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub '${Environment}-vpc'

# 출력 정의
Outputs:
  VpcId:
    Description: VPC ID
    Value: !Ref MyVPC
    Export:
      Name: !Sub '${Environment}-VpcId'
```

### 3.3 CloudFormation CLI 명령어

| 명령어 | 설명 |
|--------|------|
| `aws cloudformation create-stack` | 스택 생성 |
| `aws cloudformation update-stack` | 스택 업데이트 |
| `aws cloudformation delete-stack` | 스택 삭제 |
| `aws cloudformation describe-stacks` | 스택 상태 조회 |
| `aws cloudformation list-stack-resources` | 스택 리소스 목록 |
| `aws cloudformation describe-stack-events` | 스택 이벤트 조회 |
| `aws cloudformation validate-template` | 템플릿 검증 |
| `aws cloudformation create-change-set` | 변경 세트 생성 |

### 3.4 스택 생성 예시

```bash
# 스택 생성
aws cloudformation create-stack \
  --stack-name my-vpc-stack \
  --template-body file://vpc-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=dev \
  --tags Key=Project,Value=MyProject \
  --capabilities CAPABILITY_IAM

# 스택 생성 대기
aws cloudformation wait stack-create-complete \
  --stack-name my-vpc-stack

# 스택 업데이트
aws cloudformation update-stack \
  --stack-name my-vpc-stack \
  --template-body file://vpc-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod

# 변경 세트 사용 (권장)
aws cloudformation create-change-set \
  --stack-name my-vpc-stack \
  --change-set-name my-changes \
  --template-body file://vpc-template.yaml

aws cloudformation describe-change-set \
  --stack-name my-vpc-stack \
  --change-set-name my-changes

aws cloudformation execute-change-set \
  --stack-name my-vpc-stack \
  --change-set-name my-changes
```

### 3.5 CloudFormation 리소스 예시

#### VPC 및 네트워킹

```yaml
Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-vpc'

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Select [0, !Cidr [!Ref VpcCidr, 4, 8]]
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-public-1'

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  VPCGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: VPCGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: '0.0.0.0/0'
      GatewayId: !Ref InternetGateway
```

#### EC2 인스턴스

```yaml
Resources:
  InstanceRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

  InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Roles:
        - !Ref InstanceRole

  SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Instance security group
      VpcId: !Ref VPC
      SecurityGroupEgress:
        - IpProtocol: '-1'
          CidrIp: '0.0.0.0/0'

  EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !FindInMap [RegionMap, !Ref 'AWS::Region', AMI]
      InstanceType: t3.medium
      SubnetId: !Ref PrivateSubnet1
      SecurityGroupIds:
        - !Ref SecurityGroup
      IamInstanceProfile: !Ref InstanceProfile
      # IMDSv2 필수 (보안 모범사례)
      MetadataOptions:
        HttpTokens: required
        HttpPutResponseHopLimit: 2
      BlockDeviceMappings:
        - DeviceName: /dev/xvda
          Ebs:
            VolumeSize: 30
            VolumeType: gp3
            Encrypted: true
      Tags:
        - Key: Name
          Value: !Sub '${AWS::StackName}-instance'
```

#### Lambda 함수

```yaml
Resources:
  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

  LambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-function'
      Runtime: python3.12
      Handler: index.handler
      Role: !GetAtt LambdaRole.Arn
      Timeout: 30
      MemorySize: 256
      Code:
        ZipFile: |
          import json
          def handler(event, context):
              return {
                  'statusCode': 200,
                  'body': json.dumps('Hello from Lambda!')
              }
      Environment:
        Variables:
          ENVIRONMENT: !Ref Environment
```

### 3.6 CloudFormation 내장 함수

| 함수 | 용도 | 예시 |
|------|------|------|
| `!Ref` | 리소스/파라미터 참조 | `!Ref MyVPC` |
| `!GetAtt` | 리소스 속성 가져오기 | `!GetAtt MyVPC.CidrBlock` |
| `!Sub` | 문자열 치환 | `!Sub '${Environment}-vpc'` |
| `!Join` | 문자열 결합 | `!Join ['-', [!Ref Env, 'vpc']]` |
| `!Select` | 리스트에서 선택 | `!Select [0, !GetAZs '']` |
| `!Split` | 문자열 분할 | `!Split [',', !Ref Subnets]` |
| `!If` | 조건부 값 | `!If [IsProd, 3, 1]` |
| `!Equals` | 값 비교 | `!Equals [!Ref Env, prod]` |
| `!FindInMap` | 매핑 조회 | `!FindInMap [RegionMap, !Ref Region, AMI]` |
| `!ImportValue` | 다른 스택 출력 가져오기 | `!ImportValue VpcId` |
| `!Cidr` | CIDR 블록 계산 | `!Cidr [!Ref VpcCidr, 4, 8]` |

### 3.7 CloudFormation 모범사례

```yaml
# 1. 스택 정책으로 중요 리소스 보호
# stack-policy.json
{
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "Update:Replace",
      "Principal": "*",
      "Resource": "LogicalResourceId/ProductionDatabase"
    },
    {
      "Effect": "Allow",
      "Action": "Update:*",
      "Principal": "*",
      "Resource": "*"
    }
  ]
}

# 2. DeletionPolicy로 리소스 보호
Resources:
  Database:
    Type: AWS::RDS::DBInstance
    DeletionPolicy: Retain  # 스택 삭제 시 리소스 유지
    UpdateReplacePolicy: Snapshot  # 교체 시 스냅샷 생성
    Properties:
      # ...

# 3. 종속성 명시
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    DependsOn: VPCGatewayAttachment  # 명시적 종속성
    Properties:
      # ...

# 4. 헬퍼 스크립트 (cfn-init, cfn-signal)
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Metadata:
      AWS::CloudFormation::Init:
        config:
          packages:
            yum:
              httpd: []
          services:
            sysvinit:
              httpd:
                enabled: true
                ensureRunning: true
    Properties:
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          yum update -y
          /opt/aws/bin/cfn-init -v --stack ${AWS::StackName} --resource MyInstance --region ${AWS::Region}
          /opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource MyInstance --region ${AWS::Region}
    CreationPolicy:
      ResourceSignal:
        Timeout: PT15M
```

### 3.8 Nested Stacks (중첩 스택)

```yaml
# 부모 스택
Resources:
  VPCStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: https://s3.amazonaws.com/mybucket/vpc-template.yaml
      Parameters:
        Environment: !Ref Environment
        VpcCidr: !Ref VpcCidr

  EC2Stack:
    Type: AWS::CloudFormation::Stack
    DependsOn: VPCStack
    Properties:
      TemplateURL: https://s3.amazonaws.com/mybucket/ec2-template.yaml
      Parameters:
        VpcId: !GetAtt VPCStack.Outputs.VpcId
        SubnetId: !GetAtt VPCStack.Outputs.PrivateSubnetId

Outputs:
  VpcId:
    Value: !GetAtt VPCStack.Outputs.VpcId
```

### 3.9 StackSets (멀티 계정/리전 배포)

```bash
# StackSet 생성
aws cloudformation create-stack-set \
  --stack-set-name my-stackset \
  --template-body file://template.yaml \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false

# 스택 인스턴스 배포
aws cloudformation create-stack-instances \
  --stack-set-name my-stackset \
  --deployment-targets OrganizationalUnitIds=ou-xxxx-xxxxxxxx \
  --regions ap-northeast-2 us-east-1
```

---

## 4. IaC 선택 가이드

### 상황별 권장 도구

| 상황 | 권장 도구 | 이유 |
|------|----------|------|
| AWS 전용, 빠른 시작 | CDK | 높은 추상화, 익숙한 언어 |
| AWS 전용, 기존 CFn 경험 | CloudFormation | 학습 곡선 없음 |
| 멀티 클라우드 | Terraform | 단일 도구로 관리 |
| 기존 Terraform 코드 존재 | Terraform | 마이그레이션 비용 |
| 복잡한 조건부 로직 | CDK | 프로그래밍 언어 활용 |

### IaC 공통 모범사례

1. **버전 관리**: 모든 IaC 코드를 Git으로 관리
2. **코드 리뷰**: PR 기반 변경 관리
3. **환경 분리**: dev/staging/prod 환경 분리
4. **상태 파일 보호**: 원격 저장소 + 암호화 + 잠금
5. **모듈화**: 재사용 가능한 모듈 작성
6. **CI/CD 통합**: 자동화된 테스트 및 배포

---

## 5. MCP 서버 상세 활용

### 5.1 CDK MCP 서버 (`aws-cdk`)

#### 제공 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| `cdk_list_stacks` | 프로젝트의 스택 목록 조회 | 배포 전 스택 확인 |
| `cdk_synth` | CloudFormation 템플릿 생성 | 템플릿 미리보기 |
| `cdk_diff` | 현재 상태와 변경사항 비교 | 배포 전 영향 확인 |
| `cdk_deploy` | 스택 배포 | 인프라 생성/업데이트 |
| `cdk_destroy` | 스택 삭제 | 리소스 정리 |
| `cdk_bootstrap` | CDK 부트스트랩 | 환경 초기 설정 |
| `cdk_context` | 컨텍스트 값 조회 | 설정 확인 |

#### MCP 활용 워크플로우

```
1. 프로젝트 분석
   └── MCP: cdk_list_stacks → 스택 구조 파악

2. 변경사항 확인
   └── MCP: cdk_diff → 배포 전 변경 내용 검토

3. 템플릿 생성
   └── MCP: cdk_synth → CloudFormation 템플릿 확인

4. 배포
   └── MCP: cdk_deploy → 스택 배포 실행

5. 검증
   └── MCP: aws-cfn으로 스택 상태 확인
```

#### 사용 예시

```
사용자: "현재 CDK 프로젝트의 스택 목록을 보여줘"
→ MCP aws-cdk: cdk_list_stacks 도구 사용

사용자: "VpcStack을 배포하기 전에 변경사항을 확인해줘"
→ MCP aws-cdk: cdk_diff --stack VpcStack 도구 사용

사용자: "VpcStack을 배포해줘"
→ MCP aws-cdk: cdk_deploy --stack VpcStack 도구 사용
```

---

### 5.2 Terraform MCP 서버 (`aws-terraform`)

#### 제공 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| `terraform_init` | 프로젝트 초기화 | 프로바이더 다운로드 |
| `terraform_plan` | 실행 계획 생성 | 변경사항 미리보기 |
| `terraform_apply` | 변경사항 적용 | 리소스 생성/수정 |
| `terraform_destroy` | 리소스 삭제 | 인프라 정리 |
| `terraform_show` | 현재 상태 표시 | 상태 파일 조회 |
| `terraform_state_list` | 상태 리소스 목록 | 관리 리소스 확인 |
| `terraform_output` | 출력값 조회 | 배포 결과 확인 |
| `terraform_validate` | 구문 검증 | 코드 오류 확인 |
| `terraform_fmt` | 코드 포맷팅 | 스타일 통일 |

#### MCP 활용 워크플로우

```
1. 초기화
   └── MCP: terraform_init → 프로바이더 설치

2. 코드 검증
   └── MCP: terraform_validate → 구문 오류 확인
   └── MCP: terraform_fmt → 코드 정리

3. 계획 수립
   └── MCP: terraform_plan → 변경 계획 검토

4. 적용
   └── MCP: terraform_apply → 리소스 생성

5. 결과 확인
   └── MCP: terraform_output → 출력값 조회
   └── MCP: terraform_state_list → 생성된 리소스 확인
```

#### 사용 예시

```
사용자: "Terraform 프로젝트를 초기화해줘"
→ MCP aws-terraform: terraform_init 도구 사용

사용자: "변경 계획을 보여줘"
→ MCP aws-terraform: terraform_plan 도구 사용

사용자: "현재 관리 중인 리소스 목록을 보여줘"
→ MCP aws-terraform: terraform_state_list 도구 사용

사용자: "VPC ID 출력값을 확인해줘"
→ MCP aws-terraform: terraform_output -raw vpc_id 도구 사용
```

---

### 5.3 CloudFormation MCP 서버 (`aws-cfn`)

CDK는 내부적으로 CloudFormation을 사용하므로, 배포된 스택 관리에 `aws-cfn` MCP도 활용합니다.

#### 제공 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| `cfn_list_stacks` | 스택 목록 조회 | 배포된 스택 확인 |
| `cfn_describe_stack` | 스택 상세 정보 | 스택 상태/출력 확인 |
| `cfn_list_resources` | 스택 리소스 목록 | 생성된 리소스 확인 |
| `cfn_get_template` | 스택 템플릿 조회 | 현재 템플릿 확인 |
| `cfn_list_events` | 스택 이벤트 조회 | 배포 진행/오류 확인 |
| `cfn_validate_template` | 템플릿 검증 | 문법 오류 확인 |

#### 사용 예시

```
사용자: "배포된 CloudFormation 스택 목록을 보여줘"
→ MCP aws-cfn: cfn_list_stacks 도구 사용

사용자: "mgmt-vpc 스택의 리소스들을 보여줘"
→ MCP aws-cfn: cfn_list_resources --stack-name mgmt-vpc 도구 사용

사용자: "스택 배포 중 오류가 발생했어. 이벤트를 확인해줘"
→ MCP aws-cfn: cfn_list_events --stack-name <stack-name> 도구 사용
```

---

### 5.4 MCP 통합 활용 시나리오

#### 시나리오 1: CDK로 새 VPC 생성

```
1. CDK 프로젝트 분석
   → MCP aws-cdk: cdk_list_stacks

2. 변경사항 확인
   → MCP aws-cdk: cdk_diff --stack VpcStack

3. 배포 실행
   → MCP aws-cdk: cdk_deploy --stack VpcStack

4. 배포 결과 확인
   → MCP aws-cfn: cfn_describe_stack --stack-name VpcStack
   → MCP aws-cfn: cfn_list_resources --stack-name VpcStack

5. 실제 리소스 확인
   → MCP aws-core: VPC, 서브넷 정보 조회
```

#### 시나리오 2: Terraform으로 EC2 인스턴스 관리

```
1. 프로젝트 초기화
   → MCP aws-terraform: terraform_init

2. 코드 검증
   → MCP aws-terraform: terraform_validate

3. 계획 확인
   → MCP aws-terraform: terraform_plan

4. 적용
   → MCP aws-terraform: terraform_apply

5. 결과 확인
   → MCP aws-terraform: terraform_output
   → MCP aws-terraform: terraform_state_list

6. 실제 리소스 확인
   → MCP aws-core: EC2 인스턴스 정보 조회
```

#### 시나리오 3: 기존 리소스를 Terraform으로 가져오기

```
1. 현재 리소스 확인
   → MCP aws-core: 리소스 ID 조회

2. Terraform 코드 작성
   → 해당 리소스의 .tf 파일 작성

3. Import 실행
   → CLI: terraform import aws_instance.main i-xxxx

4. 상태 확인
   → MCP aws-terraform: terraform_state_list

5. 코드와 상태 동기화 확인
   → MCP aws-terraform: terraform_plan (No changes 확인)
```

---

### 5.5 CLI vs MCP 선택 기준

| 상황 | 권장 | 이유 |
|------|------|------|
| 스택/리소스 조회 | MCP | 구조화된 응답, 빠른 처리 |
| 배포 실행 | MCP | 진행 상황 모니터링 |
| 대화형 작업 | CLI | 사용자 입력 필요 시 |
| 복잡한 파이프라인 | CLI | 스크립트 연동 |
| 디버깅 | CLI + MCP | 상세 로그 확인 |

### 5.6 문제 해결

#### MCP 서버 연결 오류

```bash
# uvx 설치 확인
which uvx

# MCP 서버 수동 테스트
uvx awslabs.cdk-mcp-server@latest --help
uvx awslabs.terraform-mcp-server@latest --help

# AWS 자격 증명 확인
aws sts get-caller-identity
```

#### CDK/Terraform CLI 오류

```bash
# CDK 버전 확인
cdk --version
cdk doctor

# Terraform 버전 확인
terraform --version
terraform providers
```
