#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import threading
import webbrowser
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
import tkinter as tk
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tkinter import messagebox, ttk
from urllib3.util.retry import Retry

DFO_URL = "https://www.dailyfaceoff.com/hockey-player-news"


# ---------- Robust ET timezone (Windows-safe) ----------
def get_et_tz():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("America/New_York")
    except Exception:
        try:
            import tzdata  # noqa: F401
            from zoneinfo import ZoneInfo

            return ZoneInfo("America/New_York")
        except Exception:
            return timezone(timedelta(hours=-4), name="ET")


ET = get_et_tz()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


SESSION = make_session()

# ---------- Team colors ----------
TEAM_COLORS = {
    "Anaheim Ducks": ("#FC4C02", "#000000"),
    "Arizona Coyotes": ("#8C2633", "#E2D6B5"),
    "Boston Bruins": ("#FFB81C", "#000000"),
    "Buffalo Sabres": ("#003087", "#FFB81C"),
    "Calgary Flames": ("#C8102E", "#F1BE48"),
    "Carolina Hurricanes": ("#CC0000", "#000000"),
    "Chicago Blackhawks": ("#CF0A2C", "#000000"),
    "Colorado Avalanche": ("#6F263D", "#236192"),
    "Columbus Blue Jackets": ("#002654", "#CE1126"),
    "Dallas Stars": ("#006847", "#8F8F8C"),
    "Detroit Red Wings": ("#CE1126", "#FFFFFF"),
    "Edmonton Oilers": ("#041E42", "#FF4C00"),
    "Florida Panthers": ("#C8102E", "#B9975B"),
    "Los Angeles Kings": ("#111111", "#A2AAAD"),
    "Minnesota Wild": ("#154734", "#EB8191"),
    "Montréal Canadiens": ("#AF1E2D", "#192168"),
    "Nashville Predators": ("#FFB81C", "#041E42"),
    "New Jersey Devils": ("#CE1126", "#000000"),
    "New York Islanders": ("#003087", "#F47D30"),
    "New York Rangers": ("#0038A8", "#CE1126"),
    "Ottawa Senators": ("#C52032", "#C2912C"),
    "Philadelphia Flyers": ("#F74902", "#000000"),
    "Pittsburgh Penguins": ("#FCB514", "#000000"),
    "San Jose Sharks": ("#006D75", "#EA7200"),
    "Seattle Kraken": ("#001628", "#99D9D9"),
    "St. Louis Blues": ("#002F87", "#FFB81C"),
    "Tampa Bay Lightning": ("#002868", "#FFFFFF"),
    "Toronto Maple Leafs": ("#00205B", "#FFFFFF"),
    "Vancouver Canucks": ("#00205B", "#00843D"),
    "Vegas Golden Knights": ("#B4975A", "#333F42"),
    "Washington Capitals": ("#041E42", "#C8102E"),
    "Winnipeg Jets": ("#041E42", "#7B303E"),
}
ALIASES = {
    "tbl": "Tampa Bay Lightning",
    "lightning": "Tampa Bay Lightning",
    "bolts": "Tampa Bay Lightning",
    "blues": "St. Louis Blues",
    "st louis": "St. Louis Blues",
    "st. louis": "St. Louis Blues",
    "cbj": "Columbus Blue Jackets",
    "blue jackets": "Columbus Blue Jackets",
    "hawks": "Chicago Blackhawks",
    "blackhawks": "Chicago Blackhawks",
    "devils": "New Jersey Devils",
    "islanders": "New York Islanders",
    "rangers": "New York Rangers",
    "habs": "Montréal Canadiens",
    "canadiens": "Montréal Canadiens",
    "montreal": "Montréal Canadiens",
    "knights": "Vegas Golden Knights",
    "golden knights": "Vegas Golden Knights",
    "leafs": "Toronto Maple Leafs",
    "maple leafs": "Toronto Maple Leafs",
    "kraken": "Seattle Kraken",
    "panthers": "Florida Panthers",
    "penguins": "Pittsburgh Penguins",
    "sharks": "San Jose Sharks",
    "oilers": "Edmonton Oilers",
    "flames": "Calgary Flames",
    "red wings": "Detroit Red Wings",
    "senators": "Ottawa Senators",
    "canucks": "Vancouver Canucks",
    "capitals": "Washington Capitals",
    "jets": "Winnipeg Jets",
    "kings": "Los Angeles Kings",
    "stars": "Dallas Stars",
    "wild": "Minnesota Wild",
    "predators": "Nashville Predators",
    "avalanche": "Colorado Avalanche",
    "coyotes": "Arizona Coyotes",
    "ducks": "Anaheim Ducks",
    "sabres": "Buffalo Sabres",
    "bruins": "Boston Bruins",
    "flyers": "Philadelphia Flyers",
    "nyr": "New York Rangers",
    "nyi": "New York Islanders",
    "lak": "Los Angeles Kings",
    "vgk": "Vegas Golden Knights",
    "wsh": "Washington Capitals",
    "sj": "San Jose Sharks",
    "sjs": "San Jose Sharks",
    "mtl": "Montréal Canadiens",
    "bos": "Boston Bruins",
    "phi": "Philadelphia Flyers",
    "wpg": "Winnipeg Jets",
    "van": "Vancouver Canucks",
}
for full in list(TEAM_COLORS):
    ALIASES[full.lower()] = full

