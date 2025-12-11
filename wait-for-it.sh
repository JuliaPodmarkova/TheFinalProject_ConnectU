#!/bin/sh


set -e

host="$1"
port="$2"

export PGPASSWORD=$POSTGRES_PASSWORD

until psql -h "$host" -p "$port" -U "$POSTGRES_USER" -d "$POSTGRES_DATABASE" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up!"