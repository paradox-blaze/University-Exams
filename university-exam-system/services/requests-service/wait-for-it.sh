#!/usr/bin/env bash
# wait-for-it.sh

host="$1"
port="$2"

shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "Waiting for $host:$port to be ready..."
  sleep 1
done

>&2 echo "$host:$port is up - executing command"
exec $cmd
