# Ultimate Podkop List

Автоматический список доменов для Podkop, рассчитанный на использование в России.

## Как запустить

1. Создайте публичный репозиторий GitHub.
2. Загрузите в него всё содержимое этого архива, сохранив папку `.github/workflows`.
3. Откройте вкладку **Actions** → **Update Ultimate Podkop List** → **Run workflow**.
4. После выполнения появится файл `ultimate-podkop-list.txt`.
5. В Podkop добавьте URL:

```text
https://raw.githubusercontent.com/ВАШ_ЛОГИН/ВАШ_РЕПОЗИТОРИЙ/main/ultimate-podkop-list.txt
```

Тип списка в Podkop: **Dynamic / URL**, режим — маршрутизация через прокси.

Список ежедневно пересобирается, удаляет дубли и ограничивается 5000 доменами.
Не добавляйте одновременно этот список и `Russia inside`: Ultimate уже включает его источник.
