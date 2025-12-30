# AWS Infrastructure Agent

Claude Agent SDK를 사용하여 AWS 인프라를 관리하는 에이전트입니다.

## 기능

- EC2 인스턴스 모니터링
- Security Group 보안 분석
- AWS 비용 요약 조회
- AWS CLI 명령 실행 (읽기 전용)

## 설치

```bash
cd agents/aws-agent
pip install -r requirements.txt
```

## 환경 설정

### AWS 자격 증명
```bash
aws configure
# 또는
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=ap-northeast-2
```

### Anthropic API 키
```bash
export ANTHROPIC_API_KEY=your-api-key
```

## 사용법

### 대화형 모드
```bash
python agent.py
```

### 단일 질문 모드
```bash
python agent.py -q "현재 실행 중인 EC2 인스턴스를 알려줘"
```

### 리전 지정
```bash
python agent.py --region us-east-1
```

## 예시 질문

```
- 현재 EC2 인스턴스 상태를 알려줘
- Security Group 중 위험한 설정이 있는지 확인해줘
- 이번 주 AWS 비용은 얼마야?
- VPC 목록을 보여줘
```

## 보안

- **읽기 전용**: 리소스 생성/수정/삭제 명령은 차단됩니다
- **안전한 명령어만 허용**: delete, terminate, create 등 위험한 명령어 필터링
- **AWS 자격 증명 필요**: 적절한 IAM 권한이 설정되어야 합니다

## 필요한 IAM 권한

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ce:GetCostAndUsage",
        "iam:List*",
        "iam:Get*",
        "s3:List*",
        "rds:Describe*",
        "lambda:List*"
      ],
      "Resource": "*"
    }
  ]
}
```

## 도구 목록

| 도구 | 설명 |
|------|------|
| `aws_cli` | AWS CLI 명령 실행 (읽기 전용) |
| `get_ec2_instances` | EC2 인스턴스 목록 조회 |
| `get_security_groups` | Security Group 조회 및 보안 분석 |
| `get_cost_summary` | AWS 비용 요약 |

## 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────►│  AWS Agent  │────►│   Claude    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────┴─────┐
                    ▼           ▼
              ┌─────────┐  ┌─────────┐
              │  Boto3  │  │ AWS CLI │
              └────┬────┘  └────┬────┘
                   │            │
                   ▼            ▼
              ┌─────────────────────┐
              │        AWS          │
              │  (EC2, S3, IAM...)  │
              └─────────────────────┘
```
