# AWS Best Practices Reference

AWS Well-Architected Framework 기반 모범사례 가이드입니다.

## 1. 보안 (Security)

### IAM 모범사례

| 원칙 | 설명 |
|------|------|
| **최소 권한 원칙** | 필요한 최소한의 권한만 부여 |
| **MFA 활성화** | 모든 IAM 사용자에 MFA 필수 |
| **루트 계정 미사용** | 일상 작업에 루트 계정 사용 금지 |
| **역할 기반 접근** | 사용자 대신 IAM 역할 사용 권장 |
| **정기적 자격증명 교체** | Access Key 90일마다 교체 |
| **미사용 자격증명 제거** | 90일 이상 미사용 자격증명 삭제 |

```bash
# MFA 미활성화 사용자 확인
aws iam list-users --query 'Users[?MFADevices==`[]`].UserName'

# 미사용 Access Key 확인 (90일 이상)
aws iam list-access-keys --user-name <user>
aws iam get-access-key-last-used --access-key-id <key-id>
```

### 네트워크 보안

| 원칙 | 설명 |
|------|------|
| **VPC 사용** | 모든 리소스를 VPC 내에 배치 |
| **프라이빗 서브넷** | DB, 애플리케이션 서버는 프라이빗 서브넷에 |
| **Security Group** | 필요한 포트만 최소 IP 범위로 허용 |
| **NACL** | 서브넷 레벨 추가 방어층 |
| **VPC Flow Logs** | 네트워크 트래픽 모니터링 활성화 |
| **PrivateLink/VPC Endpoint** | AWS 서비스 접근 시 프라이빗 연결 사용 |

```bash
# 0.0.0.0/0 허용된 Security Group 확인
aws ec2 describe-security-groups \
  --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]].[GroupId,GroupName]'
```

### 데이터 보호

| 원칙 | 설명 |
|------|------|
| **저장 데이터 암호화** | S3, EBS, RDS 등 모든 저장소 암호화 |
| **전송 데이터 암호화** | TLS/SSL 사용, HTTPS 강제 |
| **KMS 키 관리** | CMK 사용, 키 교체 활성화 |
| **S3 버킷 정책** | 퍼블릭 액세스 차단 기본 활성화 |

```bash
# 암호화되지 않은 S3 버킷 확인
aws s3api list-buckets --query 'Buckets[].Name' --output text | \
  xargs -I {} aws s3api get-bucket-encryption --bucket {} 2>/dev/null || echo "Not encrypted: {}"

# 암호화되지 않은 EBS 볼륨 확인
aws ec2 describe-volumes --query 'Volumes[?Encrypted==`false`].[VolumeId,State]'
```

## 2. 안정성 (Reliability)

### 고가용성 설계

| 원칙 | 설명 |
|------|------|
| **Multi-AZ 배포** | 최소 2개 AZ에 리소스 분산 |
| **Auto Scaling** | 부하에 따른 자동 확장/축소 |
| **로드 밸런서** | ALB/NLB로 트래픽 분산 |
| **헬스 체크** | 주기적인 상태 확인 구성 |
| **장애 격리** | 서비스별 독립적인 장애 도메인 |

```bash
# 단일 AZ에만 있는 RDS 인스턴스 확인
aws rds describe-db-instances \
  --query 'DBInstances[?MultiAZ==`false`].[DBInstanceIdentifier,AvailabilityZone]'
```

### 백업 및 복구

| 원칙 | 설명 |
|------|------|
| **자동 백업 활성화** | RDS, DynamoDB 자동 백업 |
| **크로스 리전 복제** | 재해 복구를 위한 리전 간 복제 |
| **복구 테스트** | 정기적인 복구 절차 테스트 |
| **RPO/RTO 정의** | 비즈니스 요구사항에 맞는 목표 설정 |

```bash
# 백업 미활성화 RDS 확인
aws rds describe-db-instances \
  --query 'DBInstances[?BackupRetentionPeriod==`0`].DBInstanceIdentifier'
```

## 3. 성능 효율성 (Performance Efficiency)

### 컴퓨팅 최적화

| 원칙 | 설명 |
|------|------|
| **적절한 인스턴스 타입** | 워크로드에 맞는 인스턴스 패밀리 선택 |
| **최신 세대 사용** | 비용 대비 성능이 좋은 최신 세대 |
| **Graviton 고려** | ARM 기반 Graviton으로 비용/성능 개선 |
| **스팟 인스턴스** | 내결함성 워크로드에 스팟 활용 |

| 인스턴스 패밀리 | 용도 |
|----------------|------|
| `t3/t4g` | 범용, 버스트 가능 |
| `m6i/m7g` | 범용, 균형 잡힌 성능 |
| `c6i/c7g` | 컴퓨팅 집약적 |
| `r6i/r7g` | 메모리 집약적 |
| `i3/i4i` | 스토리지 집약적 |

### 스토리지 최적화

| 스토리지 타입 | 용도 | IOPS |
|--------------|------|------|
| `gp3` | 범용 SSD (권장) | 3,000-16,000 |
| `io2` | 고성능 SSD | 최대 256,000 |
| `st1` | 처리량 최적화 HDD | - |
| `sc1` | 콜드 HDD | - |

