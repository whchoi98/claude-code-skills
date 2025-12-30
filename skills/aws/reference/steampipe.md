# Steampipe Reference

SQL을 사용하여 AWS 리소스를 조회하고 분석하는 Steampipe 가이드입니다.

## 1. 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Steampipe 아키텍처                                │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐   │
│  │  SQL Query  │────►│  Steampipe  │────►│       AWS Plugin            │   │
│  │             │     │   Engine    │     │  (aws_ec2_instance, ...)    │   │
│  └─────────────┘     └─────────────┘     └──────────────┬──────────────┘   │
│                                                         │                   │
│                                                         ▼                   │
│                                                  ┌─────────────┐            │
│                                                  │   AWS API   │            │
│                                                  └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Steampipe 장점

| 특징 | 설명 |
|------|------|
| **SQL 인터페이스** | 익숙한 SQL로 클라우드 리소스 조회 |
| **읽기 전용** | 실수로 리소스 수정 불가 |
| **JOIN 지원** | 여러 리소스 간 관계 분석 |
| **실시간 데이터** | API 직접 호출, 캐시 없음 |
| **멀티 클라우드** | AWS, GCP, Azure 등 지원 |

---

## 2. 설치 및 설정

### 2.1 Steampipe 설치

```bash
# Linux
sudo /bin/sh -c "$(curl -fsSL https://steampipe.io/install/steampipe.sh)"

# macOS
brew install turbot/tap/steampipe

# 버전 확인
steampipe --version
```

### 2.2 AWS 플러그인 설치

```bash
# AWS 플러그인 설치
steampipe plugin install aws

# 설치된 플러그인 확인
steampipe plugin list
```

### 2.3 AWS 자격 증명 설정

```bash
# 기본 프로파일 사용
aws configure

# 또는 환경 변수
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=ap-northeast-2
```

### 2.4 멀티 리전/멀티 계정 설정

```hcl
# ~/.steampipe/config/aws.spc
connection "aws" {
  plugin  = "aws"
  regions = ["ap-northeast-2", "us-east-1", "eu-west-1"]
}

# 멀티 계정
connection "aws_dev" {
  plugin  = "aws"
  profile = "dev"
  regions = ["ap-northeast-2"]
}

connection "aws_prod" {
  plugin  = "aws"
  profile = "prod"
  regions = ["ap-northeast-2"]
}
```

---

## 3. 기본 사용법

### 3.1 대화형 모드

```bash
steampipe query
```

### 3.2 단일 쿼리 실행

```bash
steampipe query "SELECT * FROM aws_ec2_instance LIMIT 5"
```

### 3.3 출력 형식

```bash
# JSON 출력
steampipe query "SELECT * FROM aws_ec2_instance" --output json

# CSV 출력
steampipe query "SELECT * FROM aws_ec2_instance" --output csv

# 테이블 출력 (기본)
steampipe query "SELECT * FROM aws_ec2_instance" --output table
```

---

## 4. 주요 테이블

### 4.1 Compute

| 테이블 | 설명 |
|--------|------|
| `aws_ec2_instance` | EC2 인스턴스 |
| `aws_ec2_ami` | AMI 이미지 |
| `aws_lambda_function` | Lambda 함수 |
| `aws_ecs_cluster` | ECS 클러스터 |
| `aws_ecs_service` | ECS 서비스 |
| `aws_eks_cluster` | EKS 클러스터 |

### 4.2 Storage

| 테이블 | 설명 |
|--------|------|
| `aws_s3_bucket` | S3 버킷 |
| `aws_ebs_volume` | EBS 볼륨 |
| `aws_ebs_snapshot` | EBS 스냅샷 |
| `aws_efs_file_system` | EFS 파일시스템 |

### 4.3 Network

| 테이블 | 설명 |
|--------|------|
| `aws_vpc` | VPC |
| `aws_vpc_subnet` | 서브넷 |
| `aws_vpc_security_group` | Security Group |
| `aws_vpc_security_group_rule` | SG 규칙 |
| `aws_ec2_network_interface` | ENI |
| `aws_route53_zone` | Route53 호스팅 영역 |

### 4.4 IAM

| 테이블 | 설명 |
|--------|------|
| `aws_iam_user` | IAM 사용자 |
| `aws_iam_role` | IAM 역할 |
| `aws_iam_policy` | IAM 정책 |
| `aws_iam_access_key` | Access Key |

### 4.5 Database

| 테이블 | 설명 |
|--------|------|
| `aws_rds_db_instance` | RDS 인스턴스 |
| `aws_rds_db_cluster` | RDS 클러스터 |
| `aws_dynamodb_table` | DynamoDB 테이블 |
| `aws_elasticache_cluster` | ElastiCache 클러스터 |

---

## 5. 보안 감사 쿼리

### 5.1 IAM 보안

