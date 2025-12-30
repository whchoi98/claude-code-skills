#!/usr/bin/env python3
"""
AWS Infrastructure Agent
Claude Agent SDK를 사용하여 AWS 인프라를 관리하는 에이전트입니다.
"""

import anthropic
import boto3
import json
import subprocess
from datetime import datetime
from typing import Any

# AWS Skill 시스템 프롬프트
AWS_SKILL_PROMPT = """당신은 AWS 인프라 관리 전문가입니다.

## 역할
- AWS 리소스 상태 모니터링 및 분석
- 보안 설정 검토 및 권장사항 제공
- 비용 최적화 제안
- 인프라 문제 해결

## 사용 가능한 도구
- aws_cli: AWS CLI 명령 실행
- get_ec2_instances: EC2 인스턴스 목록 조회
- get_security_groups: Security Group 조회
- get_cost_summary: 비용 요약 조회

## 원칙
1. 안전 우선: 리소스 삭제/수정 전 항상 확인
2. 비용 인식: 비용 발생 가능 작업은 미리 경고
3. 최소 권한: 필요한 최소한의 작업만 수행
4. 명확한 설명: 모든 작업과 결과를 명확하게 설명
"""

# 도구 정의
TOOLS = [
    {
        "name": "aws_cli",
        "description": "AWS CLI 명령을 실행합니다. 읽기 전용 명령만 허용됩니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "실행할 AWS CLI 명령 (aws 접두사 제외). 예: 'ec2 describe-instances'"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "get_ec2_instances",
        "description": "현재 리전의 EC2 인스턴스 목록을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "필터링할 인스턴스 상태 (running, stopped, all)",
                    "enum": ["running", "stopped", "all"]
                }
            }
        }
    },
    {
        "name": "get_security_groups",
        "description": "VPC의 Security Group 목록을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "vpc_id": {
                    "type": "string",
                    "description": "VPC ID (선택사항, 미지정시 모든 VPC)"
                }
            }
        }
    },
    {
        "name": "get_cost_summary",
        "description": "최근 AWS 비용 요약을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "조회할 기간 (일수, 기본값: 7)",
                    "default": 7
                }
            }
        }
    }
]

# 위험한 명령어 블랙리스트
DANGEROUS_COMMANDS = [
    "delete", "terminate", "remove", "destroy",
    "create", "modify", "update", "put",
    "start", "stop", "reboot"
]


