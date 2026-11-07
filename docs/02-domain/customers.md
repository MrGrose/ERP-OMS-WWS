# Домен: Customers (Клиенты)

## Статус
**PROPOSED**

## 1. Назначение
Управление данными клиентов: контакты, адреса, кредитные лимиты, история.

## 2. Основные сущности
- **Customer** — клиент (id, name, email, phone, credit_limit, status)
- **CustomerAddress** — адреса доставки (customer_id, type: BILLING/SHIPPING)
- **CustomerContact** — контакты (customer_id, email, phone, type)

## 3. Основные процессы
- Регистрация клиента
- Обновление данных
- Управление кредитным лимитом
- Заморозка/активация

## 4. Граница интеграции
**Входящие:**
- **Orders** → customer_id для нового заказа

**Исходящие:**
- → **Orders**: доступный credit_limit, кредитные условия
- → **Pricing**: персональные скидки (если есть)
- → **Audit**: история

## 5. Инварианты и правила
- BR-060: Customer.credit_limit >= 0 (или NULL для неограниченного)
- BR-061: Customer.status в [ACTIVE, INACTIVE, SUSPENDED]

## 6. Состояния
- ACTIVE, INACTIVE, SUSPENDED, ARCHIVED

## 7. Журнал и аудит
- Все изменения данных в audit_log
- История кредитов

## 8. Интеграция
- Orders requires customer_id + credit_limit check
- Pricing may use customer_id for custom pricing

## 9. OPEN вопросы
- [ ] Customer segments/tiers?
- [ ] Loyalty program integration?
- [ ] Credit scoring?
