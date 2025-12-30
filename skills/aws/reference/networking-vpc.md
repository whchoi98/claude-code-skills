# Networking & VPC Reference

AWS 네트워킹 및 VPC 설계/운영 가이드입니다.

## MCP 서버 활용

VPC 관련 작업은 `aws-core` MCP 서버를 사용합니다.

```bash
# CLI 대체 명령어
aws ec2 describe-vpcs
aws ec2 describe-subnets
aws ec2 describe-security-groups
aws ec2 describe-route-tables
```

---

## 1. VPC 아키텍처 패턴

### 1.1 기본 3-Tier 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VPC (10.0.0.0/16)                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Public Subnet (10.0.1.0/24)          Public Subnet (10.0.2.0/24)   │   │
│  │  ┌─────────────┐                      ┌─────────────┐               │   │
│  │  │     ALB     │                      │ NAT Gateway │               │   │
│  │  └─────────────┘                      └─────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                    │                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Private Subnet (10.0.11.0/24)        Private Subnet (10.0.12.0/24) │   │
│  │  ┌─────────────┐                      ┌─────────────┐               │   │
│  │  │   App EC2   │                      │   App EC2   │               │   │
│  │  └─────────────┘                      └─────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                    │                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Private Subnet (10.0.21.0/24)        Private Subnet (10.0.22.0/24) │   │
│  │  ┌─────────────┐                      ┌─────────────┐               │   │
│  │  │     RDS     │◄────────────────────►│   RDS(SB)   │               │   │
│  │  └─────────────┘                      └─────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 CIDR 설계 권장사항

| 환경 | VPC CIDR | 서브넷 크기 |
|------|----------|------------|
| 소규모 | /24 (256 IPs) | /26 (64 IPs) |
| 중규모 | /20 (4,096 IPs) | /24 (256 IPs) |
| 대규모 | /16 (65,536 IPs) | /20 (4,096 IPs) |

#### 서브넷 할당 예시 (10.0.0.0/16)

| 용도 | AZ-a | AZ-b | AZ-c |
|------|------|------|------|
| Public | 10.0.1.0/24 | 10.0.2.0/24 | 10.0.3.0/24 |
| Private (App) | 10.0.11.0/24 | 10.0.12.0/24 | 10.0.13.0/24 |
| Private (DB) | 10.0.21.0/24 | 10.0.22.0/24 | 10.0.23.0/24 |
| Reserved | 10.0.100.0/24+ | | |

---

## 2. 핵심 컴포넌트

### 2.1 Internet Gateway (IGW)

```bash
# IGW 생성
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=my-igw}]'

# VPC에 연결
aws ec2 attach-internet-gateway --internet-gateway-id igw-xxx --vpc-id vpc-xxx
```

### 2.2 NAT Gateway

| 타입 | 용도 | 비용 |
|------|------|------|
| NAT Gateway | 프로덕션 권장, 관리형 | ~$32/월 + 데이터 |
| NAT Instance | 개발/테스트, 직접 관리 | EC2 비용만 |

```bash
# Elastic IP 할당
aws ec2 allocate-address --domain vpc

# NAT Gateway 생성
aws ec2 create-nat-gateway \
  --subnet-id subnet-xxx \
  --allocation-id eipalloc-xxx \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=my-nat}]'
```

### 2.3 Route Table

```bash
# 퍼블릭 서브넷 라우트 (IGW)
aws ec2 create-route --route-table-id rtb-xxx --destination-cidr-block 0.0.0.0/0 --gateway-id igw-xxx

# 프라이빗 서브넷 라우트 (NAT)
aws ec2 create-route --route-table-id rtb-xxx --destination-cidr-block 0.0.0.0/0 --nat-gateway-id nat-xxx
```

---

## 3. Security Group vs NACL

### 3.1 비교

| 항목 | Security Group | NACL |
|------|---------------|------|
| 레벨 | 인스턴스 (ENI) | 서브넷 |
| 상태 | Stateful | Stateless |
| 규칙 | 허용만 | 허용/거부 |
| 평가 순서 | 모든 규칙 평가 | 번호 순서대로 |
| 기본 동작 | 모두 거부 | 모두 허용 |

### 3.2 Security Group 모범사례

```bash
# 웹 서버 SG
aws ec2 create-security-group \
  --group-name web-sg \
  --description "Web server SG" \
  --vpc-id vpc-xxx

# HTTP/HTTPS 허용 (ALB에서만)
aws ec2 authorize-security-group-ingress \
  --group-id sg-web \
  --protocol tcp \
  --port 80 \
  --source-group sg-alb

# DB SG - 앱 서버에서만 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-db \
  --protocol tcp \
  --port 3306 \
  --source-group sg-app
```

#### Security Group 참조 패턴

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ALB SG    │────►│   App SG    │────►│    DB SG    │
│ 80/443 허용  │     │ ALB SG 참조 │     │ App SG 참조 │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 3.3 NACL 설정 예시

```bash
# 인바운드 규칙 (허용)
aws ec2 create-network-acl-entry \
  --network-acl-id acl-xxx \
  --ingress \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=443,To=443 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow

# 아웃바운드 임시 포트 허용 (Stateless이므로 필요)
aws ec2 create-network-acl-entry \
  --network-acl-id acl-xxx \
  --egress \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow
```

---

## 4. VPC Endpoint

### 4.1 엔드포인트 타입

