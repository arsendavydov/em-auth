## Common CI scripts

Здесь будут лежать общие shell-скрипты, которые не зависят от конкретного CI провайдера.

Планируемое содержимое:

- `check-active-provider.sh` — проверка `ACTIVE_CI_PROVIDER` на сервере;
- дополнительные общие проверки для SSH, `kubectl` и deploy guard-логики.
