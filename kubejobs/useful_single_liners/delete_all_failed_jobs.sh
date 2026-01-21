kubectl get jobs -o json | jq -r '.items[] | select(.status.failed==.spec.completions) | .metadata.name' | xargs kubectl delete job
