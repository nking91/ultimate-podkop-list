#!/usr/bin/env python3
from __future__ import annotations
import re
import urllib.request
from pathlib import Path

OUT = Path("ultimate-podkop-list.txt")
MIN_COUNT = 3000
MAX_COUNT = 5000

SOURCES = [
    # Основной актуальный список для пользователей из РФ
    ("itdog-russia-inside",
     "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst",
     "plain"),

    # Домены, которые блокируются в РФ, и ресурсы с геоограничениями для РФ
    ("refilter-all",
     "https://raw.githubusercontent.com/1andrevich/Re-filter-lists/main/domains_all.lst",
     "plain"),
    ("refilter-community",
     "https://raw.githubusercontent.com/1andrevich/Re-filter-lists/main/community.lst",
     "plain"),

    # V2Fly: востребованные категории и сервисы
    ("v2fly-ai",
     "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/category-ai-!cn",
     "v2fly"),
    ("v2fly-dev",
     "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/category-dev",
     "v2fly"),
    ("v2fly-media",
     "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/category-media",
     "v2fly"),
    ("v2fly-vpn",
     "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/category-vpnservices",
     "v2fly"),
    ("v2fly-anticensorship",
     "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/category-anticensorship",
     "v2fly"),
]

FORCE = {
    # Telegram
    "telegram.org", "t.me", "telegram.me", "telegra.ph", "tdesktop.com",
    "telegram-cdn.org", "telegram.space",
    # Discord
    "discord.com", "discord.gg", "discordapp.com", "discordapp.net",
    "discordcdn.com", "cdn.discordapp.com", "media.discordapp.net",
    # Spotify
    "spotify.com", "scdn.co", "spotifycdn.com", "spotifycdn.net", "pscdn.co",
    "akamaized.net",
    # OpenAI
    "openai.com", "chatgpt.com", "oaistatic.com", "oaiusercontent.com",
    # GitHub
    "github.com", "github.io", "githubusercontent.com", "githubassets.com",
    "raw.githubusercontent.com", "objects.githubusercontent.com",
    # Основные CDN
    "cloudflare.com", "cloudflare-dns.com", "cloudflareinsights.com",
    "workers.dev", "pages.dev", "cdnjs.com", "jsdelivr.net", "unpkg.com",
    "fastly.com", "fastly.net", "akamai.com", "akamaihd.net",
    "akamaized.net", "edgekey.net", "edgesuite.net", "cloudfront.net",
    "amazonaws.com", "azureedge.net", "azurefd.net", "bunny.net",
    "bunnycdn.com", "cdn77.org", "cachefly.net",
}

# Не отправляем через прокси локальные/служебные и российские инфраструктурные зоны целиком.
DROP_SUFFIXES = (
    ".local", ".lan", ".home", ".internal", ".localhost", ".arpa",
)

DOMAIN_RE = re.compile(
    r"^(?:\*\.)?(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}$"
)

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Ultimate-Podkop-List/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="ignore")

def normalize_domain(value: str) -> str | None:
    value = value.strip().lower().rstrip(".")
    value = re.sub(r"^\|\|", "", value)
    value = re.sub(r"\^.*$", "", value)
    value = re.sub(r"^(domain|full):", "", value)
    value = value.split()[0] if value else ""
    if value.startswith("*."):
        value = value[2:]
    if value.startswith("."):
        value = value[1:]
    if not value or any(value.endswith(s) for s in DROP_SUFFIXES):
        return None
    if DOMAIN_RE.match(value):
        return value
    return None

def parse_plain(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "!", ";", "[")):
            continue
        # hosts-формат
        parts = line.split()
        if len(parts) >= 2 and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", parts[0]):
            line = parts[1]
        d = normalize_domain(line)
        if d:
            out.append(d)
    return out

def parse_v2fly(text: str) -> list[str]:
    out = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("include:", "keyword:", "regexp:")):
            continue
        line = line.split("@", 1)[0].split("&", 1)[0].strip()
        d = normalize_domain(line)
        if d:
            out.append(d)
    return out

def main() -> None:
    domains: list[str] = []
    seen: set[str] = set()

    def add(d: str) -> None:
        if d not in seen:
            seen.add(d)
            domains.append(d)

    for d in sorted(FORCE):
        add(d)

    failures = []
    for name, url, fmt in SOURCES:
        try:
            text = fetch(url)
            parsed = parse_v2fly(text) if fmt == "v2fly" else parse_plain(text)
            for d in parsed:
                add(d)
            print(f"{name}: +{len(parsed)}")
        except Exception as e:
            failures.append(f"{name}: {e}")
            print(f"WARNING {name}: {e}")

    # Ограничиваем размер, сохраняя порядок приоритетов источников.
    domains = domains[:MAX_COUNT]

    header = [
        "# Ultimate Podkop List",
        "# Автоматически собранный список доменов для маршрутизации через прокси в РФ.",
        "# Один домен на строку; домен покрывает и его поддомены.",
        f"# Уникальных доменов: {len(domains)}",
        "# Источники: itdoginfo/allow-domains, Re-filter-lists, v2fly/domain-list-community.",
        "# Обновляется ежедневно через GitHub Actions.",
        "",
    ]
    OUT.write_text("\n".join(header + domains) + "\n", encoding="utf-8")

    if len(domains) < MIN_COUNT:
        raise SystemExit(
            f"Получено только {len(domains)} доменов; требуется минимум {MIN_COUNT}. "
            f"Ошибки: {'; '.join(failures) or 'нет'}"
        )
    print(f"Готово: {OUT}, {len(domains)} доменов")

if __name__ == "__main__":
    main()
