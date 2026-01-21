kubectl get pods --field-selector=status.phase=Failed -o json | kubectl delete -f -
