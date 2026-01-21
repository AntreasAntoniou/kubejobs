kubectl get pods --field-selector=status.phase=Succeeded -o json | kubectl delete -f -
