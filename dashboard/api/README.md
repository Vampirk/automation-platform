# 🌐 Dashboard API

FastAPI 기반 REST API 서버로 작업 관리, 모니터링, 통계 조회 기능을 제공합니다.

**작성자:** 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)  
**작성일:** 2025-10-26  
**상태:** ✅ 완료

---

## 📁 파일 구조

```
dashboard/api/
├── __init__.py           # 패키지 초기화
├── main.py              # FastAPI 메인 서버
├── dependencies.py      # 공통 의존성 (DB 세션 등)
├── schemas.py           # Pydantic 스키마
├── jobs.py              # 작업 관리 API
├── monitoring.py        # 모니터링 API
└── README.md           # 이 파일
```

---

## 🎯 주요 기능

### 1. 작업 관리 API (`/jobs`)
- ✅ 작업 CRUD (생성, 조회, 수정, 삭제)
- ✅ 작업 활성화/비활성화
- ✅ 작업 즉시 실행
- ✅ 작업 실행 이력 조회
- ✅ 필터링 및 페이지네이션

### 2. 모니터링 API (`/monitoring`)
- ✅ 시스템 메트릭 조회 (CPU/메모리/디스크/네트워크)
- ✅ 실시간 시스템 상태 조회
- ✅ 알림 조회
- ✅ 대시보드 통계
- ✅ 시스템 건강 상태 체크
- ✅ 최근 실행 이력 및 알림 조회

---

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
# FastAPI 및 관련 패키지 설치
pip install fastapi uvicorn[standard] pydantic python-multipart

# 또는 requirements.txt에 추가
echo "fastapi>=0.104.0" >> requirements.txt
echo "uvicorn[standard]>=0.24.0" >> requirements.txt
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일에 API 서버 설정 추가:

```env
# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
```

### 3. 서버 실행

#### 방법 1: 직접 실행
```bash
# 프로젝트 루트에서 실행
PYTHONPATH=/path/to/automation-platform python dashboard/api/main.py
```

#### 방법 2: uvicorn 직접 사용
```bash
# 개발 모드 (자동 재시작)
uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8000 --reload

# 프로덕션 모드
uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 방법 3: Python 모듈로 실행
```bash
python -m dashboard.api.main
```

### 4. API 문서 확인

서버 실행 후 브라우저에서 접속:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 📚 API 엔드포인트

### 기본 엔드포인트

#### `GET /`
루트 엔드포인트 - API 정보 조회

**응답:**
```json
{
  "name": "Automation Platform API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "endpoints": {
    "jobs": "/jobs",
    "monitoring": "/monitoring"
  }
}
```

#### `GET /health`
헬스 체크

**응답:**
```json
{
  "status": "healthy",
  "platform": "linux",
  "api_version": "1.0.0"
}
```

### 작업 관리 API

#### `GET /jobs`
작업 목록 조회

**쿼리 파라미터:**
- `skip`: 건너뛸 레코드 수 (기본값: 0)
- `limit`: 조회할 레코드 수 (기본값: 100, 최대: 1000)
- `sort_by`: 정렬 기준 (id/name/created_at/updated_at)
- `order`: 정렬 순서 (asc/desc)
- `enabled`: 활성화 상태 필터 (true/false)
- `job_type`: 작업 유형 필터 (monitoring/security/account/etc)

**응답 예시:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "name": "daily_monitoring",
      "description": "일일 시스템 모니터링",
      "job_type": "monitoring",
      "script_path": "scripts/monitoring/system_monitor.py",
      "cron_expression": "0 0 * * *",
      "enabled": true,
      "created_at": "2025-10-26T00:00:00Z",
      "updated_at": "2025-10-26T00:00:00Z"
    }
  ]
}
```

#### `GET /jobs/{job_id}`
작업 상세 조회

#### `POST /jobs`
작업 생성

**요청 본문:**
```json
{
  "name": "new_job",
  "description": "새로운 작업",
  "job_type": "monitoring",
  "script_path": "scripts/monitoring/system_monitor.py",
  "cron_expression": "0 * * * *",
  "enabled": true,
  "max_retries": 3,
  "timeout_seconds": 300,
  "priority": 5
}
```

#### `PUT /jobs/{job_id}`
작업 수정

**요청 본문:** (수정할 필드만 포함)
```json
{
  "enabled": false,
  "cron_expression": "0 */2 * * *"
}
```

#### `DELETE /jobs/{job_id}`
작업 삭제

