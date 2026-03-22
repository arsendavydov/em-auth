#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FASTAPI_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

COMPOSE_FILE="docker-compose.local.yml"
SERVICE_NAME="fastapi"

run_in_docker() {
    if ! docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx "$SERVICE_NAME"; then
        echo "❌ Сервис ${SERVICE_NAME} не запущен (docker compose)."
        echo "Запустите из корня проекта: COMPOSE_BAKE=true docker compose -f ${COMPOSE_FILE} up -d"
        echo "Или без Docker: $0 check-local   (venv .venv312 в корне проекта)"
        exit 1
    fi
    # python -m ruff: в образе должен быть пакет ruff (после пересборки с актуальным requirements.txt)
    docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" python -m ruff "$@"
}

run_pyright_docker() {
    docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" python -m pyright src/
}

run_local() {
    local venv_py="${PROJECT_ROOT}/.venv312/bin/python"
    if [[ ! -x "$venv_py" ]]; then
        echo "❌ Не найден ${venv_py}"
        echo "Создайте venv: python3.12 -m venv .venv312 && .venv312/bin/pip install -r requirements.txt"
        exit 1
    fi
    cd "$FASTAPI_ROOT" || exit 1
    case "$1" in
        check)
            echo "🔍 (локально) ruff check..."
            "$venv_py" -m ruff check src/ tests/
            echo "🔍 (локально) ruff format --check..."
            "$venv_py" -m ruff format --check src/ tests/
            echo "🔍 (локально) pyright..."
            "$venv_py" -m pyright src/
            ;;
        fix)
            echo "🔧 (локально) ruff check --fix --unsafe-fixes..."
            "$venv_py" -m ruff check --fix --unsafe-fixes src/ tests/
            echo "✨ (локально) ruff format..."
            "$venv_py" -m ruff format src/ tests/
            ;;
    esac
}

ACTION="${1:-check}"

case "$ACTION" in
    check)
        echo "🔍 Запуск ruff check..."
        run_in_docker check src/ tests/
        echo "🔍 Запуск ruff format --check..."
        run_in_docker format --check src/ tests/
        echo "🔍 Запуск pyright для проверки типов..."
        run_pyright_docker
        echo "✅ Все проверки завершены!"
        ;;
    fix)
        echo "🔧 Запуск ruff check --fix --unsafe-fixes..."
        run_in_docker check --fix --unsafe-fixes src/ tests/
        echo "✨ Запуск ruff format..."
        run_in_docker format src/ tests/
        echo "✅ Линтинг и форматирование завершены!"
        ;;
    check-local)
        run_local check
        echo "✅ Все проверки завершены (локальный .venv312)!"
        ;;
    fix-local)
        run_local fix
        echo "✅ Линтинг и форматирование завершены (локальный .venv312)!"
        ;;
    *)
        echo "Использование: $0 [check|fix|check-local|fix-local]"
        echo ""
        echo "Команды:"
        echo "  check        — в контейнере docker compose (нужен запущенный fastapi и образ с ruff/pyright)"
        echo "  fix          — то же, с автоисправлением и format"
        echo "  check-local  — без Docker: .venv312 в корне проекта"
        echo "  fix-local    — без Docker: правки + format"
        echo ""
        echo "Запуск из корня проекта: ./fastapi/scripts/lint.sh check-local"
        echo "Если в контейнере нет ruff — пересоберите: COMPOSE_BAKE=true docker compose -f ${COMPOSE_FILE} build fastapi"
        exit 1
        ;;
esac
