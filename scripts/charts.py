"""Fetch KTV play charts (HOLIDAY KTV, Cashbox) and write charts.json for the KTV mode."""
import json, os, re, urllib.request, datetime, html

PAGES = {
    "zh": ("國語點播", "https://www.holiday.com.tw/SongInfo/SongList.aspx?st=top&lt=tc"),
    "tw": ("台語點播", "https://www.holiday.com.tw/SongInfo/SongList.aspx?st=top&lt=tt"),
    "cb": ("錢櫃排行", "https://www.cashboxparty.com/Music/KTVMusic.aspx"),
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KTV chart updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    for enc in ("utf-8", "big5", "cp950"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")

def cells(row):
    return [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)]

def parse(page):
    songs = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S | re.I):
        c = [x for x in cells(row) if x]
        if len(c) >= 3 and c[0].isdigit():
            songs.append(c)
    rng = re.search(r"(20\d\d/\d{1,2}/\d{1,2})\s*[~～-]\s*(20\d\d/\d{1,2}/\d{1,2})", page)
    return songs, (rng.group(1) + " – " + rng.group(2)) if rng else ""

def main():
    os.makedirs("raw", exist_ok=True)
    out = {"updated": datetime.datetime.utcnow().strftime("%Y-%m-%d"), "charts": {}}
    for key, (name, url) in PAGES.items():
        try:
            page = fetch(url)
        except Exception as e:
            print(key, "fetch failed:", e)
            continue
        open(f"raw/{key}.html", "w", encoding="utf-8").write(page)
        rows, rng = parse(page)
        print(key, len(page), "chars,", len(rows), "rows,", rng)
        out["charts"][key] = {"name": name, "range": rng, "rows": rows[:60]}
    if out["charts"]:
        json.dump(out, open("charts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
