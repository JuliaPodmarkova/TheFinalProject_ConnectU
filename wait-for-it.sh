#!/bin/sh
# wait-for-postgres.sh (Упрощенная версия)

set -e

host="$1"
port="$2"

export PGPASSWORD=$POSTGRES_PASSWORD

# Мы просто ждем в цикле, пока psql не сможет подключиться
until psql -h "$host" -p "$port" -U "$POSTGRES_USER" -d "$POSTGRES_DATABASE" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up!"
# Скрипт просто успешно завершается, ничего не выполняя (не используя exec)