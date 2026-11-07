# Домен: Audit & Reporting (Аудит и отчетность)

## Статус
**OUT_OF_SCOPE** (GL, двойная запись, 1С-уровень финансовая консолидация)

## 1. Назначение
Логирование и трассировка всех операций для аудита, финансовой отчетности, налогообложения.

**Важно:** GL (General Ledger), двойная запись (double-entry bookkeeping), финансовая консолидация — **OUT_OF_SCOPE**. 
Интеграция с 1С, SAP, или аналогичной системой — будущая работа.

## 2. Основные сущности (для аудита в пределах ERP)
- **AuditLog** — лог всех операций (id, entity_type, entity_id, action, old_value, new_value, user_id, timestamp)
- **EventLog** — события (stock_movement, payment_attempt, order_status_change)

## 3. Основные процессы
- Запись каждого изменения (CREATE, UPDATE, DELETE) в AuditLog
- Связь с domain events (StockMovement, PaymentAttempt, OrderStatusChange)
- Экспорт данных для бухгалтерии

## 4. Граница интеграции
**Входящие:**
- Все домены → отправка событий в AuditLog

**Исходящие:**
- → Внешние системы (1С, SAP): экспорт через API/export

## 5. Инварианты и правила
- BR-100: Все изменения в таблицах логируются в AuditLog
- BR-101: AuditLog неизменяем (append-only)

## 6. Состояния
- LOGGED (только одно состояние)

## 7. Журнал и аудит
- AuditLog сама является журналом

## 8. Интеграция
- Все домены пишут в AuditLog
- Экспорт в 1С / SAP: отдельный сервис (вне ERP)

## 9. OPEN вопросы
- [ ] GL schema design?
- [ ] Double-entry bookkeeping rules?
- [ ] Tax reporting integration?
- [ ] Compliance audit trail?

---

## Что делается в пределах ERP

В пределах этого проекта:
1. **AuditLog** — каждое изменение, кто и когда
2. **StockMovement** — каждое движение товара (основание для бухгалтерии)
3. **PaymentAttempt** — каждая попытка оплаты
4. **OrderStatusChange** — все статусы заказов
5. **InvoiceStatusChange** — все статусы счетов

Затем data export → 1С / бухгалтер для GL и финансовой отчетности.

## Следующие шаги
- [ ] Определить необходимость GL в этом проекте или все ч/з 1С?
- [ ] Spec export format для 1С
- [ ] Audit trail compliance requirements (какие данные нужны для налоговой?)
