"""
Hook-from-screenshot inbox.

User drops chart screenshots → tool stores them and creates pending cards.
An agent (or human) reads the image and fills symbol / TF / side / MSK time into gold CSV.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INBOX_DIR = ROOT / "labels" / "inbox"
SHOTS_DIR = ROOT / "labels" / "screenshots"
CARDS_PATH = ROOT / "labels" / "hook_inbox.jsonl"
GOLD_PATH = ROOT / "labels" / "hooks_gold.csv"

MSK = timezone(timedelta(hours=3))


@dataclass
class HookCard:
    id: str
    image: str  # relative path from repo root
    status: str = "pending"  # pending | labeled | rejected
    symbol: str | None = None
    timeframe: str | None = None
    side: str | None = None  # long | short
    time_msk: str | None = None  # "2026-07-12 05:00"
    time_utc: str | None = None
    label_status: str = "gold"  # gold | reject
    note: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    labeled_at: str | None = None


def ensure_dirs() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "labels").mkdir(parents=True, exist_ok=True)


def _slug(s: str) -> str:
    s = re.sub(r"[^\w.\-]+", "_", s, flags=re.UNICODE)
    return s.strip("_")[:80] or "shot"


def _new_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


def _append_card(card: HookCard) -> None:
    ensure_dirs()
    with CARDS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(card), ensure_ascii=False) + "\n")


def load_cards() -> list[HookCard]:
    if not CARDS_PATH.exists():
        return []
    out: list[HookCard] = []
    for line in CARDS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        out.append(HookCard(**d))
    return out


def save_all_cards(cards: list[HookCard]) -> None:
    ensure_dirs()
    with CARDS_PATH.open("w", encoding="utf-8") as f:
        for c in cards:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")


def ingest_file(
    path: Path,
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
    side: str | None = None,
    note: str = "",
) -> HookCard:
    """Copy one screenshot into screenshots/ and create a pending card."""
    ensure_dirs()
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    cid = _new_id()
    ext = path.suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        ext = ".png"
    parts = [cid]
    if symbol:
        parts.append(_slug(symbol.upper()))
    if side:
        parts.append(side.lower())
    dest_name = "_".join(parts) + ext
    dest = SHOTS_DIR / dest_name
    shutil.copy2(path, dest)

    rel = dest.relative_to(ROOT).as_posix()
    card = HookCard(
        id=cid,
        image=rel,
        symbol=symbol.upper().replace("/", "") if symbol else None,
        timeframe=timeframe,
        side=side.lower() if side else None,
        note=note,
    )
    _append_card(card)
    return card


def ingest_inbox_folder() -> list[HookCard]:
    """Move all images from labels/inbox/ into screenshots + cards."""
    ensure_dirs()
    cards: list[HookCard] = []
    for path in sorted(INBOX_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
            continue
        card = ingest_file(path)
        # remove original from inbox after copy
        try:
            path.unlink()
        except OSError:
            pass
        cards.append(card)
    return cards


def msk_to_utc_iso(time_msk: str) -> str:
    """
    Parse '2026-07-12 05:00' or '12.07.2026 05:00' or '2026-07-12T05:00' as MSK open time.
    """
    raw = time_msk.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            dt = dt.replace(tzinfo=MSK)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse MSK time: {time_msk!r} (use YYYY-MM-DD HH:MM)")


def label_card(
    card_id: str,
    *,
    symbol: str,
    timeframe: str,
    side: str,
    time_msk: str,
    label_status: str = "gold",
    note: str = "",
    write_gold: bool = True,
) -> HookCard:
    """Fill pending card fields and optionally append to hooks_gold.csv."""
    cards = load_cards()
    found: HookCard | None = None
    for c in cards:
        if c.id == card_id:
            found = c
            break
    if found is None:
        raise KeyError(f"card not found: {card_id}")

    utc = msk_to_utc_iso(time_msk)
    found.symbol = symbol.upper().replace("/", "").replace("-", "")
    if not found.symbol.endswith("USDT") and found.symbol.isalpha():
        # SYN → SYNUSDT heuristic optional — keep as given if already full
        pass
    found.timeframe = timeframe
    found.side = side.lower()
    found.time_msk = time_msk
    found.time_utc = utc
    found.label_status = label_status
    if note:
        found.note = note
    found.status = "labeled"
    found.labeled_at = datetime.now(timezone.utc).isoformat()

    save_all_cards(cards)

    if write_gold:
        append_gold_row(found)
    return found


def append_gold_row(card: HookCard) -> None:
    ensure_dirs()
    if not card.symbol or not card.time_utc or not card.side or not card.timeframe:
        raise ValueError("card incomplete for gold CSV")

    header = "symbol,time_utc,side,timeframe,status,user_said_msk,note,screenshot\n"
    if not GOLD_PATH.exists():
        GOLD_PATH.write_text(
            "# Human-labeled hooks (gold set)\n"
            "# time_utc = open of hook candle; user times MSK unless noted\n"
            + header,
            encoding="utf-8",
        )

    # migrate: if old header without screenshot, still append compatible row
    said = card.time_msk or ""
    note = (card.note or "").replace(",", ";").replace("\n", " ")
    line = (
        f"{card.symbol},{card.time_utc},{card.side},{card.timeframe},"
        f"{card.label_status},{said} MSK,{note},{card.image}\n"
    )

    text = GOLD_PATH.read_text(encoding="utf-8")
    # avoid exact duplicate image or same symbol+time
    if card.image in text and card.time_utc in text:
        return
    with GOLD_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def list_pending() -> list[HookCard]:
    return [c for c in load_cards() if c.status == "pending"]


def print_inbox() -> None:
    cards = load_cards()
    if not cards:
        print("Inbox empty. Drop screenshots into labels/inbox/ then:")
        print("  python -m trader hook ingest")
        print("Or: python -m trader hook shot path/to/screen.png")
        return
    print(f"{'ID':<22} {'status':<10} {'symbol':<12} {'tf':<6} {'side':<6} image")
    for c in cards:
        print(
            f"{c.id:<22} {c.status:<10} {(c.symbol or '—'):<12} "
            f"{(c.timeframe or '—'):<6} {(c.side or '—'):<6} {c.image}"
        )
