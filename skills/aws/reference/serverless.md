# Serverless Reference

AWS 서버리스 서비스 (Lambda, API Gateway, Step Functions, EventBridge) 가이드입니다.

## MCP 서버 설정

```json
{
  "mcpServers": {
    "aws-lambda": {
      "command": "uvx",
      "args": ["awslabs.lambda-tool-mcp-server@latest"],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "aws-stepfunctions": {
      "command": "uvx",
      "args": ["awslabs.stepfunctions-tool-mcp-server@latest"],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    },
    "aws-serverless": {
      "command": "uvx",
      "args": ["awslabs.aws-serverless-mcp-server@latest"],
      "env": {
        "AWS_REGION": "ap-northeast-2",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

### MCP 도구

| 서버 | 도구 | 설명 |
|------|------|------|
| `aws-lambda` | `lambda_list_functions` | 함수 목록 |
| `aws-lambda` | `lambda_invoke` | 함수 호출 |
| `aws-lambda` | `lambda_get_logs` | 로그 조회 |
| `aws-stepfunctions` | `sfn_list_state_machines` | 상태 머신 목록 |
| `aws-stepfunctions` | `sfn_start_execution` | 실행 시작 |

---

## 1. 서버리스 아키텍처

### 1.1 일반적인 패턴

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         서버리스 웹 애플리케이션                              │
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ Route53 │───►│CloudFront│───►│   S3    │    │         │                  │
│  └─────────┘    └─────────┘    │(Static) │    │         │                  │
│                      │         └─────────┘    │         │                  │
│                      ▼                        │         │                  │
│                ┌───────────┐                  │DynamoDB │                  │
│                │API Gateway│                  │         │                  │
│                └─────┬─────┘                  │         │                  │
│                      │                        │         │                  │
│                      ▼                        │         │                  │
│                ┌─────────┐                    │         │                  │
│                │ Lambda  │───────────────────►│         │                  │
│                └─────────┘                    └─────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 이벤트 기반 처리

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         이벤트 기반 아키텍처                                  │
│                                                                             │
│  ┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌─────────┐              │
│  │   S3    │───►│ EventBridge │───►│ Lambda  │───►│   SNS   │              │
│  │(Upload) │    └─────────────┘    │(Process)│    │(Notify) │              │
│  └─────────┘           │           └─────────┘    └─────────┘              │
│                        │                                                    │
│                        ▼                                                    │
│                 ┌─────────────┐                                             │
│                 │Step Functions│                                            │
│                 │ (Workflow)  │                                             │
│                 └─────────────┘                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AWS Lambda

### 2.1 Lambda 기본 구조

```python
# Python Lambda 핸들러
import json
import boto3

def lambda_handler(event, context):
    """
    event: 트리거 소스에서 전달된 이벤트 데이터
    context: 런타임 정보 (함수명, 메모리, 실행 시간 등)
    """

    # 로직 처리
    result = process_event(event)

    # 응답 반환
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(result)
    }

def process_event(event):
    # 비즈니스 로직
    return {'message': 'Success'}
```

```javascript
// Node.js Lambda 핸들러
exports.handler = async (event, context) => {
    try {
        const result = await processEvent(event);

        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(result)
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Internal Server Error' })
        };
    }
};
```

### 2.2 Lambda 설정 권장사항

| 설정 | 권장값 | 설명 |
|------|--------|------|
| **메모리** | 128MB ~ 10GB | 메모리 증가 시 CPU도 증가 |
| **제한 시간** | 최소 필요 시간 | 최대 15분 |
| **동시성** | 기본 1000 | 계정/함수별 제한 가능 |
| **임시 스토리지** | 512MB ~ 10GB | /tmp 디렉토리 |

### 2.3 Lambda 생성 및 관리

```bash
# 함수 생성
aws lambda create-function \
  --function-name my-function \
  --runtime python3.12 \
  --role arn:aws:iam::xxx:role/lambda-role \
  --handler index.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 256

# 함수 호출
aws lambda invoke \
  --function-name my-function \
  --payload '{"key": "value"}' \
  response.json

# 로그 조회
aws logs filter-log-events \
  --log-group-name /aws/lambda/my-function \
  --start-time $(date -d '1 hour ago' +%s)000
