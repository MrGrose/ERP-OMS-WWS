# ADR-005: Фоновые задачи через Arq
**Статус:** accepted
**Дата:** 2026-11-07
**Maturity:** mvp
**Capability:** `queue.arq`
## Контекст
Нужна простая очередь на Redis
## Решение
Arq worker + Redis
## Последствия
Плюсы: легковесно, async-native. Минусы: меньше фич чем Celery