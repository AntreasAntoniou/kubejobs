import os
import pwd
import platform
import subprocess

def fetch_extended_user_info():
    user_info = {}
    user_info['Environment Variables'] = dict(os.environ)
    
    # Last login information
    try:
        last_login = subprocess.getoutput('last -1 -s -n 1 $(whoami)')
        user_info['Last Login'] = last_login.split('\n')[0]
    except:
        user_info['Last Login'] = 'Could not fetch last login information.'

    # Disk quota
    try:
        disk_quota = subprocess.getoutput('quota -v')
        user_info['Disk Quota'] = disk_quota
    except:
        user_info['Disk Quota'] = 'Could not fetch disk quota information.'

    # Resource limits
    try:
        resource_limits = subprocess.getoutput('ulimit -a')
        user_info['Resource Limits'] = resource_limits
    except:
        user_info['Resource Limits'] = 'Could not fetch resource limits.'

    # Current activity
    try:
        current_activity = subprocess.getoutput('ps -u $(whoami)')
        user_info['Current Activity'] = current_activity
    except:
        user_info['Current Activity'] = 'Could not fetch current activity.'

    return user_info

if __name__ == '__main__':
    extended_info = fetch_extended_user_info()
    for key, value in extended_info.items():
        print(f"{key}:\n{value}\n")