#### `POST /jobs/{job_id}/enable`
작업 활성화

#### `POST /jobs/{job_id}/disable`
작업 비활성화

#### `POST /jobs/{job_id}/execute`
작업 즉시 실행

**응답:** JobExecution 객체

#### `GET /jobs/{job_id}/executions`
작업 실행 이력 조회

**쿼리 파라미터:**
- `skip`, `limit`, `sort_by`, `order`
- `status_filter`: 상태 필터 (pending/running/success/failed/cancelled)

#### `GET /jobs/executions/{execution_id}`
실행 이력 상세 조회

### 모니터링 API

#### `GET /monitoring/metrics`
시스템 메트릭 조회

**쿼리 파라미터:**
- `skip`, `limit`, `sort_by`, `order`
- `hostname`: 호스트명 필터
- `start_time`: 시작 시간 (ISO 8601 형식)
- `end_time`: 종료 시간 (ISO 8601 형식)

#### `GET /monitoring/metrics/latest`
최신 시스템 메트릭 조회

**쿼리 파라미터:**
- `hostname`: 호스트명 (선택적)

#### `GET /monitoring/metrics/current`
현재 시스템 메트릭 조회 (실시간)

**응답 예시:**
```json
{
  "hostname": "server01",
  "timestamp": "2025-10-26T12:00:00Z",
  "cpu": {
    "percent": 45.2,
    "count": 8
  },
  "memory": {
    "total_gb": 16.0,
    "used_gb": 8.5,
    "percent": 53.1
  },
  "disk": {
    "total_gb": 500.0,
    "used_gb": 250.0,
    "percent": 50.0
  },
  "network": {
    "sent_mb": 1024.5,
    "recv_mb": 2048.3
  }
}
```

#### `GET /monitoring/notifications`
알림 목록 조회

**쿼리 파라미터:**
- `skip`, `limit`, `sort_by`, `order`
- `level`: 레벨 필터 (INFO/WARNING/ERROR/CRITICAL)
- `channel`: 채널 필터 (email/slack/discord)
- `start_time`: 시작 시간
- `end_time`: 종료 시간

#### `GET /monitoring/notifications/{notification_id}`
알림 상세 조회

#### `GET /monitoring/stats`
대시보드 통계 조회

**응답 예시:**
```json
{
  "total_jobs": 10,
  "enabled_jobs": 8,
  "total_executions": 1234,
  "success_executions": 1150,
  "failed_executions": 84,
  "success_rate": 93.19,
  "total_notifications": 567,
  "critical_notifications": 12
}
```

#### `GET /monitoring/health`
시스템 건강 상태 조회

**응답 예시:**
```json
{
  "status": "healthy",
  "cpu_status": "healthy",
  "memory_status": "warning",
  "disk_status": "healthy",
  "last_check": "2025-10-26T12:00:00Z",
  "current_cpu": 45.2,
  "current_memory": 85.3,
  "current_disk": 50.0
}
```

#### `GET /monitoring/executions/recent`
최근 작업 실행 이력 조회

**쿼리 파라미터:**
- `limit`: 조회할 레코드 수 (1-100, 기본값: 10)

#### `GET /monitoring/notifications/recent`
최근 알림 조회

**쿼리 파라미터:**
- `limit`: 조회할 레코드 수 (1-100, 기본값: 10)
- `min_level`: 최소 레벨 (INFO/WARNING/ERROR/CRITICAL)

---

## 💻 사용 예시

### cURL

```bash
# 작업 목록 조회
curl http://localhost:8000/jobs

# 작업 생성
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_job",
    "job_type": "monitoring",
    "script_path": "scripts/monitoring/system_monitor.py",
    "cron_expression": "0 * * * *",
    "enabled": true
  }'

# 작업 실행
curl -X POST http://localhost:8000/jobs/1/execute

# 현재 시스템 메트릭 조회
curl http://localhost:8000/monitoring/metrics/current

# 대시보드 통계 조회
curl http://localhost:8000/monitoring/stats
```

### Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# 작업 목록 조회
response = requests.get(f"{BASE_URL}/jobs")
jobs = response.json()
print(f"Total jobs: {jobs['total']}")

# 작업 생성
new_job = {
    "name": "test_job",
    "job_type": "monitoring",
    "script_path": "scripts/monitoring/system_monitor.py",
    "cron_expression": "0 * * * *",
    "enabled": True
}
response = requests.post(f"{BASE_URL}/jobs", json=new_job)
created_job = response.json()
print(f"Created job ID: {created_job['id']}")