```

### 2.4 Lambda 계층 (Layer)

```bash
# 계층 생성
aws lambda publish-layer-version \
  --layer-name my-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.12

# 함수에 계층 연결
aws lambda update-function-configuration \
  --function-name my-function \
  --layers arn:aws:lambda:ap-northeast-2:xxx:layer:my-layer:1
```

### 2.5 환경 변수 및 시크릿

```bash
# 환경 변수 설정
aws lambda update-function-configuration \
  --function-name my-function \
  --environment "Variables={DB_HOST=mydb.xxx.rds.amazonaws.com,STAGE=prod}"

# KMS로 암호화
aws lambda update-function-configuration \
  --function-name my-function \
  --kms-key-arn arn:aws:kms:ap-northeast-2:xxx:key/xxx
```

```python
# Secrets Manager에서 시크릿 조회
import boto3
import json

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='my-secret')
    return json.loads(response['SecretString'])
```

---

## 3. API Gateway

### 3.1 API 타입 비교

| 타입 | 용도 | 비용 |
|------|------|------|
| **HTTP API** | 간단한 API, 낮은 지연 | $1/백만 요청 |
| **REST API** | 풀 기능, API 관리 | $3.5/백만 요청 |
| **WebSocket API** | 실시간 통신 | 연결 시간 기반 |

### 3.2 HTTP API (권장)

```bash
# HTTP API 생성
aws apigatewayv2 create-api \
  --name my-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:ap-northeast-2:xxx:function:my-function
```

### 3.3 REST API

```bash
# REST API 생성
aws apigateway create-rest-api \
  --name my-rest-api \
  --endpoint-configuration types=REGIONAL

# 리소스 생성
aws apigateway create-resource \
  --rest-api-id xxx \
  --parent-id xxx \
  --path-part users

# 메서드 생성
aws apigateway put-method \
  --rest-api-id xxx \
  --resource-id xxx \
  --http-method GET \
  --authorization-type NONE

# Lambda 통합
aws apigateway put-integration \
  --rest-api-id xxx \
  --resource-id xxx \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/arn:aws:lambda:xxx/invocations
```

### 3.4 API Gateway 기능

| 기능 | 설명 |
|------|------|
| **인증** | IAM, Cognito, Lambda Authorizer |
| **스로틀링** | 요청 제한 (버스트/정상) |
| **캐싱** | 응답 캐시 (REST API만) |
| **CORS** | 크로스 오리진 설정 |
| **요청 검증** | 스키마 검증 |
| **변환** | 요청/응답 매핑 |

---

## 4. Step Functions

### 4.1 상태 머신 정의 (ASL)

```json
{
  "Comment": "주문 처리 워크플로우",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:xxx:function:validate-order",
      "Next": "ProcessPayment",
      "Catch": [
        {
          "ErrorEquals": ["ValidationError"],
          "Next": "OrderFailed"
        }
      ]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:xxx:function:process-payment",
      "Next": "CheckInventory",
      "Retry": [
        {
          "ErrorEquals": ["PaymentRetryableError"],
          "MaxAttempts": 3,
          "IntervalSeconds": 2,
          "BackoffRate": 2
        }
      ]
    },
    "CheckInventory": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.inventory.available",
          "BooleanEquals": true,
          "Next": "FulfillOrder"
        }
      ],
      "Default": "WaitForInventory"
    },
    "WaitForInventory": {
      "Type": "Wait",
      "Seconds": 300,
      "Next": "CheckInventory"
    },
    "FulfillOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:xxx:function:fulfill-order",
      "Next": "OrderComplete"
    },
    "OrderComplete": {
      "Type": "Succeed"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed",
      "Cause": "Order validation or processing failed"
    }
  }
}
```

### 4.2 상태 타입

| 타입 | 용도 | 예시 |
|------|------|------|
| **Task** | 작업 실행 | Lambda, ECS, SNS 등 |
| **Choice** | 조건 분기 | if/else 로직 |
| **Parallel** | 병렬 실행 | 동시 처리 |
| **Map** | 반복 처리 | 배열 순회 |
| **Wait** | 대기 | 지연 처리 |
| **Pass** | 데이터 전달 | 변환, 기본값 |
| **Succeed** | 성공 종료 | |
| **Fail** | 실패 종료 | |

### 4.3 Step Functions 관리

```bash
# 상태 머신 생성
aws stepfunctions create-state-machine \
  --name my-workflow \
  --definition file://definition.json \
  --role-arn arn:aws:iam::xxx:role/step-functions-role

