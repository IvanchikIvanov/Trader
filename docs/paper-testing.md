# Как тестировать стратегию **без депозита**

Три уровня — от простого к «как в бою». **Ни один не требует денег на бирже.**

| Уровень | Что это | Деньги | Нужны ключи? |
|---------|---------|--------|--------------|
| **1. Бэктест** | Прогон крючков по **истории** OHLCV | Виртуальный equity | **Нет** (публичные свечи Binance) |
| **2. Paper live** | Сигналы «сейчас» без ордеров (лог / алерты) | Нет | Обычно нет |
| **3. Demo / testnet** | Ордера на **тестовой** бирже | Фейковые | Testnet keys (не mainnet) |

Сейчас в репо реализован **уровень 1** (paper backtest).

---

## 1. Быстрый старт (бэктест)

### Установка

```bash
cd C:\devices\trader
python -m pip install -r requirements.txt
```

### Прогон BTC за 30 дней

```bash
python -m trader backtest --symbol BTCUSDT --days 30
```

### ETH + свой риск + CSV + график

```bash
python -m trader backtest --symbol ETHUSDT --days 60 --risk-pct 0.005 --rr 2 --csv-out data/eth_trades.csv --open
```

После прогона — **TradingView-style HTML** (Lightweight Charts):

- свечи как в TV (тёмная тема, крест, зум скроллом, drag)  
- ▲ long / ▼ short / ● exit  
- price lines: stop/liq и TP  
- volume + equity снизу  
- **время на оси — Москва (MSK)**  
- таблица сделок под графиком  

Файлы: `charts/btcusdt_7d.html` и т.п.

```bash
python -m trader backtest --symbol BTCUSDT --days 7 --stake 30 --leverage 10 --open
python -m trader backtest --symbol ETHUSDT --days 7 --chart-bars 400 --open
```

| Флаг | Смысл | Default |
|------|--------|---------|
| `--symbol` | `BTCUSDT` / `ETHUSDT` | BTCUSDT |
| `--days` | История назад | 30 |
| `--equity` | Стартовый **бумажный** депозит | 10000 |
| `--risk-pct` | Риск на сделку (0.005 = 0.5%) | 0.005 |
| `--rr` | Цель в R (2 = 1:2) | 2 |
| `--no-htf` | Без фильтра 1h/4h bias | off |
| `--csv-out` | Сохранить сделки | — |
| `--chart PATH` | HTML-график (если не указан — auto в `charts/`) | auto |
| `--chart-bars N` | Рисовать только последние N баров 15m | all |
| `--open` | Открыть график в браузере | off |

Данные: **Binance USDT-M futures public API** — без API key и без депозита.

### Unit-тесты (без сети)

```bash
# PowerShell — отключает сломанные global pytest plugins (web3 и т.п.)
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
python -m pytest tests/ -q
```

---

## 2. Что именно симулируется

По `docs/trading-brief.md`:

1. Качает 15m / 1h / 4h.  
2. Ищет **long hook** (1–3 red после high) и **short hook** (1–3 green после low).  
3. Bias 1h/4h (SMA) — long только при up, short при down.  
4. Вход на **close** крюка, SL за extreme крюка, TP = entry ± `rr` × risk.  
5. Equity виртуальный; размер позиции = `(equity × risk%) / (entry − stop)`.

**Ограничения v0 (важно):**

- Нет комиссий / funding / проскальзывания (или упрощены).  
- HTF bias — SMA, не полный HH/HL structure engine.  
- Partial take и trailing пока не в движке (только full TP/SL).  
- Один символ за запуск; один open position.  
- Прошлое ≠ будущее — edge может исчезнуть.

Это **исследование**, не гарантия профита.

---

## 3. Как читать результат

```
trades: 12
win_rate: 0.42
avg_r: 0.35
ending_equity: 10120
return_pct: 1.2
```

| Метрика | На что смотреть |
|---------|------------------|
| `trades` | Мало сделок → мало статистики; расширь `--days` |
| `win_rate` | При R:R 1:2 достаточно ~35–40%+ при стабильном avg R |
| `avg_r` | Главное: средний R после всех SL/TP |
| `return_pct` | На paper equity; не путать с live |

Смотри последние сделки: нет ли серии SL на боковике → ужесточить bias / фильтры.

---

## 4. Уровень 2 — paper «сейчас» (позже)

Когда бэктест устраивает:

1. Раз в 15m (после close свечи) качать последние бары.  
2. Если сигнал — **лог + алерт** (Telegram), **не** ордер.  
3. Ты сам решаешь, входить ли на demo/live.

Пока можно вручную:  
`python -m trader backtest --symbol BTCUSDT --days 3`  
и смотреть, были ли сигналы «вчера–сегодня».

---

## 5. Уровень 3 — testnet (фейковые ордера)

1. Binance / Bybit **Futures Testnet** — отдельные ключи.  
2. Ключи только в `.env` (никогда в git).  
3. Bot шлёт order на testnet; risk как в brief.  
4. Live mainnet — **только** после human gate.

Сейчас testnet-клиент **не** подключён — сначала стабилизируем детектор + бэктест.

---

## 6. Оптимальный порядок работы

```
1. pytest                          # логика крючка не сломана
2. backtest BTC 30–90d             # есть ли вообще сделки / R
3. backtest ETH                    # тот же edge?
4. Зафиксировать risk % / buffer   # в trading-brief.md
5. Улучшить bias (HH/HL)           # меньше ложных hooks
6. Paper alerts 2 недели           # без ордеров
7. Testnet                         # с фейковыми ордерами
8. Live micro                      # human only, tiny size
```

---

## 7. Безопасность

- Не вставляй mainnet API keys «для теста».  
- Public klines = read-only рынок, **ордеров нет**.  
- Loops/agents: `docs/trading-brief.md` + `loop-constraints.md` — paper only.

---

## 8. Частые вопросы

**Нужен ли Binance-аккаунт?**  
Нет, для бэктеста достаточно публичного HTTP.

**Это те же свечи, что на фьючах?**  
Да, endpoint `fapi.binance.com` (USDT-M). Другая биржа → другой адаптер данных.

**Почему сделок 0?**  
Мало дней, жёсткий HTF filter (`--no-htf` для диагностики), или на участке не было чистых 1–3 candle hooks.

**Как добавить комиссии?**  
Следующий шаг в `backtest.py` — fee bps на entry/exit; пока результаты **оптимистичны**.
