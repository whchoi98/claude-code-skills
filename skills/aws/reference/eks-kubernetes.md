# EKS & Kubernetes Reference

Amazon EKS 클러스터 관리 및 Kubernetes 운영 가이드입니다.

## MCP 서버 설정

```json
{
  "mcpServers": {
    "aws-eks": {
      "command": "uvx",
      "args": [
        "awslabs.eks-mcp-server@latest",
        "--allow-write",
        "--allow-sensitive-data-access"
      ],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### MCP 도구

| 도구 | 설명 |
|------|------|
| `eks_list_clusters` | EKS 클러스터 목록 |
| `eks_describe_cluster` | 클러스터 상세 정보 |
| `eks_list_nodegroups` | 노드그룹 목록 |
| `eks_describe_nodegroup` | 노드그룹 상세 정보 |
| `eks_list_addons` | 애드온 목록 |
| `eks_kubectl` | kubectl 명령 실행 |

---

## 1. EKS 클러스터 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EKS Control Plane                              │
│                        (AWS 관리형, Multi-AZ 자동 배포)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ API Server  │  │   etcd      │  │ Controller  │  │  Scheduler  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   ENI (Elastic NI)    │
                    └───────────┬───────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────────────────┐
│                              Data Plane (VPC)                               │
│  ┌─────────────────────────┐      ┌─────────────────────────┐              │
│  │     Node Group (AZ-a)   │      │     Node Group (AZ-b)   │              │
│  │  ┌─────┐  ┌─────┐      │      │  ┌─────┐  ┌─────┐      │              │
│  │  │ Pod │  │ Pod │      │      │  │ Pod │  │ Pod │      │              │
│  │  └─────┘  └─────┘      │      │  └─────┘  └─────┘      │              │
│  │  ┌─────────────────┐   │      │  ┌─────────────────┐   │              │
│  │  │  EC2 Instance   │   │      │  │  EC2 Instance   │   │              │
│  │  └─────────────────┘   │      │  └─────────────────┘   │              │
│  └─────────────────────────┘      └─────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 클러스터 생성 및 관리

### 2.1 eksctl로 클러스터 생성

```yaml
# cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: my-cluster
  region: ap-northeast-2
  version: "1.29"

vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: Single  # HighlyAvailable for prod

managedNodeGroups:
  - name: managed-ng
    instanceType: m6i.large
    desiredCapacity: 2
    minSize: 1
    maxSize: 4
    volumeSize: 100
    volumeType: gp3
    privateNetworking: true
    iam:
      withAddonPolicies:
        albIngress: true
        cloudWatch: true

addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest

cloudWatch:
  clusterLogging:
    enableTypes: ["api", "audit", "authenticator", "controllerManager", "scheduler"]
```

```bash
# 클러스터 생성
eksctl create cluster -f cluster-config.yaml

# kubeconfig 업데이트
aws eks update-kubeconfig --name my-cluster --region ap-northeast-2
```

### 2.2 AWS CLI로 관리

```bash
# 클러스터 목록
aws eks list-clusters --region ap-northeast-2

# 클러스터 정보
aws eks describe-cluster --name my-cluster --region ap-northeast-2

# 노드그룹 목록
aws eks list-nodegroups --cluster-name my-cluster --region ap-northeast-2

# 애드온 목록
aws eks list-addons --cluster-name my-cluster --region ap-northeast-2
```

---

## 3. kubectl 기본 명령어

### 3.1 리소스 조회

```bash
# 노드 상태
kubectl get nodes -o wide

# 모든 네임스페이스의 Pod
kubectl get pods -A

# 서비스 목록
kubectl get svc -A

# 디플로이먼트
kubectl get deployments -A

# 전체 리소스 요약
kubectl get all -A
```

### 3.2 리소스 상세 정보

```bash
# Pod 상세
kubectl describe pod <pod-name> -n <namespace>

