"""Screenshot inbox helpers (no network)."""

from pathlib import Path

# minimal 1x1 PNG
_PNG = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
        0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x05, 0xFE, 0xD4, 0xEF, 0x00, 0x00,
        0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
)


def test_msk_to_utc():
    from trader.hook_shot import msk_to_utc_iso

    iso = msk_to_utc_iso("2026-07-12 05:00")
    assert "2026-07-12T02:00:00" in iso


def test_ingest_and_label(tmp_path, monkeypatch):
    import trader.hook_shot as hs
    from trader.hook_shot import ingest_file, label_card

    monkeypatch.setattr(hs, "ROOT", tmp_path)
    monkeypatch.setattr(hs, "INBOX_DIR", tmp_path / "labels" / "inbox")
    monkeypatch.setattr(hs, "SHOTS_DIR", tmp_path / "labels" / "screenshots")
    monkeypatch.setattr(hs, "CARDS_PATH", tmp_path / "labels" / "hook_inbox.jsonl")
    monkeypatch.setattr(hs, "GOLD_PATH", tmp_path / "labels" / "hooks_gold.csv")

    img = tmp_path / "fake.png"
    img.write_bytes(_PNG)

    card = ingest_file(img, side="long")
    assert card.status == "pending"
    assert (tmp_path / card.image).exists()

    labeled = label_card(
        card.id,
        symbol="BTCUSDT",
        timeframe="15m",
        side="long",
        time_msk="2026-07-12 05:00",
        note="test",
    )
    assert labeled.status == "labeled"
    assert "02:00:00" in (labeled.time_utc or "")
    gold = (tmp_path / "labels" / "hooks_gold.csv").read_text(encoding="utf-8")
    assert "BTCUSDT" in gold
