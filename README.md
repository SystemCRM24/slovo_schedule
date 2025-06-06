# Приложение для составления расписания занятий

Описание

Mira - 
https://miro.com/welcomeonboard/RW9xVHBNVDJvd09WRUYvS2E4SEg2NlIwNTRTelFyTjg2aGEyMGQrMVlQRUdpZGRuS2VPemlUWVJxMno0bmNuanZuT1cvQ0hlMjR2dUl3bXFKT2llN1BLTXRlNWl0amQ2dVhBRmVSSFdyUUYxbXRMMzFVazFvTlRjVFhPZ0ZIVWxyVmtkMG5hNDA3dVlncnBvRVB2ZXBnPT0hdjE=?share_link_id=583012695472

## TODO

[ ] Доделать мидлеварь для возврата полного трейсбэка ошибки.
[ ] Переписать BatchBuilder под итератор(генератор) и функцию join


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