| 타입 | 대상 | 비용 |
|------|------|------|
| **Gateway** | S3, DynamoDB | 무료 |
| **Interface** | 대부분의 AWS 서비스 | ~$7/월/AZ + 데이터 |
| **Gateway LB** | 서드파티 어플라이언스 | 사용량 기반 |

### 4.2 Gateway Endpoint (S3)

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.ap-northeast-2.s3 \
  --route-table-ids rtb-xxx rtb-yyy
```

### 4.3 Interface Endpoint (SSM)

```bash
# SSM 접속을 위한 필수 엔드포인트
for service in ssm ssmmessages ec2messages; do
  aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxx \
    --service-name com.amazonaws.ap-northeast-2.$service \
    --vpc-endpoint-type Interface \
    --subnet-ids subnet-xxx subnet-yyy \
    --security-group-ids sg-xxx \
    --private-dns-enabled
done
```

### 4.4 권장 VPC Endpoint

| 서비스 | 용도 | 우선순위 |
|--------|------|----------|
| S3 (Gateway) | 로그, 아티팩트 저장 | 필수 |
| SSM, SSMMessages, EC2Messages | Session Manager | 필수 |
| ECR (dkr, api) | 컨테이너 이미지 | 권장 |
| CloudWatch Logs | 로그 전송 | 권장 |
| STS | 임시 자격 증명 | 권장 |
| Secrets Manager | 시크릿 조회 | 선택 |

---

## 5. VPC Peering & Transit Gateway

### 5.1 VPC Peering

```
     ┌─────────────┐         ┌─────────────┐
     │   VPC A     │◄───────►│   VPC B     │
     │ 10.0.0.0/16 │ Peering │ 10.1.0.0/16 │
     └─────────────┘         └─────────────┘
```

```bash
# Peering 연결 생성
aws ec2 create-vpc-peering-connection \
  --vpc-id vpc-aaa \
  --peer-vpc-id vpc-bbb

# 수락
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id pcx-xxx

# 양쪽 라우트 테이블에 라우트 추가
aws ec2 create-route --route-table-id rtb-aaa --destination-cidr-block 10.1.0.0/16 --vpc-peering-connection-id pcx-xxx
aws ec2 create-route --route-table-id rtb-bbb --destination-cidr-block 10.0.0.0/16 --vpc-peering-connection-id pcx-xxx
```

### 5.2 Transit Gateway

```
                    ┌─────────────────┐
                    │ Transit Gateway │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │   VPC A     │   │   VPC B     │   │   VPC C     │
    │ 10.0.0.0/16 │   │ 10.1.0.0/16 │   │ 10.2.0.0/16 │
    └─────────────┘   └─────────────┘   └─────────────┘
```

**사용 시점:**
- VPC 3개 이상 연결
- 중앙 집중식 라우팅 필요
- 온프레미스 연결 (VPN/Direct Connect)

---

## 6. 하이브리드 연결

### 6.1 Site-to-Site VPN

```
┌─────────────────┐                        ┌─────────────────┐
│   온프레미스     │◄─────── VPN ─────────►│      AWS        │
│  (Customer GW)  │    IPsec 터널 x2       │  (Virtual GW)   │
└─────────────────┘                        └─────────────────┘
```

```bash
# Customer Gateway 생성
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65000

# Virtual Private Gateway 생성
aws ec2 create-vpn-gateway --type ipsec.1

# VPC에 연결
aws ec2 attach-vpn-gateway --vpn-gateway-id vgw-xxx --vpc-id vpc-xxx

# VPN 연결 생성
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxx \
  --vpn-gateway-id vgw-xxx
```

### 6.2 Direct Connect

| 연결 타입 | 대역폭 | 용도 |
|----------|--------|------|
| Dedicated | 1/10/100 Gbps | 대용량, 일관된 성능 |
| Hosted | 50Mbps ~ 10Gbps | 유연한 대역폭 |

---

## 7. VPC Flow Logs

### 7.1 활성화

```bash
# CloudWatch Logs로 전송
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::xxx:role/flow-logs-role

# S3로 전송 (비용 효율적)
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxx \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket
```

### 7.2 로그 분석

```
# Flow Log 형식
version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status

# 예시: 거부된 트래픽
2 123456789012 eni-xxx 10.0.1.5 10.0.2.10 49152 3306 6 1 40 1620000000 1620000060 REJECT OK
```

---

## 8. 모범사례 체크리스트

### 설계 시

- [ ] CIDR 겹침 방지 (향후 피어링/TGW 고려)
- [ ] Multi-AZ 서브넷 배치
- [ ] 퍼블릭/프라이빗 서브넷 분리
- [ ] 서브넷 크기 여유 확보

### 보안

- [ ] Security Group: 최소 권한, SG 참조 사용
- [ ] NACL: 서브넷 레벨 추가 방어
- [ ] VPC Flow Logs 활성화
- [ ] 0.0.0.0/0 인바운드 최소화

### 비용 최적화

- [ ] NAT Gateway: 단일 vs Multi-AZ 검토
- [ ] VPC Endpoint: 트래픽 많은 서비스 우선
- [ ] S3 Gateway Endpoint 사용 (무료)

### 연결성

- [ ] VPC Endpoint로 AWS 서비스 접근
- [ ] DNS 해석 활성화
- [ ] 프라이빗 DNS 사용
