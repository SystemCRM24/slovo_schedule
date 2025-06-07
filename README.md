# Приложение для составления расписания занятий

Описание

Mira - 
https://miro.com/welcomeonboard/RW9xVHBNVDJvd09WRUYvS2E4SEg2NlIwNTRTelFyTjg2aGEyMGQrMVlQRUdpZGRuS2VPemlUWVJxMno0bmNuanZuT1cvQ0hlMjR2dUl3bXFKT2llN1BLTXRlNWl0amQ2dVhBRmVSSFdyUUYxbXRMMzFVazFvTlRjVFhPZ0ZIVWxyVmtkMG5hNDA3dVlncnBvRVB2ZXBnPT0hdjE=?share_link_id=583012695472

## TODO

[*] Доделать мидлеварь в бэкенде для возврата полного трейсбэка ошибки.
[ ] Переписать BatchBuilder под итератор(генератор) и функцию join
[ ] Избавиться от вложенной структуры данных на фронте
[ ] Кеширование данных для бэка и фронта
[ ] Слабые связи на фронте -> по факту означает переписать весь фронт.


## Запуск

- создать .env файл со следующим содержимым
```
# Общие
MODE="dev"    # dev или prod

# Для Бэкенда
BITRIX_WEBHOOK=""

# Для Фронта
VITE_API_URL=""
VITE_BASE_PATH=""
```
