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

## 8. 체크리스트

### 클러스터 생성 시

- [ ] 프라이빗 서브넷에 노드 배치
- [ ] 관리형 노드그룹 사용
- [ ] 클러스터 로깅 활성화
- [ ] OIDC Provider 연결
- [ ] VPC CNI 최신 버전

### 보안

- [ ] 프라이빗 엔드포인트 사용
- [ ] Pod Security Standards 적용
- [ ] IRSA로 Pod 권한 관리
- [ ] Network Policy 적용
- [ ] Secrets 암호화 (KMS)

### 운영

- [ ] AWS Load Balancer Controller 설치
- [ ] Metrics Server 설치
- [ ] Container Insights 활성화
- [ ] HPA/VPA 설정
- [ ] PodDisruptionBudget 설정