SORTED_ALIASES = sorted(ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True)

# ---------- Parsing helpers ----------
SRC_PFX = re.compile(r"^\s*Source\s*[:\-\u2013\u2014\u2022]", re.I)
ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(Z|[+-]\d{2}:\d{2})?")
HUMAN_DT = re.compile(r"[A-Za-z]{3}\s+\d{1,2},?\s*\d{4}", re.I)
HUMAN_TM = re.compile(r"\d{1,2}:\d{2}(?:\s?[APMapm]{2})?")
TZ_TOK = re.compile(r"\b(ET|EDT|EST)\b", re.I)


def normalize_team_text(txt: str | None) -> str | None:
    if not txt:
        return None
    s = txt.strip().lower()
    for alias, full in SORTED_ALIASES:
        if re.search(rf"\b{re.escape(alias)}\b", s):
            return full
    return None


def extract_team_any(*texts) -> str | None:
    blob = " ".join(t for t in texts if t)
    return normalize_team_text(blob)


def parse_ts_from_source_text(txt: str) -> datetime | None:
    if not txt:
        return None

    m = ISO_RE.search(txt)
    if m:
        iso = m.group(0).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(ET)
        except Exception:
            pass

    dm = HUMAN_DT.search(txt)
    tm = HUMAN_TM.search(txt)
    if dm and tm:
        date_str = dm.group(0).replace(",", "").strip()
        time_str = tm.group(0).strip().upper()
        combo = TZ_TOK.sub("", f"{date_str} {time_str}").strip()
        for fmt in ("%b %d %Y %H:%M", "%b %d %Y %I:%M", "%b %d %Y %I:%M %p"):
            try:
                return datetime.strptime(combo, fmt).replace(tzinfo=ET)
            except Exception:
                continue
    return None


def minutes_ago(dt: datetime) -> float:
    now = datetime.now(ET if dt and dt.tzinfo else None)
    return (now - dt).total_seconds() / 60.0


def clean_text(t: str) -> str:
    t = re.sub(r"\s+", " ", (t or "")).strip()
    return t[:220] + "…" if len(t) > 220 else t


