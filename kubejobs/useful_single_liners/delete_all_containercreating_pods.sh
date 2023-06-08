kubectl get pods --field-selector=status.phase=ContainerCreating -o json | kubectl delete -f -