# 이벤트 조회
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# 로그 조회
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous  # 이전 컨테이너
kubectl logs <pod-name> -n <namespace> -f          # 실시간

# 리소스 사용량
kubectl top nodes
kubectl top pods -A
```

### 3.3 디버깅

```bash
# Pod 내부 접속
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# 임시 디버그 Pod
kubectl run debug --rm -it --image=busybox -- /bin/sh

# DNS 테스트
kubectl run dns-test --rm -it --image=busybox -- nslookup kubernetes.default
```

---

## 4. 핵심 Kubernetes 리소스

### 4.1 Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-repo/my-app:v1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4.2 Service

```yaml
# ClusterIP (내부용)
apiVersion: v1
kind: Service
metadata:
  name: my-app-svc
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP

---
# LoadBalancer (NLB)
apiVersion: v1
kind: Service
metadata:
  name: my-app-nlb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### 4.3 Ingress (ALB)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  rules:
  - host: my-app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app-svc
            port:
              number: 80
```

### 4.4 ConfigMap & Secret

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-app-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"

---
# Secret (base64 인코딩)
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secret
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQxMjM=  # echo -n 'password123' | base64
```

---

## 5. EKS 애드온

### 5.1 필수 애드온

| 애드온 | 설명 | 필수 여부 |
|--------|------|----------|
| **vpc-cni** | AWS VPC CNI 플러그인 | 필수 |
| **coredns** | 클러스터 DNS | 필수 |
| **kube-proxy** | 네트워크 프록시 | 필수 |
| **aws-ebs-csi-driver** | EBS 볼륨 지원 | 권장 |
| **aws-efs-csi-driver** | EFS 볼륨 지원 | 선택 |

### 5.2 AWS Load Balancer Controller

```bash
# Helm으로 설치
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 5.3 Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 확인
kubectl top nodes
kubectl top pods -A
```

---

## 6. 보안 모범사례

### 6.1 Pod Security Standards

```yaml
# Namespace에 PSS 적용
apiVersion: v1
kind: Namespace
metadata:
  name: my-namespace
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 6.2 RBAC 설정

```yaml
# ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default

---
# Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]

---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-rolebinding
  namespace: default
subjects:
- kind: ServiceAccount
  name: my-app-sa
  namespace: default
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```

### 6.3 IRSA (IAM Roles for Service Accounts)

```bash
# OIDC Provider 연결
eksctl utils associate-iam-oidc-provider --cluster my-cluster --approve

# Service Account에 IAM 역할 연결
eksctl create iamserviceaccount \
  --name my-app-sa \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve
```

### 6.4 Network Policy

```yaml
# 기본 거부 정책
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress

---
# 특정 트래픽만 허용
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-my-app
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

---

## 7. 모니터링 및 로깅

### 7.1 CloudWatch Container Insights

```bash
# Container Insights 활성화
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# FluentBit 설치 (로그 수집)
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml
```

### 7.2 Prometheus & Grafana

```bash
# Prometheus 스택 설치
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace
```

---

## 8. AWS EKS 모범사례

> 참고: [AWS EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)

### 8.1 클러스터 설계

#### Control Plane

| 항목 | 모범사례 |
|------|----------|
| **Kubernetes 버전** | 최신 버전 또는 n-1 버전 유지 |
| **엔드포인트 접근** | 프라이빗 엔드포인트 사용 권장 |
| **로깅** | 모든 컨트롤 플레인 로그 활성화 |
| **Secrets 암호화** | KMS CMK로 envelope 암호화 |

```bash
# Secrets 암호화 활성화
aws eks create-cluster \
  --name my-cluster \
  --encryption-config '[{"resources":["secrets"],"provider":{"keyArn":"arn:aws:kms:xxx"}}]'
```

#### Data Plane

| 항목 | 모범사례 |
|------|----------|
| **노드 배치** | 프라이빗 서브넷에 배치 |
| **노드그룹 유형** | 관리형 노드그룹 사용 |
| **인스턴스 타입** | 워크로드에 맞는 적절한 크기 선택 |
| **AMI** | EKS 최적화 AMI 또는 Bottlerocket 사용 |
| **노드 자동 확장** | Karpenter 또는 Cluster Autoscaler 사용 |

