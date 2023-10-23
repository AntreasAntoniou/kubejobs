import os
import pwd
import grp

def fetch_user_info():
    user_info = {}
    
    # Get the current user name
    user_info['Current User'] = os.getlogin()
    
    # Get user entry from /etc/passwd
    pw_entry = pwd.getpwnam(os.getlogin())
    
    # Extracting home directory and shell from the password entry
    user_info['Home Directory'] = pw_entry.pw_dir
    user_info['Shell'] = pw_entry.pw_shell
    
    # Get group IDs
    group_ids = os.getgrouplist(os.getlogin(), pw_entry.pw_gid)
    
    # Get group names from group IDs
    user_info['Groups'] = [grp.getgrgid(gid).gr_name for gid in group_ids]
    
    return user_info

if __name__ == "__main__":
    info = fetch_user_info()
    for key, value in info.items():
        print(f"{key}: {value}")
