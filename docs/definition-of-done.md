# Definition of Done (DoD)

## Статус
**PROPOSED**

## Назначение
Критерии, которым должна соответствовать реализованная задача перед тем, как ее считать завершенной.

---

## Checklist для завершенной задачи

### 1. Code quality
- [ ] Код следует project style guide (Python / TypeScript / SQL conventions)
- [ ] Нет лишних комментариев (только для non-obvious logic)
- [ ] Функции малые и fokused (не более 20 строк идеально)
- [ ] Нет дублирования кода (DRY)
- [ ] Используются existing utilities, не переизобретаем

### 2. Testing
- [ ] Unit tests написаны (для business logic)
- [ ] Integration tests написаны (для endpoints / flows)
- [ ] Все тесты pass локально
- [ ] Code coverage >= 60% (goal: 80%)
- [ ] Edge cases покрыты (if applicable)
- [ ] E2E tests pass (for user-facing features)

### 3. Documentation
- [ ] Docstrings на функциях / классах (если не очевидно)
- [ ] README updated (if new feature)
- [ ] API docs updated (if new endpoint)
- [ ] BR-xxx документированы (если new rules)
- [ ] State machine updated (if new states)
- [ ] Decision document (if major change)

### 4. Database (if applicable)
- [ ] Alembic migration created + tested
- [ ] Constraints added (CHECK, UNIQUE, FK, etc)
- [ ] Indexes added (if needed for performance)
- [ ] Rollback script exists (if needed)

### 5. Business rules compliance
- [ ] Все relevant BR-xxx соблюдены
- [ ] State machines valid (no invalid transitions)
- [ ] Domain boundaries не нарушены
- [ ] Cross-domain flows correct (если applicable)

### 6. Integration
- [ ] Новая фичи не ломает existing features (regression testing)
- [ ] API contracts соответствуют spec (if applicable)
- [ ] Audit log логирует changes (if required)
- [ ] Error handling proper (meaningful error messages)

### 7. Security
- [ ] Input validation (не trust user input)
- [ ] Secrets не в коде (env vars / config service)
- [ ] SQL injection protection (parameterized queries)
- [ ] Authorization checks (user can only access their data)
- [ ] PII protection (if handling personal data)

### 8. Performance
- [ ] Queries optimized (no N+1)
- [ ] Indexes used where needed
- [ ] No unnecessary database round-trips
- [ ] Async operations used (if needed for latency)

### 9. Deployment readiness
- [ ] No breaking changes to API (or migration plan)
- [ ] Backward compatibility (if needed)
- [ ] Feature flag (if needs gradual rollout)
- [ ] Deployment instructions updated
- [ ] Rollback plan exists

### 10. Final verification
- [ ] Manual testing of happy path (on dev/staging)
- [ ] Manual testing of error cases
- [ ] UI responsive (if web component) — desktop + mobile
- [ ] Accessibility check (WCAG AA minimum)
- [ ] Performance acceptable (< 200ms for API, < 3s page load)

---

## By task type

### New domain/feature
- All items above
- + Architecture review (if major)
- + Performance baseline
- + Load testing (if applicable)

### Bug fix
- [ ] Root cause identified
- [ ] Fix addresses root cause, not symptom
- [ ] Regression test added (prevent same bug)
- [ ] Tests pass
- + minimal documentation update

### Refactoring
- [ ] Behavior unchanged (existing tests pass)
- [ ] Code simpler / clearer
- [ ] No performance regression
- + performance improvement documented (if applicable)

### Documentation
- [ ] Clear, accurate, up-to-date
- [ ] Examples working
- [ ] Links valid
- [ ] No typos / grammar errors

---

## Sign-off process

### Before commit/PR
**Developer**: Self-check против DoD  
```
- [ ] All tests pass
- [ ] Code review self
- [ ] No obvious issues
```

### Before merge
**Code Reviewer**: Verify against DoD  
```
- [ ] Tests adequate
- [ ] Business rules met
- [ ] No security issues
- [ ] Performance acceptable
- [ ] Documentation clear
```

### Before deploy
**QA/Release**: Final verification  
```
- [ ] Staging tests pass
- [ ] Performance acceptable
- [ ] No security warnings
- [ ] Rollback plan ready
```

---

## When is NOT done

- ❌ Tests fail (even 1)
- ❌ Breaking change without migration plan
- ❌ Secrets exposed in code
- ❌ No documentation
- ❌ BR-xxx violated
- ❌ Accessibility failed (if public feature)

---

## Examples

### ✓ Done: Order creation endpoint
```
- Unit tests: 4 scenarios (happy, insufficient stock, invalid customer, payment fail)
- Integration test: create order → verify DB state
- E2E test: create via UI → verify order appears in list
- Docstring: explains parameters, return value
- Error handling: meaningful messages
- Audit log: order_created event
- BR-010, BR-012 checked
- No performance issues
```

### ✗ NOT done: Inventory reserve
```
- Unit test fails (race condition in concurrent reserve)
- No integration test
- BR-008 not verified (can reserve > available)
- No documentation
- Audit log missing
→ Send back to development
```

---

## Velocity impact

Tasks that follow DoD:
- Fewer bugs (better testing)
- Easier to maintain (good documentation)
- Faster code review (clear intent)
- Lower onboarding time for new devs
- Predictable quality

---

## OPEN вопросы

- [ ] Кто проверяет DoD (code review)?
- [ ] Есть ли исключения для small fixes?
- [ ] Как автоматизировать DoD checks (linter, CI)?
- [ ] Performance baseline: кто устанавливает?