# 실행 시작
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:xxx:xxx:stateMachine:my-workflow \
  --input '{"orderId": "12345"}'

# 실행 상태 조회
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:xxx:xxx:execution:my-workflow:xxx
```

---

## 5. EventBridge

### 5.1 이벤트 패턴

```json
// S3 객체 생성 이벤트
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["my-bucket"]
    },
    "object": {
      "key": [{
        "prefix": "uploads/"
      }]
    }
  }
}
```

```json
// EC2 상태 변경 이벤트
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": {
    "state": ["stopped", "terminated"]
  }
}
```

### 5.2 규칙 생성

```bash
# 규칙 생성
aws events put-rule \
  --name my-rule \
  --event-pattern file://pattern.json \
  --state ENABLED

# 타겟 추가 (Lambda)
aws events put-targets \
  --rule my-rule \
  --targets "Id"="1","Arn"="arn:aws:lambda:xxx:function:my-function"

# 스케줄 규칙 (Cron)
aws events put-rule \
  --name daily-job \
  --schedule-expression "cron(0 9 * * ? *)" \
  --state ENABLED
```

### 5.3 스케줄 표현식

| 표현식 | 설명 |
|--------|------|
| `rate(5 minutes)` | 5분마다 |
| `rate(1 hour)` | 1시간마다 |
| `rate(1 day)` | 매일 |
| `cron(0 9 * * ? *)` | 매일 오전 9시 (UTC) |
| `cron(0 18 ? * MON-FRI *)` | 평일 오후 6시 |

---

## 6. 서버리스 모범사례

### 6.1 Lambda 최적화

```python
# 연결 재사용 (콜드 스타트 최소화)
import boto3

# 핸들러 외부에서 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('my-table')

def lambda_handler(event, context):
    # 재사용된 연결 사용
    response = table.get_item(Key={'id': event['id']})
    return response['Item']
```

### 6.2 에러 처리

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ValidationError(Exception):
    pass

def lambda_handler(event, context):
    try:
        # 입력 검증
        if 'id' not in event:
            raise ValidationError('id is required')

        result = process(event)
        return success_response(result)

    except ValidationError as e:
        logger.warning(f'Validation error: {e}')
        return error_response(400, str(e))

    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        return error_response(500, 'Internal Server Error')

def success_response(data):
    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }

def error_response(status_code, message):
    return {
        'statusCode': status_code,
        'body': json.dumps({'error': message})
    }
```

### 6.3 비용 최적화

| 전략 | 설명 |
|------|------|
| **메모리 튜닝** | 최적 메모리 크기 찾기 (AWS Lambda Power Tuning) |
| **Provisioned Concurrency** | 콜드 스타트 제거 (예측 가능한 트래픽) |
| **ARM (Graviton2)** | x86 대비 20% 저렴, 34% 성능 향상 |
| **코드 최적화** | 패키지 크기 최소화, 지연 로딩 |

### 6.4 보안

```json
// Lambda 최소 권한 정책
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:xxx:table/my-table"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

## 7. 체크리스트

### Lambda

- [ ] 적절한 메모리/타임아웃 설정
- [ ] 환경 변수 암호화 (KMS)
- [ ] VPC 설정 (필요시)
- [ ] Dead Letter Queue 설정
- [ ] X-Ray 추적 활성화
- [ ] 최소 권한 IAM 역할

### API Gateway

- [ ] 인증/인가 설정
- [ ] 스로틀링 설정
- [ ] CORS 설정
- [ ] 요청 검증
- [ ] 커스텀 도메인 (Route53 + ACM)

### Step Functions

- [ ] 에러 처리 (Catch/Retry)
- [ ] 실행 이력 보존 설정
- [ ] 타임아웃 설정
- [ ] 로깅 활성화

### EventBridge

- [ ] DLQ 설정
- [ ] 이벤트 아카이브
- [ ] 리플레이 설정
