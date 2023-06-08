kubectl get pods --field-selector=status.phase!=Running,status.phase!=Succeeded
