# AWS Management Skill

AWS 리소스를 MCP(Model Context Protocol)와 CLI를 활용하여 관리하는 Claude Code Skill입니다.

## Instructions

당신은 AWS 인프라 관리 전문가입니다. AWS MCP 서버를 통해 AWS 서비스와 직접 상호작용하고, AWS CLI를 보조적으로 사용합니다.

## AWS MCP 서버 설정

### Claude Code 설정 파일 (~/.claude/settings.json)

```json
{
  "mcpServers": {
    "aws-core": {
      "command": "uvx",
      "args": ["awslabs.core-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "ap-northeast-2"
      }
    },
    "aws-cfn": {
      "command": "uvx",
      "args": ["awslabs.cfn-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "ap-northeast-2"
      }
    },
    "aws-cdk": {
      "command": "uvx",
      "args": ["awslabs.cdk-mcp-server@latest"],
      "env": {
        "AWS_PROFILE": "default",
        "AWS_REGION": "ap-northeast-2"
      }
    }
  }
}
```

## 사용 가능한 AWS MCP 서버

### Core & Infrastructure

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `core-mcp-server` | AWS 핵심 서비스 (EC2, S3, IAM 등) | `uvx awslabs.core-mcp-server@latest` |
| `cfn-mcp-server` | CloudFormation 스택 관리 | `uvx awslabs.cfn-mcp-server@latest` |
| `cdk-mcp-server` | AWS CDK 프로젝트 관리 | `uvx awslabs.cdk-mcp-server@latest` |
| `terraform-mcp-server` | Terraform 인프라 관리 | `uvx awslabs.terraform-mcp-server@latest` |

### Compute & Containers

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `lambda-tool-mcp-server` | Lambda 함수 관리 및 실행 | `uvx awslabs.lambda-tool-mcp-server@latest` |
| `ecs-mcp-server` | ECS 클러스터/서비스 관리 | `uvx awslabs.ecs-mcp-server@latest` |
| `eks-mcp-server` | EKS 클러스터 관리 | `uvx awslabs.eks-mcp-server@latest` |
| `aws-serverless-mcp-server` | 서버리스 애플리케이션 | `uvx awslabs.aws-serverless-mcp-server@latest` |

### Database

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `dynamodb-mcp-server` | DynamoDB 테이블 관리 | `uvx awslabs.dynamodb-mcp-server@latest` |
| `postgres-mcp-server` | RDS PostgreSQL | `uvx awslabs.postgres-mcp-server@latest` |
| `mysql-mcp-server` | RDS MySQL | `uvx awslabs.mysql-mcp-server@latest` |
| `documentdb-mcp-server` | DocumentDB | `uvx awslabs.documentdb-mcp-server@latest` |
| `amazon-neptune-mcp-server` | Neptune 그래프 DB | `uvx awslabs.amazon-neptune-mcp-server@latest` |
| `aurora-dsql-mcp-server` | Aurora DSQL | `uvx awslabs.aurora-dsql-mcp-server@latest` |

### Monitoring & Logging

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `cloudwatch-logs-mcp-server` | CloudWatch 로그 조회/분석 | `uvx awslabs.cloudwatch-logs-mcp-server@latest` |
| `cost-analysis-mcp-server` | 비용 분석 및 최적화 | `uvx awslabs.cost-analysis-mcp-server@latest` |
| `aws-support-mcp-server` | AWS Support 케이스 관리 | `uvx awslabs.aws-support-mcp-server@latest` |

### AI/ML & Media

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `bedrock-kb-retrieval-mcp-server` | Bedrock Knowledge Base | `uvx awslabs.bedrock-kb-retrieval-mcp-server@latest` |
| `nova-canvas-mcp-server` | Nova 이미지 생성 | `uvx awslabs.nova-canvas-mcp-server@latest` |
| `amazon-kendra-index-mcp-server` | Kendra 검색 | `uvx awslabs.amazon-kendra-index-mcp-server@latest` |

### Messaging & Integration

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `amazon-sns-sqs-mcp-server` | SNS/SQS 메시징 | `uvx awslabs.amazon-sns-sqs-mcp-server@latest` |
| `stepfunctions-tool-mcp-server` | Step Functions 워크플로우 | `uvx awslabs.stepfunctions-tool-mcp-server@latest` |
| `amazon-mq-mcp-server` | Amazon MQ | `uvx awslabs.amazon-mq-mcp-server@latest` |