### 8.2 보안 모범사례

#### 인증 및 권한

| 항목 | 모범사례 | 위험도 |
|------|----------|--------|
| **IRSA 사용** | Pod에 직접 IAM 자격 증명 제공 | 🔴 필수 |
| **RBAC 최소 권한** | 필요한 최소한의 권한만 부여 | 🔴 필수 |
| **aws-auth ConfigMap** | 주기적으로 검토 및 감사 | 🔴 필수 |
| **cluster-admin 제한** | 관리자 권한 최소화 | 🟡 권장 |

```yaml
# aws-auth ConfigMap 예시
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::xxx:role/NodeRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::xxx:role/AdminRole
      username: admin
      groups:
        - system:masters
  mapUsers: |
    - userarn: arn:aws:iam::xxx:user/developer
      username: developer
      groups:
        - developers
```

#### Pod 보안

| 항목 | 모범사례 |
|------|----------|
| **Pod Security Standards** | `restricted` 또는 `baseline` 적용 |
| **securityContext** | 비루트 사용자, readOnlyRootFilesystem |
| **리소스 제한** | requests/limits 필수 설정 |
| **이미지 스캔** | ECR 이미지 스캔 활성화 |

```yaml
# 보안 강화된 Pod 예시
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: my-app:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
```

#### 네트워크 보안

| 항목 | 모범사례 |
|------|----------|
| **Network Policy** | 기본 거부 후 필요한 트래픽만 허용 |
| **서비스 메시** | mTLS (App Mesh, Istio) |
| **인그레스 보안** | WAF, Shield 적용 |
| **Pod 통신** | VPC CNI 보안 그룹 for Pods |

```bash
# Security Groups for Pods 활성화
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointPublicAccess=false,endpointPrivateAccess=true
```

### 8.3 안정성 모범사례

#### 고가용성

| 항목 | 모범사례 |
|------|----------|
| **Multi-AZ** | 최소 3개 AZ에 노드 분산 |
| **Pod Anti-Affinity** | 동일 앱 Pod를 다른 노드에 분산 |
| **PodDisruptionBudget** | 최소 가용 Pod 수 보장 |
| **토폴로지 분산** | topology spread constraints 사용 |

```yaml
# PodDisruptionBudget
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 2  # 또는 maxUnavailable: 1
  selector:
    matchLabels:
      app: my-app

---
# Pod Anti-Affinity
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: my-app
              topologyKey: kubernetes.io/hostname
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: my-app
```

#### 복원력

| 항목 | 모범사례 |
|------|----------|
| **헬스 체크** | liveness/readiness probe 필수 |
| **Graceful Shutdown** | preStop hook, terminationGracePeriodSeconds |
| **재시도** | 애플리케이션 레벨 재시도 로직 |
| **Circuit Breaker** | 서비스 메시 또는 앱 레벨 구현 |

```yaml
# Graceful Shutdown 설정
spec:
  terminationGracePeriodSeconds: 60
  containers:
  - name: app
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 10"]
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 3
```

### 8.4 성능 모범사례

#### 리소스 관리

| 항목 | 모범사례 |
|------|----------|
| **리소스 요청/제한** | 모든 컨테이너에 설정 |
| **HPA** | CPU/메모리 기반 자동 스케일링 |
| **VPA** | 리소스 권장값 자동 조정 |
| **LimitRange** | 네임스페이스 기본값 설정 |

```yaml
# HPA 설정
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
```

#### VPC CNI 최적화

| 설정 | 용도 |
|------|------|
| **WARM_ENI_TARGET** | 예비 ENI 수 |
| **WARM_IP_TARGET** | 예비 IP 수 |
| **MINIMUM_IP_TARGET** | 최소 유지 IP |
| **PREFIX_DELEGATION** | IP 용량 확장 |

