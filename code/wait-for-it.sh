#!/bin/bash

until nc -z $1 $2; do
  echo "Waiting for mysql to be ready"
  sleep 10
done
  
echo "Mysql is up"
exec $3