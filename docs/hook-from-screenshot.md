# Крючок со скрина (не строкой)

Ты находишь крючок **на любом графике** → кидаешь **скриншот** → он попадает в базу эталонов.

## Самый простой путь (в чат)

1. Скрин TradingView / биржи (можно со стрелкой на крюк).  
2. **Прикрепи картинку в этот чат.**  
3. Напиши коротко, если нужно: `long` / `short` или «разбери».  
4. Агент:
   - смотрит картинку;
   - сохраняет в `labels/screenshots/`;
   - пишет строку в `labels/hooks_gold.csv` (время **MSK**).

Ничего печатать руками не обязательно, если на скрине видно символ, ТФ и время.

## Через папку (без чата сразу)

1. Файлы → `labels/inbox/`  
2.  
   ```powershell
   $env:PYTHONPATH = "src"
   python -m trader hook ingest
   python -m trader hook list
   ```  
3. Потом в чат: «разбери pending» или card id.

## CLI

```powershell
# один файл
python -m trader hook shot "D:\shots\hype.png" --side long

# все из inbox
python -m trader hook ingest

# список
python -m trader hook list

# после разбора (время MSK = open свечи крюка)
python -m trader hook label 20260713T120000123456 --symbol HYPEUSDT --tf 4h --side long --when "2026-07-16 12:00"
```

## Что агент вытаскивает со скрина

| Поле | Пример |
|------|--------|
| Symbol | BTCUSDT, ETH, SYN, HYPE… |
| TF | 15m, 1h, 4h, 1D |
| Side | long / short |
| Open time | MSK, свеча-крюк |
| Note | стрелка, deep hook, etc. |

## Важно

- По умолчанию время **московское**.  
- Нужна **свеча крюка** (red long / green short), не весь импульс.  
- Paper/labels only — не live.
