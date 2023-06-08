function delete_pods_with_string_in_name
    kubectl get pods | grep $argv[1] | awk '{print $1}' | xargs kubectl delete pod
end
