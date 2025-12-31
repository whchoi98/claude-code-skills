# Claude Code Skills

Claude Code CLI를 위한 커스텀 스킬 모음입니다.

## 개요

이 저장소는 Claude Code에서 사용할 수 있는 도메인별 전문 지식과 도구를 정의한 스킬을 관리합니다. 스킬은 MCP(Model Context Protocol) 서버와 통합되어 AWS, Kubernetes 등의 인프라를 직접 관리할 수 있습니다.

## 디렉토리 구조

```
claude-code-skills/
├── skills/
│   └── aws/                          # AWS 관리 스킬
│       ├── SKILL.md                  # 메인 스킬 정의
│       └── reference/                # 참조 문서
│           ├── best-practices.md     # AWS Well-Architected Framework
│           ├── iac-cdk-terraform.md  # CDK, Terraform, MCP 통합
│           ├── eks-kubernetes.md     # EKS 클러스터 및 모범사례
│           ├── networking-vpc.md     # VPC 설계 및 네트워킹
│           ├── security-iam.md       # IAM, SCP, 보안 서비스
│           ├── serverless.md         # Lambda, API Gateway, Step Functions
│           └── steampipe.md          # SQL로 AWS 조회, 보안 감사
├── scripts/
│   └── sync-skills.sh                # 스킬 배포 스크립트
└── README.md
```

## 스킬 목록

| 스킬 | 설명 | 참조 문서 |
|------|------|-----------|
| [aws](skills/aws/SKILL.md) | AWS 인프라 관리 (MCP, CLI, Steampipe) | 7개 |

### AWS 스킬

AWS 리소스를 MCP 서버와 CLI를 활용하여 관리하는 스킬입니다.

**주요 기능:**
- 23개 AWS MCP 서버 지원 (EC2, S3, Lambda, EKS, CDK, Terraform 등)
- AWS Well-Architected Framework 기반 모범사례
- EKS/Kubernetes 클러스터 관리 및 보안
- IaC (CDK, Terraform, CloudFormation) 통합
- Steampipe SQL 쿼리로 리소스 조회 및 보안 감사

**참조 문서:**
| 문서 | 내용 |
|------|------|
| `best-practices.md` | 보안, 안정성, 성능, 비용 최적화, 운영 우수성 |
| `iac-cdk-terraform.md` | CDK, Terraform, CloudFormation, MCP 워크플로우 |
| `eks-kubernetes.md` | EKS 클러스터, kubectl, Helm, IRSA, 모범사례 |
| `networking-vpc.md` | VPC 설계, 서브넷, Security Group, VPC Endpoint |
| `security-iam.md` | IAM 정책, SCP, 권한 경계, 보안 서비스 |
| `serverless.md` | Lambda, API Gateway, Step Functions, EventBridge |
| `steampipe.md` | SQL로 AWS 조회, 보안 감사, 비용 분석, 규정 준수 |

## 설치

### 전체 스킬 동기화

```bash
./scripts/sync-skills.sh
```

### 특정 스킬 동기화

```bash
./scripts/sync-skills.sh aws
```

### 수동 복사

```bash
# 전체 스킬 디렉토리 복사
cp -r skills/aws ~/.claude/skills/
```

### 배포 구조

```
~/.claude/skills/
└── aws/
    ├── SKILL.md           # 메인 스킬 (frontmatter 포함)
    └── reference/         # 참조 문서
        ├── best-practices.md
        ├── eks-kubernetes.md
        └── ...
```

## 새 스킬 만들기

1. 스킬 디렉토리 생성:
   ```bash
   mkdir -p skills/<skill-name>/reference
   ```

2. `SKILL.md` 파일 작성 (frontmatter 필수):
   ```markdown
   ---
   name: <skill-name>
   description: 스킬 설명 (자동 활성화 키워드 포함)
   ---

   # 스킬 제목
   ...
   ```

3. (선택) `reference/` 디렉토리에 상세 문서 추가

4. Claude Code에 배포:
   ```bash
   ./scripts/sync-skills.sh <skill-name>
   ```

## 스킬 작성 가이드라인

### SKILL.md (메인 파일)
- **Frontmatter 필수**: `name`, `description` 정의
- **500줄 이하** 유지 권장 (토큰 효율성)
- 스킬 활성화 시 항상 로드됨
- 핵심 지침, MCP 설정, 기본 명령어 포함

### Frontmatter 예시
```yaml
---
name: aws
description: AWS 리소스를 MCP와 CLI로 관리. EC2, S3, Lambda, EKS, CloudFormation 등 AWS 인프라 작업 시 자동 활성화
---
```

### reference/ (참조 문서)
- 필요할 때만 Read 도구로 로드 (토큰 절약)
- `~/.claude/skills/<skill>/reference/` 경로로 참조
- 상세한 가이드, 모범사례, 예제 코드 포함

### 참조 문서 경로 규칙
```markdown
<!-- 올바른 방법 (~/.claude/skills/ 기준) -->
`~/.claude/skills/aws/reference/best-practices.md`
```

> **참고**: `sync-skills.sh`는 SKILL.md와 reference/ 디렉토리를 함께 복사합니다.

## MCP 서버 설정

AWS 스킬에서 사용하는 MCP 서버는 `~/.claude/settings.json`에 설정합니다:

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
    }
  }
}
```

자세한 MCP 서버 목록은 [AWS SKILL.md](skills/aws/SKILL.md)를 참조하세요.

## License

MIT