### 캐싱 전략

| 계층 | 서비스 | 용도 |
|------|--------|------|
| CDN | CloudFront | 정적 콘텐츠, API 응답 |
| 애플리케이션 | ElastiCache | 세션, 쿼리 결과 |
| 데이터베이스 | DAX | DynamoDB 가속 |

## 4. 비용 최적화 (Cost Optimization)

### 비용 절감 전략

| 전략 | 절감율 | 적용 대상 |
|------|--------|----------|
| **Reserved Instances** | 최대 72% | 예측 가능한 워크로드 |
| **Savings Plans** | 최대 72% | 유연한 컴퓨팅 사용 |
| **Spot Instances** | 최대 90% | 내결함성 워크로드 |
| **Graviton** | 최대 40% | ARM 호환 워크로드 |

### 미사용 리소스 정리

```bash
# 미사용 EBS 볼륨 (available 상태)
aws ec2 describe-volumes --query 'Volumes[?State==`available`].[VolumeId,Size,CreateTime]'

# 미사용 Elastic IP
aws ec2 describe-addresses --query 'Addresses[?InstanceId==null].PublicIp'

# 미사용 ELB (Healthy 호스트 0)
aws elbv2 describe-target-health --target-group-arn <arn>

# 중지된 EC2 (30일 이상)
aws ec2 describe-instances --query 'Reservations[].Instances[?State.Name==`stopped`].[InstanceId,LaunchTime]'
```

### 태깅 전략

| 태그 키 | 용도 | 예시 |
|--------|------|------|
| `Environment` | 환경 구분 | prod, staging, dev |
| `Project` | 프로젝트별 비용 추적 | project-alpha |
| `Owner` | 담당자/팀 | team-backend |
| `CostCenter` | 비용 센터 | cc-12345 |

```bash
# 태그 없는 EC2 인스턴스
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?Tags==null || length(Tags)==`0`].InstanceId'
```

## 5. 운영 우수성 (Operational Excellence)

### 인프라 코드화 (IaC)

| 도구 | 용도 |
|------|------|
| **CloudFormation** | AWS 네이티브 IaC |
| **CDK** | 프로그래밍 언어로 인프라 정의 |
| **Terraform** | 멀티 클라우드 IaC |

### 모니터링 및 알림

| 서비스 | 용도 |
|--------|------|
| **CloudWatch Metrics** | 리소스 메트릭 수집 |
| **CloudWatch Alarms** | 임계값 기반 알림 |
| **CloudWatch Logs** | 로그 중앙화 |
| **CloudTrail** | API 호출 감사 |
| **X-Ray** | 분산 추적 |

### 필수 알림 설정

| 알림 | 임계값 |
|------|--------|
| CPU 사용률 | > 80% |
| 메모리 사용률 | > 85% |
| 디스크 사용률 | > 80% |
| 에러율 | > 1% |
| 응답 시간 | > 2초 |

## 6. 서비스별 모범사례

### EC2

- [x] IMDSv2 필수 사용
- [x] 퍼블릭 IP 자동 할당 비활성화
- [x] EBS 암호화 기본 활성화
- [x] Systems Manager로 관리
- [x] 태그 필수 적용

### S3

- [x] 퍼블릭 액세스 차단
- [x] 버전 관리 활성화
- [x] 서버 측 암호화 (SSE-S3 또는 SSE-KMS)
- [x] 수명 주기 정책 설정
- [x] 액세스 로깅 활성화

### RDS

- [x] Multi-AZ 배포
- [x] 자동 백업 활성화 (7일 이상)
- [x] 암호화 활성화
- [x] Enhanced Monitoring
- [x] Performance Insights

### Lambda

- [x] 적절한 메모리 크기 설정
- [x] 제한 시간 설정
- [x] VPC 내 배치 (필요시)
- [x] 환경 변수 암호화
- [x] Dead Letter Queue 설정

### EKS

- [x] 프라이빗 엔드포인트 사용
- [x] 관리형 노드 그룹 사용
- [x] Pod Security Standards
- [x] AWS Load Balancer Controller
- [x] 클러스터 로깅 활성화

## 7. 보안 체크리스트

### 계정 수준

- [ ] AWS Organizations 사용
- [ ] SCPs로 가드레일 설정
- [ ] CloudTrail 전체 리전 활성화
- [ ] Config Rules 활성화
- [ ] GuardDuty 활성화
- [ ] Security Hub 활성화

### 네트워크 수준

- [ ] VPC Flow Logs 활성화
- [ ] WAF 적용 (웹 애플리케이션)
- [ ] Shield Advanced (DDoS 보호)
- [ ] Network Firewall (필요시)

### 데이터 수준

- [ ] 모든 저장소 암호화
- [ ] KMS 키 교체 활성화
- [ ] Secrets Manager 사용
- [ ] Macie로 민감 데이터 탐지

## 참고 링크

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Security Best Practices](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/)
- [AWS Cost Optimization](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/)
