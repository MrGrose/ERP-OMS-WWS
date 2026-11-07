# Домен: Suppliers (Поставщики)

## Статус
**PROPOSED**

## 1. Назначение
Управление данными поставщиков: контакты, условия поставки, цены.

## 2. Основные сущности
- **Supplier** — поставщик (id, name, contact_email, phone, payment_terms)
- **SupplierContact** — контакты
- **SupplierPricelist** — цены на товары

## 3. Основные процессы
- Регистрация поставщика
- Обновление данных
- Управление ценами и условиями

## 4. Граница интеграции
**Входящие:**
- **Purchasing** → создание ПО для поставщика

**Исходящие:**
- → **Purchasing**: цены (SupplierPricelist)
- → **Audit**: история

## 5. Инварианты и правила
- BR-070: Supplier.payment_terms может быть NET_30, NET_60, etc.

## 6. Состояния
- ACTIVE, INACTIVE, SUSPENDED

## 7. Журнал и аудит
- Все изменения в audit_log

## 8. Интеграция
- Purchasing uses supplier_id, payment_terms
- SupplierPricelist for pricing ПО

## 9. OPEN вопросы
- [ ] Supplier performance metrics?
- [ ] Quality ratings?
- [ ] EDI integration?