# ---------- Exact “Source:” parser (preferred) ----------
def extract_items_from_source_lines(soup: BeautifulSoup):
    items = []
    for p in soup.find_all("p"):
        t = p.get_text(" ", strip=True)
        if not t or not SRC_PFX.match(t):
            continue

        a = p.find("a", href=True)
        src_href = urljoin(DFO_URL, a["href"]) if a else None
        src_text = a.get_text(" ", strip=True) if a else t

        news = ""
        prev = p.previous_sibling
        while prev and not getattr(prev, "name", None):
            prev = prev.previous_sibling

        steps = 0
        while prev and steps < 6:
            if getattr(prev, "name", "") == "p":
                txt = prev.get_text(" ", strip=True)
                if txt and not SRC_PFX.match(txt) and len(txt.split()) > 3:
                    news = txt
                    break
            prev = prev.previous_sibling
            steps += 1
        summary = clean_text(news)

        header = ""
        node = p
        hops = 0
        while node and node.name not in ("body", "html") and hops < 4:
            hdr = node.find_previous(["h1", "h2", "h3", "h4", "h5"])
            if hdr:
                header = clean_text(hdr.get_text(" ", strip=True))
                break
            node = node.parent
            hops += 1
        if not header:
            header = clean_text(summary or src_text)

        ts = parse_ts_from_source_text(t)
        team = extract_team_any(header, src_text) or "Unknown"

        items.append(
            {
                "header": header,
                "summary": summary,
                "team": team if team in TEAM_COLORS else "Unknown",
                "timestamp_et": ts,
                "source_href": src_href,
                "source_text": src_text,
            }
        )
    return items


def extract_items_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    items = extract_items_from_source_lines(soup)

    out, seen = [], set()
    for it in items:
        sig = (it.get("header"), it.get("summary"), it.get("source_href"))
        if sig in seen:
            continue
        seen.add(sig)
        out.append(it)

    def key(it):
        ts = it.get("timestamp_et")
        return ts if isinstance(ts, datetime) else datetime.min.replace(tzinfo=ET)

    out.sort(key=key, reverse=True)
    return out


# ---------- Renderer ----------
def fetch_html_requests(url: str) -> str | None:
    try:
        r = SESSION.get(url, timeout=30)
        if r.ok:
            return r.text
    except requests.RequestException:
        return None
    return None


def fetch_news_cards():
    html = fetch_html_requests(DFO_URL)
    if not html:
        return [], 0, "Request failed"

    items = extract_items_from_html(html)
    return items, len(items), "Requests"


