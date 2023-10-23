import subprocess
import json
from typing import List, Dict, Union
from rich.console import Console
import fire

console = Console()

def list_resources(resource_type: str, username: str) -> None:
    """
    List Kubernetes resources filtered by resource type and username.
    
    :param resource_type: Type of the Kubernetes resource (e.g., 'pods' or 'jobs').
    :type resource_type: str
    :param username: Username to filter the resources by.
    :type username: str
    :return: None
    """
    try:
        # 🚀 Execute kubectl command to fetch all resources in JSON format
        result = subprocess.run(['kubectl', 'get', resource_type, '--all-namespaces', '-o', 'json'], capture_output=True, text=True)
        
        # 🧠 Parse the JSON output
        resources = json.loads(result.stdout)
        
        # 📦 Placeholder for filtered resources
        filtered_resources: List[Dict[str, Union[str, Dict[str, str]]]] = []

        # 🎯 Filter resources based on the 'username' annotation
        for item in resources['items']:
            annotations = item['metadata'].get('annotations', {})
            if annotations.get('username') == username:
                filtered_resources.append({
                    'namespace': item['metadata']['namespace'],
                    'name': item['metadata']['name'],
                    'username': annotations.get('username'),
                    'timestamp': annotations.get('timestamp'),
                    'host': annotations.get('host')
                })
        
        # 👁️ Pretty display of filtered resources using Rich library
        console.print(f"🔍 Resources of type '{resource_type}' initiated by '{username}':")
        console.print(filtered_resources)

    except subprocess.CalledProcessError as e:
        console.print(f"🚨 An error occurred: {e}", style="bold red")
    except Exception as e:
        console.print(f"🛑 Unexpected error: {e}", style="bold red")

# 🎬 Entry point
if __name__ == '__main__':
    fire.Fire(list_resources)  # 🌈 Google Fire for CLI
