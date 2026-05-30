#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""端到端测试：启动面试 -> 对话 -> 完成 -> 验证数据"""
import urllib.request, json, sys

BASE = 'http://127.0.0.1:5000'

def api(path, data=None):
    url = f'{BASE}{path}'
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
    else:
        req = urllib.request.Request(url)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)}

USER = 'viz_user2'
SID = 'job_interview'

# 1. Start interview
print('=== 1. Start Interview ===')
r = api(f'/api/examiner/start', {'user_id': USER, 'scenario_id': SID})
print(f'  success={r.get("success")}, conv_id={r.get("conversation_id")}')
if not r.get('success'):
    print(f'  ERROR: {r}')
    sys.exit(1)
CONV_ID = r['conversation_id']

# 2. Chat rounds
answers = [
    '我叫张三，北京大学计算机专业毕业，有5年Java后端开发经验，曾在阿里巴巴工作过。',
    '我负责支付系统的后端开发，使用Spring Boot、Redis、消息队列等，系统QPS达到10万+。',
    '我设计过分布式限流方案，使用令牌桶算法，通过Redis和消息队列实现高可用。',
]
for i, msg in enumerate(answers):
    r = api('/api/examiner/chat', {
        'user_id': USER, 'scenario_id': SID,
        'conversation_id': CONV_ID, 'user_message': msg
    })
    print(f'  Chat {i+1}: success={r.get("success")}, round={r.get("round_count")}')
    if not r.get('success'):
        print(f'  ERROR: {r}')
        sys.exit(1)

# 3. Finish interview
print('=== 2. Finish Interview ===')
r = api('/api/examiner/finish', {'conversation_id': CONV_ID})
print(f'  success={r.get("success")}')
report = r.get('report', {})
if isinstance(report, dict):
    print(f'  score={report.get("overall_score")}')
    print(f'  dimensions={[(d["name"], d["score"]) for d in report.get("dimensions", [])]}')
    print(f'  new_badges={len(report.get("new_badges", []))}')

# 4. Verify visualization data
print('\n=== 3. Verify Data ===')
r = api(f'/api/user/{USER}/summary')
data = r.get('data', {})
print(f'  Summary: total_practices={data.get("total_practices")}, '
      f'avg_score={data.get("avg_score")}, '
      f'scenario_count={data.get("scenario_count")}, '
      f'total_badges={data.get("total_badges")}')

r = api(f'/api/user/{USER}/streak')
print(f'  Streak: {r.get("streak")}')

r = api(f'/api/user/{USER}/dimension-trend')
trend = r.get('data', [])
print(f'  Dim Trend: {len(trend)} items')
if trend:
    for t in trend[:2]:
        print(f'    {t}')

print('\nDone!')
