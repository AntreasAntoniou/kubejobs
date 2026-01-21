delete_jobs_with_string_in_name() {
    kubectl get jobs | grep "$1" | awk '{print $1}' | xargs kubectl delete job
}
