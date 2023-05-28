#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ./remove_finalizers.sh <string_to_match>"
  exit 1
fi

match_string="$1"

pvcs_to_update=$(kubectl get pvc --no-headers | awk -v pattern="$match_string" '$0 ~ pattern {print $1}')

for pvc_name in $pvcs_to_update; do
  kubectl patch pvc $pvc_name -p '{"metadata":{"finalizers":[]}}'
  echo "Removed finalizers from PVC: $pvc_name"
done
