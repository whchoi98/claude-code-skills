# Security & IAM Reference

AWS 보안 및 IAM 관리 가이드입니다.

## MCP 서버 설정

```json
{
  "mcpServers": {
    "aws-iam": {
      "command": "uvx",
      "args": ["awslabs.iam-mcp-server@latest"],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "aws-ccapi": {
      "command": "uvx",
      "args": ["awslabs.ccapi-mcp-server@latest"],
      "env": {
        "DEFAULT_TAGS": "enabled",
        "SECURITY_SCANNING": "enabled",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### MCP 도구

| 서버 | 도구 | 설명 |
|------|------|------|
| `aws-iam` | `iam_list_users` | IAM 사용자 목록 |
| `aws-iam` | `iam_list_roles` | IAM 역할 목록 |
| `aws-iam` | `iam_get_policy` | 정책 상세 조회 |
| `aws-iam` | `iam_simulate_policy` | 정책 시뮬레이션 |
| `aws-ccapi` | `security_scan` | 보안 스캔 |

---

## 1. IAM 기본 개념

### 1.1 IAM 구성 요소

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              IAM 구조                                        │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │    User     │    │    Group    │    │    Role     │                     │
│  │  (사람)     │    │ (사용자 집합)│    │ (서비스/앱) │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         └──────────────────┼──────────────────┘                             │
│                            ▼                                                │
│                    ┌─────────────┐                                          │
│                    │   Policy    │                                          │
│                    │ (권한 정의) │                                          │
│                    └─────────────┘                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 정책 유형

| 유형 | 설명 | 사용 시점 |
|------|------|----------|
| **AWS 관리형** | AWS 제공, 자동 업데이트 | 일반적인 권한 |
| **고객 관리형** | 직접 생성/관리 | 맞춤형 권한 |
| **인라인** | 단일 엔티티에 직접 연결 | 특수 케이스 |
| **SCP** | Organizations 레벨 | 계정 가드레일 |
| **권한 경계** | 최대 권한 제한 | 위임된 관리 |

---

## 2. IAM 정책 작성

### 2.1 정책 구조

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3Read",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    }
  ]
}
```

### 2.2 주요 조건 키

| 조건 키 | 용도 | 예시 |
|--------|------|------|
| `aws:SourceIp` | 소스 IP 제한 | VPN/사무실 IP만 허용 |
| `aws:RequestedRegion` | 리전 제한 | 서울 리전만 허용 |
| `aws:PrincipalTag` | 태그 기반 접근 | 팀별 권한 |
| `aws:MultiFactorAuthPresent` | MFA 강제 | 민감한 작업 |
| `aws:CurrentTime` | 시간 제한 | 업무 시간만 허용 |

### 2.3 정책 예시

#### EC2 관리자 (제한적)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2FullAccessInRegion",
      "Effect": "Allow",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    },
    {
      "Sid": "DenyTerminateProduction",
      "Effect": "Deny",
      "Action": "ec2:TerminateInstances",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:ResourceTag/Environment": "production"
        }
      }
    }
  ]
}
```

#### S3 버킷별 접근

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::${aws:PrincipalTag/team}-bucket/*"
    }
  ]
}
```

#### MFA 강제

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyWithoutMFA",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

---

## 3. IAM 역할

### 3.1 신뢰 정책 (Trust Policy)

```json
// EC2용 역할
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```json
// 크로스 계정 역할
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

### 3.2 역할 생성

```bash
# 신뢰 정책 파일 생성
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 역할 생성
aws iam create-role \
  --role-name MyEC2Role \
  --assume-role-policy-document file://trust-policy.json

# 정책 연결
aws iam attach-role-policy \
  --role-name MyEC2Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```

### 3.3 역할 전환 (AssumeRole)

```bash
# 임시 자격 증명 획득
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/AdminRole \
  --role-session-name MySession

# 환경 변수 설정
export AWS_ACCESS_KEY_ID=<AccessKeyId>
export AWS_SECRET_ACCESS_KEY=<SecretAccessKey>
export AWS_SESSION_TOKEN=<SessionToken>
```

---

## 4. Service Control Policies (SCP)

### 4.1 SCP 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AWS Organizations                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Root (SCP: FullAWSAccess)                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  OU: Production (SCP: DenyDeleteVPC, RequireIMDSv2)         │   │   │
│  │  │  ├── Account: Prod-1                                        │   │   │
│  │  │  └── Account: Prod-2                                        │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  OU: Development (SCP: RestrictRegions)                     │   │   │
│  │  │  ├── Account: Dev-1                                         │   │   │
│  │  │  └── Account: Dev-2                                         │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 SCP 예시

#### 리전 제한

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonApprovedRegions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "ap-northeast-2",
            "us-east-1"
          ]
        },
        "ArnNotLike": {
          "aws:PrincipalARN": "arn:aws:iam::*:role/OrganizationAdmin"
        }
      }
    }
  ]
}
```

#### 루트 사용 방지

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRootUser",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:root"
        }
      }
    }
  ]
}
```

