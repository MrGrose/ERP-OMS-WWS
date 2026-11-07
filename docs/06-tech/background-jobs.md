# Background Jobs и асинхронная обработка

## Статус
**PROPOSED**

## Назначение
Спецификация задач, которые должны выполняться асинхронно, вне HTTP request/response цикла.

---

## Jobs (будущие фичи)

### 1. Inventory Reorder Signal
**Триггер**: Scheduled job (e.g., cron hourly)  
**Действие**: 
- Запрос all SKUs where on_hand < reorder_point
- Автоматическое создание PurchaseOrder (если enabled)
- Notification to procurement team

**Priority**: LOW (фондация)  
**Frequency**: Hourly или на demand  
**Retry**: 3x с exponential backoff

---

### 2. Payment Reconciliation
**Триггер**: Scheduled job (daily)  
**Действие**:
- Sync с payment gateway (Stripe, PayPal)
- Reconvile PaymentAttempt with actual transactions
- Flag discrepancies for investigation

**Priority**: HIGH  
**Frequency**: Daily  
**Retry**: Manual escalation (не auto-retry)

---

### 3. Invoice Dunning (Overdue Reminder)
**Триггер**: Scheduled job (daily)  
**Действие**:
- Find Invoices where status=ISSUED and due_date < today
- Send reminders (email / in-app notification)
- Escalate to dunning process

**Priority**: MEDIUM  
**Frequency**: Daily  
**Retry**: No (notification only)

---

### 4. Order Expiration (Backorder cleanup)
**Триггер**: Scheduled job (weekly)  
**Действие**:
- Find Orders where status=PENDING and created_at < today − 30 days
- Auto-cancel if still not paid
- Release reservations

**Priority**: MEDIUM  
**Frequency**: Weekly  
**Retry**: No (cleanup only)

---

### 5. Physical Inventory Count Report
**Триггер**: Scheduled job (monthly)  
**Действие**:
- Generate inventory variance report
- Compare physical count with system
- Export for auditor

**Priority**: LOW  
**Frequency**: Monthly  
**Retry**: No (report only)

---

### 6. Audit Log Cleanup / Archival
**Триггер**: Scheduled job (quarterly)  
**Действие**:
- Archive old audit_log records (> 1 year)
- Compress to archive storage (if needed)

**Priority**: LOW  
**Frequency**: Quarterly  
**Retry**: No (maintenance only)

---

## Job Queue Implementation

### Option 1: Celery + Redis (RECOMMENDED for future)
```python
from celery import Celery

app = Celery("erp")
app.conf.broker_url = "redis://localhost:6379"


@app.task
def reorder_signal_job():
    # Scan inventory
    ...
```

**Pros**: Scalable, distributed, retry built-in  
**Cons**: Requires Redis, adds complexity

### Option 2: APScheduler (CURRENT for foundation)
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(reorder_signal_job, "cron", hour=0)
scheduler.start()
```

**Pros**: Simple, no external dependencies  
**Cons**: Single-process, no distribution

### Option 3: Kubernetes CronJob (PRODUCTION)
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: reorder-signal-job
spec:
  schedule: "0 * * * *"  # hourly
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: erp
            image: erp:latest
            command: ["python", "-m", "erp.jobs.reorder_signal"]
```

**Pros**: Managed by k8s, scalable  
**Cons**: Requires Kubernetes

---

## Job monitoring

- Logging: каждый job логирует start, end, status
- Metrics: duration, success/failure rate
- Alerting: если job failed 3x подряд → alert DevOps
- Dashboard: (будущее) показать job history

---

## Error handling

**Retry policy**:
- Transient errors (DB timeout, network): 3x с exponential backoff
- Permanent errors (validation error): log + skip
- Critical errors (data corruption): alert immediately

---

## OPEN вопросы

- [ ] Job scheduling: APScheduler, Celery, или k8s CronJob?
- [ ] Notification method: email, Slack, SMS?
- [ ] Dunning escalation: what's the process? (lawyer involved?)
- [ ] Archive destination: S3, file system, or database?
