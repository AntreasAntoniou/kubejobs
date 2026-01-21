kubectl get pods --field-selector=status.phase=Pending -o json | kubectl delete -f -
