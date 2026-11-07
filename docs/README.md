# Документация (публичная)

Краткий набор для GitHub: архитектура, границы доменов, конкурентность и фоновые задачи. Подробные карточки доменов, state machines, ADR и ТЗ в публичный репозиторий не входят.

**Точка входа в проект:** корневой [`README.md`](../README.md).

## Что читать

| Документ | Зачем |
|----------|--------|
| [`context.md`](context.md) | Назначение, домены, инварианты MVP |
| [`01-overview/architecture.md`](01-overview/architecture.md) | Слои, пакеты, границы |
| [`02-domain/domain-map.md`](02-domain/domain-map.md) | Домены и ответственность |
| [`05-data-integrity/concurrency.md`](05-data-integrity/concurrency.md) | Резервы, транзакции, гонки |
| [`06-tech/background-jobs.md`](06-tech/background-jobs.md) | ARQ jobs (as-built) |

## Статусы в документах

| Метка | Смысл |
|-------|--------|
| **IMPLEMENTED** | Есть в коде и подтверждено тестами |
| **PARTIAL** | Часть сценария |
| **PLANNED** | Не в коде MVP |
| **OUT OF SCOPE** | Сознательно не делали |
