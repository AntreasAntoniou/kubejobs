kubectl get jobs | grep '1/1' | awk '{print $1}' | xargs kubectl delete job