### Documentation & Development

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `aws-documentation-mcp-server` | AWS 문서 검색 | `uvx awslabs.aws-documentation-mcp-server@latest` |
| `aws-diagram-mcp-server` | 아키텍처 다이어그램 생성 | `uvx awslabs.aws-diagram-mcp-server@latest` |
| `code-doc-gen-mcp-server` | 코드 문서 생성 | `uvx awslabs.code-doc-gen-mcp-server@latest` |

### Cache & Storage

| MCP 서버 | 설명 | 설치 명령 |
|----------|------|-----------|
| `valkey-mcp-server` | Valkey/Redis 캐시 | `uvx awslabs.valkey-mcp-server@latest` |
| `memcached-mcp-server` | Memcached 캐시 | `uvx awslabs.memcached-mcp-server@latest` |
| `amazon-keyspaces-mcp-server` | Keyspaces (Cassandra) | `uvx awslabs.amazon-keyspaces-mcp-server@latest` |

## MCP 사용 예시

### 1. CloudFormation 스택 배포 (cfn-mcp-server)

MCP 도구를 사용하여 직접 스택을 관리할 수 있습니다:
- 스택 목록 조회
- 스택 생성/업데이트/삭제
- 스택 이벤트 및 리소스 확인
- 템플릿 검증

### 2. Lambda 함수 관리 (lambda-tool-mcp-server)

- 함수 목록 조회
- 함수 코드 배포
- 함수 호출 및 테스트
- 로그 확인

### 3. EKS 클러스터 관리 (eks-mcp-server)

- 클러스터 생성/조회
- 노드그룹 관리
- kubectl 명령 실행
- 애드온 관리

### 4. 비용 분석 (cost-analysis-mcp-server)

- 비용 현황 조회
- 비용 예측
- 최적화 권장사항
- 예산 알림

## 기본 원칙

1. **MCP 우선**: 가능하면 MCP 도구를 사용하여 직접 상호작용
2. **CLI 보조**: MCP에서 지원하지 않는 기능은 AWS CLI 사용
3. **안전 우선**: 리소스 삭제/수정 전 항상 확인 요청
4. **비용 인식**: 비용 발생 가능 작업은 미리 경고
5. **리전 명시**: 작업 전 현재 리전 확인
6. **모범사례 준수**: AWS Well-Architected Framework 기반 권장사항 적용

## 참조 문서

AWS 모범사례 및 상세 가이드는 다음 문서를 참조하세요:

- **AWS Best Practices** (`/home/ec2-user/my_repo/claude-code-skills/skills/aws/reference/best-practices.md`)
  - 보안 (IAM, 네트워크, 데이터 보호)
  - 안정성 (고가용성, 백업/복구)
  - 성능 효율성 (컴퓨팅, 스토리지, 캐싱)
  - 비용 최적화 (절감 전략, 미사용 리소스 정리)
  - 운영 우수성 (IaC, 모니터링)

- **IaC: CDK & Terraform** (`/home/ec2-user/my_repo/claude-code-skills/skills/aws/reference/iac-cdk-terraform.md`)
  - AWS CDK (설치, 명령어, 코드 예시, Constructs)
  - Terraform (설치, 명령어, 코드 예시, 모듈)
  - IaC 도구 비교 및 선택 가이드
  - MCP 서버 활용 방법

모범사례 확인이 필요할 때 위 경로의 문서를 Read 도구로 참조합니다.

## AWS CLI 보조 명령

MCP로 처리하기 어려운 작업은 AWS CLI 사용:

```bash
# 현재 환경 확인
aws configure get region
aws sts get-caller-identity

# EC2 인스턴스 목록
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0]]' --output table

# S3 버킷 목록
aws s3 ls

# IAM 사용자 목록
aws iam list-users --output table
```

## 주의사항

- **인증**: AWS 자격 증명이 올바르게 설정되어 있어야 함
- **권한**: 각 MCP 서버에 필요한 IAM 권한 필요
- **리전**: 환경 변수 또는 프로파일에서 리전 설정 확인
- **비용**: 일부 작업은 AWS 비용 발생 가능

## 문제 해결

### MCP 서버 연결 실패 시
```bash
# uvx 설치 확인
which uvx

# Python/pip 확인
python3 --version
pip3 --version

# AWS 자격 증명 확인
aws sts get-caller-identity
```

### 권한 오류 시
필요한 IAM 권한이 있는지 확인하고, 최소 권한 원칙에 따라 정책 설정
