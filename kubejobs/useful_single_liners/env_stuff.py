from rich import print
import os
import pwd
import grp

def fetch_role_related_info():
    user_info = {}
    # Checking environment variables
    env_vars = dict(os.environ)
    user_info['Environment Variables'] = {k: v for k, v in env_vars.items() if 'ROLE' in k or 'DEPARTMENT' in k or 'SCHOOL' in k}

    # Checking directory structure
    home_dir = os.path.expanduser("~")
    user_info['Directories in Home'] = [d for d in os.listdir(home_dir) if os.path.isdir(os.path.join(home_dir, d))]

    # Group membership to infer role or department
    user_name = pwd.getpwuid(os.getuid())[0]
    groups = [g.gr_name for g in grp.getgrall() if user_name in g.gr_mem]
    user_info['Group Membership'] = groups

    return user_info

if __name__ == '__main__':
    role_related_info = fetch_role_related_info()
    print("[bold green]Role-Related User Information[/bold green]")
    for key, value in role_related_info.items():
        print(f"{key}: {value}")