class AWSAgent:
    def __init__(self, region: str = "ap-northeast-2"):
        self.client = anthropic.Anthropic()
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer는 us-east-1만 지원
        self.conversation_history = []

    def is_safe_command(self, command: str) -> bool:
        """명령어가 안전한지 확인"""
        command_lower = command.lower()
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command_lower:
                return False
        return True

    def execute_aws_cli(self, command: str) -> dict:
        """AWS CLI 명령 실행"""
        if not self.is_safe_command(command):
            return {
                "error": f"위험한 명령어가 감지되었습니다: {command}",
                "message": "읽기 전용 명령만 허용됩니다."
            }

        try:
            full_command = f"aws {command} --region {self.region} --output json"
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout}
            else:
                return {"error": result.stderr}

        except subprocess.TimeoutExpired:
            return {"error": "명령 실행 시간 초과 (30초)"}
        except Exception as e:
            return {"error": str(e)}

    def get_ec2_instances(self, state: str = "all") -> dict:
        """EC2 인스턴스 조회"""
        try:
            filters = []
            if state != "all":
                filters.append({
                    'Name': 'instance-state-name',
                    'Values': [state]
                })

            response = self.ec2.describe_instances(Filters=filters)

            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    name = ""
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break

                    instances.append({
                        "InstanceId": instance['InstanceId'],
                        "Name": name,
                        "Type": instance['InstanceType'],
                        "State": instance['State']['Name'],
                        "PrivateIp": instance.get('PrivateIpAddress', 'N/A'),
                        "PublicIp": instance.get('PublicIpAddress', 'N/A'),
                        "LaunchTime": instance['LaunchTime'].isoformat()
                    })

            return {"instances": instances, "count": len(instances)}

        except Exception as e:
            return {"error": str(e)}

    def get_security_groups(self, vpc_id: str = None) -> dict:
        """Security Group 조회"""
        try:
            filters = []
            if vpc_id:
                filters.append({
                    'Name': 'vpc-id',
                    'Values': [vpc_id]
                })

            response = self.ec2.describe_security_groups(Filters=filters)

            security_groups = []
            for sg in response['SecurityGroups']:
                # 위험한 인바운드 규칙 확인
                risky_rules = []
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            risky_rules.append({
                                "port": rule.get('FromPort', 'All'),
                                "protocol": rule.get('IpProtocol', 'All'),
                                "source": "0.0.0.0/0"
                            })

                security_groups.append({
                    "GroupId": sg['GroupId'],
                    "GroupName": sg['GroupName'],
                    "VpcId": sg.get('VpcId', 'N/A'),
                    "Description": sg['Description'],
                    "InboundRulesCount": len(sg.get('IpPermissions', [])),
                    "RiskyRules": risky_rules
                })

            return {"security_groups": security_groups, "count": len(security_groups)}

        except Exception as e:
            return {"error": str(e)}

    def get_cost_summary(self, days: int = 7) -> dict:
        """비용 요약 조회"""
        try:
            from datetime import timedelta

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )

            # 서비스별 비용 집계
            service_costs = {}
            total_cost = 0

            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    service_costs[service] = service_costs.get(service, 0) + cost
                    total_cost += cost

            # 상위 5개 서비스
            top_services = sorted(
                service_costs.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            return {
                "period": f"{start_date} ~ {end_date}",
                "total_cost": f"${total_cost:.2f}",
                "top_services": [
                    {"service": s, "cost": f"${c:.2f}"}
                    for s, c in top_services
                ]
            }

        except Exception as e:
            return {"error": str(e)}

    def process_tool_call(self, tool_name: str, tool_input: dict) -> Any:
        """도구 호출 처리"""
        if tool_name == "aws_cli":
            return self.execute_aws_cli(tool_input.get("command", ""))
        elif tool_name == "get_ec2_instances":
            return self.get_ec2_instances(tool_input.get("state", "all"))
        elif tool_name == "get_security_groups":
            return self.get_security_groups(tool_input.get("vpc_id"))
        elif tool_name == "get_cost_summary":
            return self.get_cost_summary(tool_input.get("days", 7))
        else:
            return {"error": f"알 수 없는 도구: {tool_name}"}

    def chat(self, user_message: str) -> str:
        """사용자 메시지 처리 및 응답"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Claude API 호출
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=AWS_SKILL_PROMPT,
            tools=TOOLS,
            messages=self.conversation_history
        )

        # 도구 호출 처리 (에이전트 루프)
        while response.stop_reason == "tool_use":
            # 응답에서 도구 호출 추출
            tool_use_block = None
            text_content = ""

            for block in response.content:
                if block.type == "tool_use":
                    tool_use_block = block
                elif block.type == "text":
                    text_content = block.text

            if tool_use_block:
                # 도구 실행
                tool_result = self.process_tool_call(
                    tool_use_block.name,
                    tool_use_block.input
                )

                # 대화 기록에 추가
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })

                self.conversation_history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id,
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        }
                    ]
                })

                # 다음 응답 요청
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=AWS_SKILL_PROMPT,
                    tools=TOOLS,
                    messages=self.conversation_history
                )

        # 최종 응답 추출
        final_response = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_response += block.text

        # 대화 기록에 추가
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        return final_response

    def run_interactive(self):
        """대화형 모드 실행"""
        print("=" * 60)
        print("AWS Infrastructure Agent")
        print(f"Region: {self.region}")
        print("=" * 60)
        print("명령어: 'quit' 종료, 'clear' 대화 초기화")
        print("-" * 60)

        while True:
            try:
                user_input = input("\n[You] ").strip()

                if not user_input:
                    continue

                if user_input.lower() == 'quit':
                    print("Agent를 종료합니다.")
                    break

                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("대화 기록이 초기화되었습니다.")
                    continue

                print("\n[Agent] ", end="")
                response = self.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\nAgent를 종료합니다.")
                break
            except Exception as e:
                print(f"\n오류 발생: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AWS Infrastructure Agent")
    parser.add_argument(
        "--region",
        default="ap-northeast-2",
        help="AWS 리전 (기본값: ap-northeast-2)"
    )
    parser.add_argument(
        "--query",
        "-q",
        help="단일 질문 모드 (대화형 모드 대신)"
    )

    args = parser.parse_args()

    agent = AWSAgent(region=args.region)

    if args.query:
        # 단일 질문 모드
        response = agent.chat(args.query)
        print(response)
    else:
        # 대화형 모드
        agent.run_interactive()


if __name__ == "__main__":
    main()
