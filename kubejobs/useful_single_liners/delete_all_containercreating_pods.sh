kubectl get pods --namespace informatics --field-selector=status.phase=Pending -o json | kubectl delete -f -
