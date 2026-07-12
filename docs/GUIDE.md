# Гайд: как оптимально использовать Trader

Репозиторий: [IvanchikIvanov/Trader](https://github.com/IvanchikIvanov/Trader)

## 1. Что это сейчас

**Trader** — не готовый торговый бот, а **каркас loop engineering** для Grok (и совместимых агентов).

Идея: ты не пишешь агенту каждый раз «посмотри PR / CI / issues». Ты проектируешь **циклы**, которые сами:

1. смотрят репозиторий / CI / issues / PR;
2. пишут приоритеты в state-файлы;
3. (позже, L2+) чинят мелочи в изолированном worktree;
4. всегда эскалируют человеку рискованные вещи (ключи, live-ордера, merge).

| Есть | Пока нет |
|------|----------|
| 7 паттернов + skills | Код стратегии / execution |
| `STATE.md`, budget, constraints | Биржевые API, paper/live |
| Safety для trading-секретов | CI pipeline |
| GitHub `main` | Авто-торговля |

Оптимальный режим: **сначала дисциплина агента и безопасность, потом код трейдера**.

---

## 2. Главные принципы (чтобы не сжечь токены и не сломать прод)

1. **L1 неделю (или дольше)** — только отчёты, без auto-fix и auto-merge.  
2. **Не включать все 7 loops сразу** — максимум 1–2 активных по расписанию.  
3. **Ты читаешь `STATE.md`** после прогона — иначе loop усиливает шум, а не пользу.  
4. **Секреты и live-торговля — только человек** (см. `loop-constraints.md`, `docs/safety.md`).  
5. **Kill switch:** `loop-pause-all` — стоп всех schedulers + запись в High Priority.  
6. **Бюджет week one:** ≤ 300k токенов/день на все loops (`loop-budget.md`).

---

## 3. Карта файлов (что трогать руками)

| Файл | Зачем |
|------|--------|
| `LOOP.md` | Какие cycles включены, cadence, human gates |
| `STATE.md` | Главная «память» Daily Triage — читай каждое утро |
| `*-state.md` | Память остальных паттернов |
| `loop-constraints.md` | Жёсткие правила (binding) |
| `loop-budget.md` | Лимиты runs/tokens |
| `loop-run-log.md` | Журнал: что крутили, исход |
| `docs/safety.md` | Denylist, auto-merge, trading gates |
| `AGENTS.md` | Команды тестов + конвенции для агента |
| `.grok/skills/*` | Навыки, которые loop вызывает |
| `patterns/registry.yaml` | Индекс паттернов для tooling |

---

## 4. Оптимальный порядок включения

```
Неделя 0–1          Неделя 2–3              Когда есть CI/PR
─────────────       ──────────────          ─────────────────
Daily Triage   →    + Changelog             + PR Babysitter (редко)
Issue Triage   →    + Post-Merge            + CI Sweeper (осторожно)
ручной код     →    + Dependency L1         worktree + verifier (L2)
```

| Фаза | Вкл. | Не трогать |
|------|------|------------|
| **A. Bootstrap** | Daily Triage 1×/день | PR/CI loops, auto-fix |
| **B. Код + issues** | + Issue Triage | CI Sweeper |
| **C. После merges** | + Changelog, Post-Merge | unattended L3 |
| **D. deps** | Dependency L1 → L2 patch-only | majors без human |
| **E. PR/CI** | PR Babysitter / CI | cadence &lt; 15m без early-exit |

**Почему так:** PR Babysitter и CI Sweeper — high / very-high token cost. На пустом репо они крутятся впустую и жгут бюджет.

---

## 5. Ежедневный ритуал (15–20 минут)

### Утро

1. Открой `STATE.md` (и при необходимости `issue-triage-state.md`).  
2. Запусти Daily Triage (Grok):

```text
/loop 1d Run loop-triage. Read STATE.md and loop-constraints.md.
Update High Priority and Watch List. No auto-fix. No secrets in state.
```

3. **Прочитай** отчёт:  
   - High Priority — что реально важно сегодня;  
   - Noise — добавь в ignore, если шум повторяется;  
   - поправь ошибки triage вручную (ты остаёшься инженером).  
4. Одну–две задачи из High Priority — в работу (код / issue / PR).  
5. Строка в `loop-run-log.md` (или попроси агента дописать).

### Вечер (по желанию)

- Если появились issues на GitHub — Issue Triage propose-only.  
- `npx @cobusgreyling/loop-audit . --suggest` — раз в неделю, не каждый день.

### Не делай

- Не гоняй CI Sweeper каждые 5 минут «на всякий случай».  
- Не коммить API keys / `.env` (есть `.gitignore` + denylist).  
- Не давай loop право merge в `main`.

---

## 6. Команды и промпты (cheat sheet)

### CLI

```bash
# Готовность harness
npx @cobusgreyling/loop-audit . --suggest

# Оценка стоимости перед расписанием
npx @cobusgreyling/loop-cost --pattern daily-triage --level L1 --cadence 1d
npx @cobusgreyling/loop-cost --pattern pr-babysitter --level L1 --cadence 15m

# Drift state ↔ LOOP
npx @cobusgreyling/loop-sync .

# L2: circuit breaker перед retry
npx @cobusgreyling/loop-context --check --ledger loop-ledger.json
# exit 0 = continue · exit 2 = escalate human

# L2: изолированный fix
npx @cobusgreyling/loop-worktree create --run-id fix-1 --pattern ci-sweeper
npx @cobusgreyling/loop-worktree mark --run-id fix-1 --status rejected
npx @cobusgreyling/loop-worktree cleanup --older-than 24h
```

### Grok `/loop` (копипаста)

**Daily (основной):**
```text
/loop 1d Run loop-triage. Update STATE.md. No auto-fix. Respect loop-constraints.md.
```

**Issues:**
```text
/loop 2h Run issue-triage. Update issue-triage-state.md. Propose labels only. No auto-apply.
```

**Changelog (перед релизом):**
```text
/loop 1d Run changelog-scan since last tag. Draft RELEASE_NOTES_DRAFT.md. Human review only.
```

**Deps (только report):**
```text
/loop 1d Run dependency-triage. Report only. Escalate majors and high-sev CVEs.
```

**PR watch (когда есть open PRs):**
```text
/loop 15m Run pr-review-triage. Update pr-babysitter-state.md. No auto-merge. Report CI/review blockers.
```

**CI (только когда CI реально падает и ты готов смотреть):**
```text
/loop 15m Run ci-triage. Update ci-sweeper-state.md. Report only. No auto-fix week one.
```

**Kill switch (в любой момент):**
```text
loop-pause-all. Pause every scheduled loop. Write reason to STATE.md High Priority. Do not run fixes.
```

---

## 7. Уровни зрелости (L1 → L3)

| Level | Агент делает | Ты делаешь | Когда |
|-------|--------------|------------|--------|
| **L1** | triage, state, draft notes | читаешь, решаешь | **сейчас** |
| **L2** | small fix в worktree + verifier | approve PR / merge | после 5–7 честных L1 runs |
| **L3** | unattended в узком allowlist | мониторинг + kill switch | редко; не для live trading |

Перед L2 чеклист:

- [ ] `STATE.md` после triage выглядит адекватно 3+ дня подряд  
- [ ] В `AGENTS.md` реальные `test` / `lint` команды  
- [ ] Есть CI на GitHub  
- [ ] `loop-verifier` skill используется  
- [ ] Max 3 attempts + `loop-context --check`  
- [ ] Denylist покрывает secrets / wallet / exchange  

**L3 для размещения live-ордеров — не использовать.** Даже L2 не должен трогать execution с реальными ключами.

---

## 8. Как это стыкуется с будущим trading-кодом

Рекомендуемая структура (когда начнёшь писать app):

```text
trader/
  src/                 # стратегия, risk, paper engine
  tests/
  .env.example         # только имена переменных, без значений
  docs/
    GUIDE.md           # этот файл
    safety.md
  LOOP.md / STATE.md   # loops поверх кода
```

Правила для агента в trading-контексте:

| Можно (после L2 checklist) | Нельзя never |
|----------------------------|--------------|
| рефактор risk-checks, тесты | live API keys |
| paper-trading симулятор | auto-size / place real orders |
| docs, backtest harness | правка `.env`, wallet, seeds |
| draft PR с фиксом lint/CI | auto-merge в `main` |

Дополни в `loop-constraints.md` свои правила, например:

- «Не менять default leverage / position size без human»  
- «Любой change в `execution/` → только draft PR + human»  

---

## 9. Git / GitHub workflow

```bash
# локально
git status
git pull origin main
# ...работа...
git add -A
git commit -m "meaningful message"
git push origin main   # или feature branch + PR
```

Оптимально:

1. Фичи — в **feature branch** + PR.  
2. На `main` — только review’ed merges.  
3. После появления PR → можно включить **PR Babysitter L1** (watch).  
4. После CI → **CI Sweeper L1** report-only.  

Remote: `https://github.com/IvanchikIvanov/Trader.git`

---

## 10. Бюджет токенов (ориентиры)

| Паттерн | Реалистично (L1) | Риск пережога |
|---------|------------------|---------------|
| Daily Triage 1d | ~20–50k / day | низкий |
| Issue Triage 2h | растёт с числом issues | средний |
| Changelog 1d | низкий | низкий |
| Dependency 1d | средний | majors в L2 |
| PR Babysitter 15m | **очень высокий** | вкл. только с early-exit |
| CI Sweeper 15m | **very high** | последний |

Правило: если не уверен — **реже cadence**, не «умнее промпт».

```bash
npx @cobusgreyling/loop-cost --pattern <name> --level L1 --cadence 1d
```

---

## 11. Типичные ошибки

| Ошибка | Почему плохо | Как правильно |
|--------|--------------|---------------|
| Включить все 7 loops day one | $ и шум | 1–2 loops |
| Не читать `STATE.md` | loop врёт незамеченно | 5 мин review |
| Auto-fix без CI | ломает main | L1 → CI → L2 worktree |
| Секреты в state/commit | утечка | denylist + `.gitignore` |
| CI every 5m | токен-пожар | 15m+ и early-exit |
| L3 на live trading | реальные деньги | paper only, human gate |

---

## 12. Чеклист «я использую оптимально»

**Каждый день**

- [ ] Один Daily Triage (или ручной `loop-triage`)  
- [ ] Прочитан и подправлен `STATE.md`  
- [ ] Нет секретов в git status  

**Каждую неделю**

- [ ] `loop-audit . --suggest`  
- [ ] Budget vs факт (примерно)  
- [ ] Constraints актуальны под новый код  

**Перед L2**

- [ ] Тесты в `AGENTS.md`  
- [ ] CI green на main  
- [ ] Verifier + worktree + ledger  

**Никогда**

- [ ] Auto-merge без human  
- [ ] Loop с live exchange credentials  
- [ ] Disable tests «чтобы позеленело»  

---

## 13. С чего начать сегодня (30 минут)

1. Открой `LOOP.md` и `loop-constraints.md` — 5 мин.  
2. Запусти Daily Triage (промпт из §6).  
3. Запиши в `STATE.md` 1–3 реальных next step (например: scaffold app, paper engine, CI).  
4. Закоммить state-апдейт, если triage что-то осмысленное написал:

```bash
git add STATE.md loop-run-log.md
git commit -m "chore: first daily triage state"
git push
```

5. Следующий большой шаг проекта — **код трейдера + тесты + CI**; loops начнут давать пользу только после этого.

---

## 14. Дальше по документам

| Док | Когда |
|-----|--------|
| `LOOP.md` | включить/выключить cycle |
| `loop-budget.md` | caps |
| `docs/safety.md` | denylist / incident |
| `loop-constraints.md` | «агент обязан» |
| [Loop Engineering](https://github.com/cobusgreyling/loop-engineering) | теория и patterns |
| [Showcase](https://cobusgreyling.github.io/loop-engineering/) | pattern picker |

---

*Коротко: один loop в день, читай state, не давай агенту ключи и merge, включай дорогие cycles только когда есть CI/PR, trading execution — всегда human gate.*