```bash
# VPC CNI 환경 변수 설정
kubectl set env daemonset aws-node -n kube-system \
  WARM_IP_TARGET=5 \
  MINIMUM_IP_TARGET=2
```

### 8.5 비용 최적화

| 전략 | 설명 | 절감율 |
|------|------|--------|
| **Spot Instances** | 내결함성 워크로드에 사용 | 최대 90% |
| **Graviton** | ARM 기반 노드 사용 | 최대 40% |
| **Karpenter** | 효율적인 노드 프로비저닝 | 가변 |
| **리소스 적정화** | VPA 권장값 기반 조정 | 가변 |
| **유휴 리소스 정리** | 미사용 네임스페이스/리소스 삭제 | 가변 |

```yaml
# Karpenter NodePool (Spot + Graviton)
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64", "arm64"]
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["spot", "on-demand"]
      - key: karpenter.k8s.aws/instance-family
        operator: In
        values: ["m6i", "m6g", "m7i", "m7g"]
  limits:
    cpu: 1000
    memory: 1000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
```

### 8.6 업그레이드 전략

#### 클러스터 업그레이드 순서

```
1. 백업 확인
   └── etcd 스냅샷, PV 백업

2. 애드온 호환성 확인
   └── VPC CNI, CoreDNS, kube-proxy 버전 매트릭스

3. 컨트롤 플레인 업그레이드
   └── aws eks update-cluster-version

4. 노드그룹 업그레이드
   └── 관리형: update-nodegroup-version
   └── 자체 관리형: 노드 교체

5. 애드온 업그레이드
   └── VPC CNI → CoreDNS → kube-proxy

6. 애플리케이션 검증
   └── 스모크 테스트
```

```bash
# 클러스터 버전 업그레이드
aws eks update-cluster-version \
  --name my-cluster \
  --kubernetes-version 1.30

# 노드그룹 업그레이드
aws eks update-nodegroup-version \
  --cluster-name my-cluster \
  --nodegroup-name managed-ng \
  --kubernetes-version 1.30
```

---

## 9. 체크리스트

### 클러스터 생성 시

- [ ] 프라이빗 서브넷에 노드 배치
- [ ] 관리형 노드그룹 사용
- [ ] 클러스터 로깅 활성화 (모든 유형)
- [ ] OIDC Provider 연결
- [ ] VPC CNI 최신 버전
- [ ] Secrets envelope 암호화 (KMS)

### 보안

- [ ] 프라이빗 엔드포인트 사용
- [ ] Pod Security Standards 적용
- [ ] IRSA로 Pod 권한 관리
- [ ] Network Policy 적용
- [ ] Secrets 암호화 (KMS)
- [ ] 이미지 스캔 활성화
- [ ] aws-auth ConfigMap 정기 검토

### 안정성

- [ ] Multi-AZ 노드 분산
- [ ] PodDisruptionBudget 설정
- [ ] Liveness/Readiness Probe 설정
- [ ] Graceful Shutdown 구현
- [ ] Pod Anti-Affinity 설정

### 성능 및 비용

- [ ] 리소스 requests/limits 설정
- [ ] HPA/VPA 설정
- [ ] Spot Instance 활용 (가능한 경우)
- [ ] Graviton 노드 고려
- [ ] AWS Load Balancer Controller 설치
- [ ] Metrics Server 설치
- [ ] Container Insights 활성화

---

## 10. 참고 자료

| 문서 | 링크 |
|------|------|
| **EKS Best Practices Guide** | https://aws.github.io/aws-eks-best-practices/ |
| **EKS User Guide** | https://docs.aws.amazon.com/eks/latest/userguide/ |
| **EKS Workshop** | https://www.eksworkshop.com/ |
| **Karpenter** | https://karpenter.sh/ |
| **AWS Load Balancer Controller** | https://kubernetes-sigs.github.io/aws-load-balancer-controller/ |
