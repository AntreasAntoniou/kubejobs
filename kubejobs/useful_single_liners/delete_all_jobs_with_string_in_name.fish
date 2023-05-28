function delete_jobs_with_string_in_name
    kubectl get jobs | grep $argv[1] | awk '{print $1}' | xargs kubectl delete job
end
