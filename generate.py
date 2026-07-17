#!/usr/bin/env python3
from __future__ import annotations

import ipaddress
import re
import time
import urllib.request
from pathlib import Path

OUTPUT = Path("ultimate-podkop-list.txt")

# Актуальные публичные списки проекта itdoginfo/allow-domains.
# Russia/inside-raw.lst уже включает заблокированные и геоограниченные
# для пользователей из России ресурсы.
SOURCES = [
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst",

    # Сервисные списки добавляются отдельно, потому что часть из них
    # намеренно не входит полностью в Russia inside.
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/telegram.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/discord.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/google_ai.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/google_meet.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/google_play.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/youtube.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/twitter.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/meta.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/tiktok.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/roblox.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/cloudflare.lst",
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/cloudfront.lst",
]

# Только реальные корневые домены сервисов, которые могут отсутствовать
# в исходниках в отдельный момент. Никаких сгенерированных доменов.
REQUIRED_DOMAINS = {
    # Telegram
    "telegram.org", "telegram.me", "t.me", "telegra.ph", "tdesktop.com",
    # Discord
    "discord.com", "discord.gg", "discordapp.com", "discordapp.net",
    "discord.media", "discordcdn.com",
    # Spotify
    "spotify.com", "scdn.co", "spotifycdn.com", "spotifycdn.net", "pscdn.co",
    # OpenAI
    "openai.com", "chatgpt.com", "oaistatic.com", "oaiusercontent.com",
    # Anthropic
    "anthropic.com", "claude.ai", "claude.com",
    # GitHub
    "github.com", "github.io", "githubassets.com", "githubusercontent.com",
    # Developer services
    "docker.com", "docker.io", "npmjs.com", "pypi.org", "pythonhosted.org",
    # Common delivery domains used by included services
    "akamaized.net", "cloudfront.net", "fastly.net", "jsdelivr.net",
}

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9-]{2,63}$"
)

FORBIDDEN_SUFFIXES = (
    ".local", ".localhost", ".lan", ".home", ".internal", ".arpa"
)

def download(url: str, attempts: int = 4) -> str:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ultimate-podkop-list/2.0"},
            )
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 3)
    raise RuntimeError(f"Не удалось скачать {url}: {last_error}")

def normalize(value: str) -> str | None:
    value = value.strip().lower().rstrip(".")
    if not value:
        return None

    # Убираем комментарий и распространённые префиксы форматов правил.
    value = value.split("#", 1)[0].strip()
    value = value.removeprefix("domain:")
    value = value.removeprefix("full:")
    value = value.removeprefix("||")
    value = value.rstrip("^")

    # hosts-формат: 0.0.0.0 example.org
    fields = value.split()
    if len(fields) >= 2:
        try:
            ipaddress.ip_address(fields[0])
            value = fields[1]
        except ValueError:
            value = fields[0]

    # Поддержка wildcard/суффиксной записи.
    value = value.removeprefix("*.").removeprefix(".")

    if "/" in value or ":" in value:
        return None
    if value.endswith(FORBIDDEN_SUFFIXES):
        return None
    if DOMAIN_RE.fullmatch(value):
        return value
    return None

def parse(text: str) -> set[str]:
    result: set[str] = set()
    # Некоторые RAW-файлы отображаются как строки, некоторые как пробелы.
    for token in re.split(r"\s+", text):
        domain = normalize(token)
        if domain:
            result.add(domain)
    return result

def main() -> None:
    domains = set(REQUIRED_DOMAINS)
    successful_sources = 0
    errors: list[str] = []

    for url in SOURCES:
        try:
            parsed = parse(download(url))
            if not parsed:
                raise RuntimeError("источник не содержит распознанных доменов")
            domains.update(parsed)
            successful_sources += 1
            print(f"OK: {url} — {len(parsed)} доменов")
        except Exception as exc:
            errors.append(str(exc))
            print(f"WARNING: {exc}")

    # Основной Russia inside обязателен. Не публикуем пустой/аварийный файл.
    if successful_sources == 0 or len(domains) < 500:
        raise SystemExit(
            "Генерация остановлена: не получен основной набор доменов.\n"
            + "\n".join(errors)
        )

    sorted_domains = sorted(domains)

    header = [
        "# Ultimate Podkop List",
        "# Автоматически обновляемый список доменов для маршрутизации через прокси.",
        "# Источник: itdoginfo/allow-domains (Russia inside + сервисные списки).",
        "# Один домен на строку. Поддомены покрываются правилом domain suffix Podkop.",
        f"# Domains: {len(sorted_domains)}",
        "",
    ]

    OUTPUT.write_text(
        "\n".join(header + sorted_domains) + "\n",
        encoding="utf-8",
    )
    print(f"Создан {OUTPUT}: {len(sorted_domains)} уникальных доменов")

if __name__ == "__main__":
    main()