# 작업 실행
job_id = created_job['id']
response = requests.post(f"{BASE_URL}/jobs/{job_id}/execute")
execution = response.json()
print(f"Execution ID: {execution['id']}, Status: {execution['status']}")

# 시스템 메트릭 조회
response = requests.get(f"{BASE_URL}/monitoring/metrics/current")
metrics = response.json()
print(f"CPU: {metrics['cpu']['percent']}%")
print(f"Memory: {metrics['memory']['percent']}%")
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// 작업 목록 조회
fetch(`${BASE_URL}/jobs`)
  .then(response => response.json())
  .then(data => console.log('Jobs:', data));

// 작업 생성
const newJob = {
  name: 'test_job',
  job_type: 'monitoring',
  script_path: 'scripts/monitoring/system_monitor.py',
  cron_expression: '0 * * * *',
  enabled: true
};

fetch(`${BASE_URL}/jobs`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(newJob)
})
  .then(response => response.json())
  .then(data => console.log('Created:', data));

// 현재 시스템 메트릭
fetch(`${BASE_URL}/monitoring/metrics/current`)
  .then(response => response.json())
  .then(data => {
    console.log(`CPU: ${data.cpu.percent}%`);
    console.log(`Memory: ${data.memory.percent}%`);
  });
```

---

## 🔒 보안 고려사항

### 현재 구현
- ✅ CORS 설정 (현재는 모든 origin 허용)
- ✅ 요청 검증 (Pydantic)
- ✅ 에러 핸들링

### 프로덕션 환경 권장사항
- [ ] API 키 인증 구현
- [ ] HTTPS 사용 (nginx/reverse proxy)
- [ ] Rate limiting
- [ ] CORS origin 제한
- [ ] JWT 토큰 인증
- [ ] 입력 sanitization
- [ ] SQL injection 방어 (SQLAlchemy ORM 사용 중)

### CORS 설정 수정 (프로덕션)

`main.py`의 CORS 설정을 수정:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 🐛 문제 해결

### 1. ModuleNotFoundError

**문제:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**해결:**
```bash
pip install fastapi uvicorn[standard]
```

### 2. 포트 이미 사용 중

**문제:**
```
OSError: [Errno 98] Address already in use
```

**해결:**
```bash
# 다른 포트 사용
uvicorn dashboard.api.main:app --port 8001

# 또는 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9
```

### 3. 데이터베이스 연결 오류

**문제:**
```
OperationalError: unable to open database file
```

**해결:**
```bash
# 데이터베이스 초기화
python storage/database.py

# 권한 확인
chmod 664 data/automation.db
```

### 4. CORS 에러

**문제:**
브라우저에서 API 호출 시 CORS 에러 발생

**해결:**
`main.py`의 CORS 설정에서 프론트엔드 origin 추가

---

## 📊 성능 최적화

### 1. 데이터베이스 인덱스
이미 주요 컬럼에 인덱스 설정됨:
- `jobs.name` (unique index)
- `job_executions.job_id`, `job_executions.status`
- `system_metrics.timestamp`, `system_metrics.hostname`

### 2. 페이지네이션
모든 목록 API는 페이지네이션 지원 (최대 1000개)

### 3. 워커 수 증가 (프로덕션)
```bash
uvicorn dashboard.api.main:app --workers 4
```

### 4. 캐싱 (선택적)
Redis 캐싱을 추가하여 반복 조회 성능 향상 가능

---

## 🧪 테스트

### API 테스트
```bash
# 프로젝트 루트에서
python -m pytest tests/api/

# 또는 수동 테스트
python dashboard/api/main.py &
sleep 5
curl http://localhost:8000/health
curl http://localhost:8000/jobs
kill %1
```

### 부하 테스트 (선택적)
```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

---

## 🗺️ 향후 계획

- [ ] WebSocket 지원 (실시간 로그 스트리밍)
- [ ] GraphQL API 추가 (선택적)
- [ ] API 키 인증
- [ ] Rate limiting
- [ ] Redis 캐싱
- [ ] 메트릭 집계 API (시간대별/일별)
- [ ] 작업 스케줄러 통합 (API에서 직접 스케줄 관리)

---

## 📚 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Uvicorn 문서](https://www.uvicorn.org/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)

---

**💡 Tip:** Swagger UI (`/docs`)에서 모든 API를 인터랙티브하게 테스트할 수 있습니다!
