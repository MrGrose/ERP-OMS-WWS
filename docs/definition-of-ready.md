# Definition of Ready (DoR)

## Статус
**PROPOSED**

## Назначение
Критерии, которым должна соответствовать задача перед тем, как ее можно начать реализовывать.

---

## Checklist для задачи (перед StartWork)

### 1. Requirement clarity
- [ ] Задача ясна и однозначна (или есть несколько option?)?
- [ ] Есть criteria of acceptance (что значит "done")?
- [ ] Определены граничные случаи (edge cases)?
- [ ] Если нужны, обсуждены dependency на другие домены?

### 2. Domain boundary
- [ ] Понятно, какой домен затрагивается?
- [ ] Задача соответствует domain boundaries?
- [ ] Если cross-domain, есть ли spec в `docs/02-domain/cross-domain-flows.md`?

### 3. Business rules
- [ ] Определены соответствующие BR-xxx?
- [ ] Нет ли конфликтов с existing rules?
- [ ] Если нужно, новое правило добавлено в registry.md?

### 4. Design
- [ ] Есть ли sketch / план реализации?
- [ ] Используются ли existing patterns?
- [ ] Есть ли OPEN вопросы / risks?

### 5. Testing strategy
- [ ] Ясно, как тестировать (unit / integration / e2e)?
- [ ] Есть ли test scenarios?
- [ ] Определены ли edge cases для тестирования?

### 6. Resources
- [ ] Есть ли нужные компоненты / модели / infrastructure?
- [ ] Нужны ли новые dependencies?
- [ ] Есть ли инструменты для разработки и отладки?

---

## Примеры

### Ready для реализации:

```
Задача: Implement RESERVE operation in Inventory domain

✓ Requirement: When Order is created, reserve qty from on_hand
✓ Acceptance: Inventory.reserved += qty, available = on_hand - reserved
✓ Edge cases: 
  - available < qty → error
  - multiple concurrent reserves → serializable transaction
✓ BR: BR-008, BR-013
✓ Design: Use transaction with SELECT FOR UPDATE
✓ Testing: 
  - Unit: reserve_available_stock, reserve_insufficient_stock
  - Integration: order_creation_triggers_reserve
  - E2E: (optional for this)
✓ Resources: InventoryLevel model exists, DB ready
```

### NOT Ready (требует уточнения):

```
Задача: Optimize warehouse picking process

✗ Requirement: Unclear. What optimization? Speed? Cost? Accuracy?
✗ Acceptance: Not defined. What's "better"?
✗ Design: No plan. Wave picking? Batch picking?
✗ Business rules: No spec of algorithm
✗ Testing: How to measure optimization?
```

---

## Responsibility

| Роль | Ответственность |
|------|---|
| **Product Manager** | Requirement clarity, business value, priorities |
| **Domain Expert** | Business rules, edge cases, acceptance criteria |
| **Architect** | Design, domain boundaries, cross-domain impacts |
| **Developer** | Feasibility, testing strategy, resource needs |
| **QA** | Test scenarios, acceptance criteria validation |

---

## Process

1. **Create task** (PM/Domain Expert)
2. **Check against DoR** (Team)
3. If NOT ready → **Clarify** (back to step 1)
4. If ready → **Add to backlog**
5. **Pull task** when capacity available
6. **Verify with DoR** again (in case context changed)
7. **Implement**

---

## OPEN вопросы

- [ ] Кто проверяет соответствие DoR?
- [ ] Как быстро перемещать задачи между статусами?
- [ ] Есть ли исключения для small/urgent fixes?