# ---------- GUI ----------
class NewsApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Daily Faceoff · Player News Monitor")
        self.root.configure(bg="#0f172a")
        self.cache_ids = set()
        self.refresh_job = None

        self._build_styles()

        top = ttk.Frame(root, padding=(12, 12, 12, 8), style="Top.TFrame")
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Lookback", style="Label.TLabel").pack(side=tk.LEFT)
        self.lookback_var = tk.StringVar(value="10")
        self.lookback_combo = ttk.Combobox(
            top,
            width=7,
            textvariable=self.lookback_var,
            state="readonly",
            values=["5", "10", "30", "60", "120"],
        )
        self.lookback_combo.pack(side=tk.LEFT, padx=(6, 18))

        ttk.Label(top, text="Auto-refresh", style="Label.TLabel").pack(side=tk.LEFT)
        self.refresh_var = tk.StringVar(value="10")
        self.refresh_combo = ttk.Combobox(
            top,
            width=7,
            textvariable=self.refresh_var,
            state="readonly",
            values=["5", "10", "30", "60", "120"],
        )
        self.refresh_combo.pack(side=tk.LEFT, padx=(6, 18))
        self.refresh_combo.bind("<<ComboboxSelected>>", self._on_refresh_changed)

        ttk.Button(top, text="Retrieve News", command=self.fetch_now, style="Primary.TButton").pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(top, text="Clear", command=self.clear_all).pack(side=tk.LEFT, padx=4)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(root, textvariable=self.status_var, anchor="w", style="Status.TLabel").pack(
            side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8)
        )

        frame_wrap = ttk.Frame(root, style="Top.TFrame")
        frame_wrap.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        self.canvas = tk.Canvas(frame_wrap, borderwidth=0, highlightthickness=0, bg="#0f172a")
        self.scroll_y = ttk.Scrollbar(frame_wrap, orient="vertical", command=self.canvas.yview)
        self.cards_frame = ttk.Frame(self.canvas, style="Top.TFrame")
        self.cards_frame.bind(
            "<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.schedule_refresh()
        self.fetch_now()

    def _build_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("Top.TFrame", background="#0f172a")
        style.configure("Label.TLabel", background="#0f172a", foreground="#dbeafe", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", background="#0f172a", foreground="#93c5fd", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(10, 6))
        style.configure("Primary.TButton", foreground="#0f172a")

    def _ui(self, fn, *args):
        self.root.after(0, lambda: fn(*args))

    def _on_refresh_changed(self, _evt=None):
        self.schedule_refresh(reschedule=True)

    def clear_all(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        self.cache_ids.clear()
        self.status_var.set("Cleared.")

    def fetch_now(self):
        threading.Thread(target=self._do_fetch_thread, daemon=True).start()

    def _do_fetch_thread(self):
        self._ui(self._set_status, "Fetching DailyFaceoff…")
        try:
            cards, found_count, how = fetch_news_cards()
        except Exception as e:
            self._ui(self._set_status, f"Error fetching: {e}")
            return

        self._ui(self._set_status, f"{how}: parsed {found_count} items. Applying lookback…")

        try:
            lookback = int(self.lookback_var.get())
        except Exception:
            lookback = 10

        add_queue = []
        for it in cards:
            ts = it.get("timestamp_et")
            if isinstance(ts, datetime) and minutes_ago(ts) > lookback + 0.5:
                continue

            sig = (it.get("source_href"), it.get("header"), it.get("summary"))
            if sig in self.cache_ids:
                continue
            self.cache_ids.add(sig)
            add_queue.append(it)

        self._ui(self._apply_results, add_queue)

    def _apply_results(self, items):
        for it in items:
            self._add_card(it)
        self._set_status(f"Added {len(items)} item(s)." if items else "No new items for selected lookback.")

    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _open_link(self, url: str):
        if not url:
            messagebox.showinfo("No Link", "No source link found for this item.")
            return
        webbrowser.open_new(url)

    def _add_card(self, item: dict):
        team = item.get("team") or "Unknown"
        bg, fg = TEAM_COLORS.get(team, ("#1f2937", "#f8fafc"))

        outer = tk.Frame(self.cards_frame, bg="#0f172a")
        outer.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)
        card = tk.Frame(outer, bg=bg, bd=0, highlightthickness=1, highlightbackground="#94a3b8")
        card.pack(side=tk.TOP, fill=tk.X)
        inner = tk.Frame(card, bg=bg)
        inner.pack(side=tk.TOP, fill=tk.X, padx=12, pady=12)

        tk.Label(
            inner,
            text=item.get("header", ""),
            bg=bg,
            fg=fg,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            wraplength=1040,
            justify="left",
        ).pack(fill=tk.X)

        if item.get("summary"):
            tk.Label(
                inner,
                text=item["summary"],
                bg=bg,
                fg=fg,
                font=("Segoe UI", 9),
                anchor="w",
                wraplength=1040,
                justify="left",
            ).pack(fill=tk.X, pady=(4, 0))

        footer = tk.Frame(inner, bg=bg)
        footer.pack(fill=tk.X, pady=(8, 0))

        ts = item.get("timestamp_et")
        ts_txt = ts.strftime("%b %d, %Y %H:%M") if isinstance(ts, datetime) else "Unknown"
        tk.Label(footer, text=f"Time (ET): {ts_txt}", bg=bg, fg=fg, font=("Segoe UI", 8)).pack(side=tk.LEFT)
        ttk.Button(footer, text="Open Source", command=lambda u=item.get("source_href"): self._open_link(u)).pack(
            side=tk.RIGHT
        )
        tk.Label(footer, text=team, bg=bg, fg=fg, font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT, padx=(0, 8))

    def schedule_refresh(self, reschedule=False):
        try:
            minutes = int(self.refresh_var.get())
        except Exception:
            minutes = 10
        delay_ms = max(1, minutes) * 60 * 1000

        if reschedule and self.refresh_job is not None:
            try:
                self.root.after_cancel(self.refresh_job)
            except Exception:
                pass
            self.refresh_job = None

        def _tick():
            self.fetch_now()
            self.refresh_job = self.root.after(delay_ms, _tick)

        if self.refresh_job is None:
            self.refresh_job = self.root.after(delay_ms, _tick)


def main():
    root = tk.Tk()
    app = NewsApp(root)
    root.geometry("1120x760")
    root.mainloop()


if __name__ == "__main__":
    main()