```sql
-- MFA 미활성화 사용자
SELECT
  name,
  user_id,
  password_last_used,
  mfa_enabled
FROM aws_iam_user
WHERE mfa_enabled = false;

-- 90일 이상 미사용 Access Key
SELECT
  user_name,
  access_key_id,
  create_date,
  access_key_last_used_date
FROM aws_iam_access_key
WHERE access_key_last_used_date < NOW() - INTERVAL '90 days'
   OR access_key_last_used_date IS NULL;

-- Admin 권한 사용자
SELECT
  name,
  attached_policy_arns
FROM aws_iam_user
WHERE attached_policy_arns::text LIKE '%AdministratorAccess%';
```

### 5.2 네트워크 보안

```sql
-- 0.0.0.0/0에서 SSH(22) 허용하는 Security Group
SELECT
  group_id,
  group_name,
  vpc_id,
  ip_permission
FROM aws_vpc_security_group_rule
WHERE type = 'ingress'
  AND cidr_ip = '0.0.0.0/0'
  AND from_port = 22;

-- 0.0.0.0/0에서 RDP(3389) 허용하는 Security Group
SELECT
  group_id,
  group_name,
  vpc_id,
  ip_permission
FROM aws_vpc_security_group_rule
WHERE type = 'ingress'
  AND cidr_ip = '0.0.0.0/0'
  AND from_port = 3389;

-- 모든 포트 개방된 Security Group
SELECT
  group_id,
  group_name,
  vpc_id
FROM aws_vpc_security_group_rule
WHERE type = 'ingress'
  AND cidr_ip = '0.0.0.0/0'
  AND from_port = 0
  AND to_port = 65535;
```

### 5.3 S3 보안

```sql
-- 퍼블릭 S3 버킷
SELECT
  name,
  region,
  bucket_policy_is_public,
  block_public_acls,
  block_public_policy
FROM aws_s3_bucket
WHERE bucket_policy_is_public = true
   OR block_public_acls = false;

-- 암호화 미적용 S3 버킷
SELECT
  name,
  region,
  server_side_encryption_configuration
FROM aws_s3_bucket
WHERE server_side_encryption_configuration IS NULL;

-- 버전 관리 미적용 버킷
SELECT
  name,
  region,
  versioning_enabled
FROM aws_s3_bucket
WHERE versioning_enabled = false;
```

### 5.4 EC2 보안

```sql
-- 암호화되지 않은 EBS 볼륨
SELECT
  volume_id,
  size,
  state,
  encrypted
FROM aws_ebs_volume
WHERE encrypted = false;

-- Public IP가 있는 EC2 인스턴스
SELECT
  instance_id,
  tags ->> 'Name' as name,
  public_ip_address,
  instance_state
FROM aws_ec2_instance
WHERE public_ip_address IS NOT NULL;

-- IMDSv1 사용 인스턴스 (보안 취약)
SELECT
  instance_id,
  tags ->> 'Name' as name,
  metadata_options ->> 'HttpTokens' as http_tokens
FROM aws_ec2_instance
WHERE metadata_options ->> 'HttpTokens' = 'optional';
```

---

## 6. 비용 최적화 쿼리

### 6.1 미사용 리소스

```sql
-- 미연결 EBS 볼륨
SELECT
  volume_id,
  size,
  volume_type,
  create_time
FROM aws_ebs_volume
WHERE state = 'available';

-- 미연결 Elastic IP
SELECT
  allocation_id,
  public_ip,
  association_id
FROM aws_vpc_eip
WHERE association_id IS NULL;

-- 오래된 EBS 스냅샷 (90일 이상)
SELECT
  snapshot_id,
  volume_id,
  volume_size,
  start_time
FROM aws_ebs_snapshot
WHERE start_time < NOW() - INTERVAL '90 days';
```

### 6.2 리소스 크기 분석

```sql
-- 인스턴스 타입별 개수
SELECT
  instance_type,
  COUNT(*) as count
FROM aws_ec2_instance
WHERE instance_state = 'running'
GROUP BY instance_type
ORDER BY count DESC;

-- 가장 큰 EBS 볼륨
SELECT
  volume_id,
  size,
  volume_type,
  state
FROM aws_ebs_volume
ORDER BY size DESC
LIMIT 10;

-- RDS 인스턴스 크기 분석
SELECT
  db_instance_identifier,
  db_instance_class,
  allocated_storage,
  multi_az
FROM aws_rds_db_instance
ORDER BY allocated_storage DESC;
```

---

## 7. 인벤토리 쿼리

### 7.1 전체 리소스 현황

```sql
-- EC2 인스턴스 요약
SELECT
  instance_state,
  COUNT(*) as count
FROM aws_ec2_instance
GROUP BY instance_state;

-- VPC 및 서브넷 현황
SELECT
  v.vpc_id,
  v.cidr_block,
  COUNT(s.subnet_id) as subnet_count
FROM aws_vpc v
LEFT JOIN aws_vpc_subnet s ON v.vpc_id = s.vpc_id
GROUP BY v.vpc_id, v.cidr_block;

-- Lambda 함수 런타임별 현황
SELECT
  runtime,
  COUNT(*) as count
FROM aws_lambda_function
GROUP BY runtime
ORDER BY count DESC;
```

