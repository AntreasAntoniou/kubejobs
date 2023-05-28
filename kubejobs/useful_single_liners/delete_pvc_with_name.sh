#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./delete_pvcs.sh <string_to_match>"
  exit 1
fi

match_string="$1"

kubectl get pvc --no-headers | awk -v pattern="$match_string" '$0 ~ pattern {print $1}' | xargs -r kubectl delete pvc