#### 보안 서비스 비활성화 방지

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyDisableSecurityServices",
      "Effect": "Deny",
      "Action": [
        "guardduty:DeleteDetector",
        "guardduty:DisassociateFromMasterAccount",
        "securityhub:DisableSecurityHub",
        "config:DeleteConfigRule",
        "config:StopConfigurationRecorder",
        "cloudtrail:DeleteTrail",
        "cloudtrail:StopLogging"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 5. 권한 경계 (Permission Boundary)

### 5.1 개념

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  유효 권한 = 자격 증명 정책 ∩ 권한 경계 ∩ SCP                               │
│                                                                             │
│  ┌───────────────────┐                                                     │
│  │    자격 증명 정책   │                                                     │
│  │  ┌─────────────┐  │                                                     │
│  │  │ 권한 경계   │  │  ← 이 교집합만 유효                                  │
│  │  │ ┌───────┐  │  │                                                     │
│  │  │ │ SCP  │  │  │                                                     │
│  │  │ └───────┘  │  │                                                     │
│  │  └─────────────┘  │                                                     │
│  └───────────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 사용 예시

```bash
# 권한 경계 정책 생성
aws iam create-policy \
  --policy-name DeveloperBoundary \
  --policy-document file://boundary-policy.json

# 사용자에게 권한 경계 적용
aws iam put-user-permissions-boundary \
  --user-name developer1 \
  --permissions-boundary arn:aws:iam::123456789012:policy/DeveloperBoundary

# 역할에게 권한 경계 적용
aws iam put-role-permissions-boundary \
  --role-name DeveloperRole \
  --permissions-boundary arn:aws:iam::123456789012:policy/DeveloperBoundary
```

---

## 6. 보안 서비스

### 6.1 필수 보안 서비스

| 서비스 | 용도 | 우선순위 |
|--------|------|----------|
| **IAM Access Analyzer** | 외부 공유 리소스 탐지 | 필수 |
| **CloudTrail** | API 호출 감사 | 필수 |
| **GuardDuty** | 위협 탐지 | 필수 |
| **Security Hub** | 보안 현황 통합 | 필수 |
| **Config** | 리소스 규정 준수 | 권장 |
| **Inspector** | 취약점 스캔 | 권장 |
| **Macie** | 민감 데이터 탐지 | 선택 |

### 6.2 활성화 명령

```bash
# GuardDuty 활성화
aws guardduty create-detector --enable

# Security Hub 활성화
aws securityhub enable-security-hub

# IAM Access Analyzer 활성화
aws accessanalyzer create-analyzer \
  --analyzer-name my-analyzer \
  --type ACCOUNT

# Config 레코더 시작
aws configservice start-configuration-recorder \
  --configuration-recorder-name default
```

---

## 7. 자격 증명 관리

### 7.1 Access Key 모범사례

| 항목 | 권장사항 |
|------|----------|
| 사용 최소화 | IAM 역할 우선 사용 |
| 정기 교체 | 90일마다 교체 |
| 미사용 키 삭제 | 90일 미사용 시 삭제 |
| 하드코딩 금지 | Secrets Manager/Parameter Store 사용 |

```bash
# 미사용 Access Key 확인
aws iam list-access-keys --user-name myuser

aws iam get-access-key-last-used --access-key-id AKIAXXXXXXXX
```

### 7.2 Secrets Manager

```bash
# 시크릿 생성
aws secretsmanager create-secret \
  --name MyDBPassword \
  --secret-string '{"username":"admin","password":"mypassword"}'

# 시크릿 조회
aws secretsmanager get-secret-value --secret-id MyDBPassword

# 자동 교체 활성화
aws secretsmanager rotate-secret \
  --secret-id MyDBPassword \
  --rotation-lambda-arn arn:aws:lambda:xxx:xxx:function:rotation
```

### 7.3 Parameter Store

```bash
# SecureString 파라미터 생성
aws ssm put-parameter \
  --name /myapp/db/password \
  --value "mypassword" \
  --type SecureString

# 파라미터 조회
aws ssm get-parameter \
  --name /myapp/db/password \
  --with-decryption
```

---

## 8. 보안 체크리스트

### IAM

- [ ] 루트 계정 MFA 활성화
- [ ] 루트 계정 Access Key 삭제
- [ ] IAM 사용자 MFA 필수
- [ ] 최소 권한 원칙 적용
- [ ] IAM Access Analyzer 활성화
- [ ] 미사용 자격 증명 정리

### 감사 및 모니터링

- [ ] CloudTrail 전체 리전 활성화
- [ ] CloudTrail S3 버킷 보호
- [ ] GuardDuty 활성화
- [ ] Security Hub 활성화
- [ ] Config Rules 설정

### Organizations

- [ ] SCP로 가드레일 설정
- [ ] 리전 제한 SCP
- [ ] 보안 서비스 비활성화 방지 SCP

### 암호화

- [ ] KMS CMK 사용
- [ ] 키 교체 활성화
- [ ] 키 정책 최소 권한