### 7.2 태그 분석

```sql
-- Name 태그 없는 EC2 인스턴스
SELECT
  instance_id,
  instance_type,
  instance_state,
  tags
FROM aws_ec2_instance
WHERE tags ->> 'Name' IS NULL;

-- 환경(Environment) 태그별 리소스
SELECT
  tags ->> 'Environment' as environment,
  COUNT(*) as count
FROM aws_ec2_instance
GROUP BY tags ->> 'Environment';
```

---

## 8. 복합 쿼리 (JOIN)

### 8.1 EC2와 Security Group 연결

```sql
SELECT
  i.instance_id,
  i.tags ->> 'Name' as instance_name,
  sg.group_id,
  sg.group_name
FROM aws_ec2_instance i,
     jsonb_array_elements(i.security_groups) as sg_element
JOIN aws_vpc_security_group sg
  ON sg.group_id = sg_element ->> 'GroupId';
```

### 8.2 EBS와 EC2 연결 현황

```sql
SELECT
  v.volume_id,
  v.size,
  v.state,
  i.instance_id,
  i.tags ->> 'Name' as instance_name
FROM aws_ebs_volume v
LEFT JOIN aws_ec2_instance i
  ON v.attachments -> 0 ->> 'InstanceId' = i.instance_id;
```

### 8.3 서브넷과 인스턴스 분포

```sql
SELECT
  s.subnet_id,
  s.availability_zone,
  s.cidr_block,
  COUNT(i.instance_id) as instance_count
FROM aws_vpc_subnet s
LEFT JOIN aws_ec2_instance i ON s.subnet_id = i.subnet_id
GROUP BY s.subnet_id, s.availability_zone, s.cidr_block
ORDER BY instance_count DESC;
```

---

## 9. Compliance Mod (규정 준수)

### 9.1 AWS Compliance Mod 설치

```bash
# CIS AWS Foundations Benchmark
steampipe mod install github.com/turbot/steampipe-mod-aws-compliance

# 실행
cd ~/.steampipe/mods/github.com/turbot/steampipe-mod-aws-compliance
steampipe dashboard
```

### 9.2 주요 Benchmark

| Benchmark | 설명 |
|-----------|------|
| CIS v1.5.0 | CIS AWS Foundations Benchmark |
| AWS Foundational Security | AWS 기본 보안 모범사례 |
| NIST 800-53 | NIST 보안 컨트롤 |
| PCI DSS | 결제 카드 산업 표준 |
| HIPAA | 의료 정보 보호법 |

### 9.3 CLI에서 Benchmark 실행

```bash
# CIS Benchmark 실행
steampipe check benchmark.cis_v150

# 특정 컨트롤만 실행
steampipe check control.cis_v150_1_1
steampipe check control.cis_v150_1_2
```

---

## 10. 자주 사용하는 쿼리 모음

### 10.1 일일 보안 점검

```sql
-- 1. 퍼블릭 노출 리소스
SELECT 'Public EC2' as type, COUNT(*) as count
FROM aws_ec2_instance WHERE public_ip_address IS NOT NULL
UNION ALL
SELECT 'Public S3', COUNT(*)
FROM aws_s3_bucket WHERE bucket_policy_is_public = true
UNION ALL
SELECT 'Open Security Group', COUNT(DISTINCT group_id)
FROM aws_vpc_security_group_rule WHERE cidr_ip = '0.0.0.0/0';
```

### 10.2 비용 점검

```sql
-- 미사용 리소스 요약
SELECT 'Unattached EBS' as type, COUNT(*) as count, SUM(size) as total_gb
FROM aws_ebs_volume WHERE state = 'available'
UNION ALL
SELECT 'Unused EIP', COUNT(*), NULL
FROM aws_vpc_eip WHERE association_id IS NULL;
```

### 10.3 리소스 인벤토리

```sql
-- 리전별 리소스 현황
SELECT
  region,
  'EC2' as resource_type,
  COUNT(*) as count
FROM aws_ec2_instance
GROUP BY region
UNION ALL
SELECT
  region,
  'RDS',
  COUNT(*)
FROM aws_rds_db_instance
GROUP BY region
ORDER BY region, resource_type;
```

---

## 11. 참고 자료

| 문서 | 링크 |
|------|------|
| **Steampipe 공식 문서** | https://steampipe.io/docs |
| **AWS 플러그인 테이블** | https://hub.steampipe.io/plugins/turbot/aws/tables |
| **AWS Compliance Mod** | https://hub.steampipe.io/mods/turbot/aws_compliance |
| **Steampipe Hub** | https://hub.steampipe.io |
