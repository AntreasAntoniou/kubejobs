import subprocess

import fire


class KubeManager:
    def delete_pvc_with_name(
        self, match_string, workspace_name, user_name="ALL"
    ):
        """Delete PVCs that match the given string, within a given workspace, filtered by user."""
        # Validate input
        if not match_string or not workspace_name:
            print(
                "Usage: delete_pvc_with_name <match_string> <workspace_name> [<user_name>]"
            )
            return False

        # Set the workspace (namespace)
        kubectl_context = ["--namespace", workspace_name]

        get_pvc_command = (
            ["kubectl", "get", "pvc"] + kubectl_context + ["--no-headers"]
        )
        pvcs_output = subprocess.check_output(get_pvc_command).decode().strip()

        # Filter by match_string and optionally by user_name label
        matching_pvcs = [
            line.split()[0]
            for line in pvcs_output.split("\n")
            if match_string in line
        ]

        # If filtering by a specific user, retrieve pods with matching user labels
        if user_name != "ALL":
            for pvc in list(matching_pvcs):
                get_pvc_user_command = (
                    ["kubectl", "get", "pvc", pvc]
                    + kubectl_context
                    + ["-o", "jsonpath={.metadata.labels.eidf/user}"]
                )
                pvc_user = (
                    subprocess.check_output(get_pvc_user_command)
                    .decode()
                    .strip()
                )
                if pvc_user != user_name:
                    matching_pvcs.remove(pvc)

        for pvc in matching_pvcs:
            delete_command = [
                "kubectl",
                "delete",
                "pvc",
                pvc,
            ] + kubectl_context
            subprocess.run(delete_command, check=True)

        return True  # Indicates success

    def delete_all_completed_jobs(self, workspace_name, user_name="ALL"):
        """Delete all completed jobs from a given workspace, filtered by user."""
        if not workspace_name:
            print(
                "Usage: delete_all_completed_jobs <workspace_name> [<user_name>]"
            )
            return False

        kubectl_context = ["--namespace", workspace_name]

        # Get jobs that have completed (1 of 1 completions)
        get_jobs_command = (
            ["kubectl", "get", "jobs"] + kubectl_context + ["--no-headers"]
        )
        jobs_output = (
            subprocess.check_output(get_jobs_command).decode().strip()
        )

        jobs_to_delete = []
        for line in jobs_output.split("\n"):
            columns = line.split()
            if len(columns) >= 2 and columns[1] == "1/1":
                job_name = columns[0]
                jobs_to_delete.append(job_name)

        for job_name in jobs_to_delete:
            # Retrieve job's user label if needed
            if user_name != "ALL":
                get_job_user_command = (
                    ["kubectl", "get", "job", job_name]
                    + kubectl_context
                    + ["-o", "jsonpath={.metadata.labels.eidf/user}"]
                )
                job_user = (
                    subprocess.check_output(get_job_user_command)
                    .decode()
                    .strip()
                )
                if job_user != user_name:
                    continue  # Skip jobs not matching user label

            # Delete the job
            delete_job_command = [
                "kubectl",
                "delete",
                "job",
                job_name,
            ] + kubectl_context
            subprocess.run(delete_job_command, check=True)

        return True


if __name__ == "__main__":
    fire.Fire(KubeManager)
