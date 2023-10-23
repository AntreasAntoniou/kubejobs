import platform

def get_system_info():
    info = {
        "OS": platform.system(),
        "Release": platform.release(),
        "Version": platform.version(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
    }
    return info

if __name__ == "__main__":
    system_info = get_system_info()
    print(system_info)
