# Inbox — кидай сюда скрины крючков

1. Сохрани скрин с TradingView / Bybit / Binance (PNG/JPG).  
2. Положи файл в **эту папку** `labels/inbox/`.  
3. Выполни:

```powershell
cd C:\devices\trader
$env:PYTHONPATH = "src"
python -m trader hook ingest
python -m trader hook list
```

4. **Скинь тот же скрин в чат агенту** (или напиши card id) — агент смотрит картинку и пишет в gold:

```powershell
python -m trader hook label <CARD_ID> --symbol HYPEUSDT --tf 4h --side long --when "2026-07-16 12:00"
```

Время — **open свечи-крюка, Москва (MSK)**.

Либо одной командой без inbox:

```powershell
python -m trader hook shot "C:\Users\...\Desktop\chart.png" --side long
```
