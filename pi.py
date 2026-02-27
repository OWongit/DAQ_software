import subprocess


def getCPUtemperature():
    """Return CPU temperature as a string (e.g. '45.2')."""
    result = subprocess.run(
        ["vcgencmd", "measure_temp"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return ""
    return result.stdout.strip().replace("temp=", "").replace("'C\n", "").replace("'C", "")


def getRAMinfo():
    """Return RAM info (unit=kb) as [total, used, free]."""
    result = subprocess.run(
        ["free"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return ["0", "0", "0"]
    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return ["0", "0", "0"]
    # Second line is "Mem: total used free ..."
    parts = lines[1].split()
    if len(parts) < 4:
        return ["0", "0", "0"]
    return parts[1:4]


def getCPUuse():
    """Return % of CPU used as a string."""
    result = subprocess.run(
        ["top", "-b", "-n1"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return ""
    for line in result.stdout.splitlines():
        if "Cpu(s)" in line or "cpu(s)" in line:
            # Line like "%Cpu(s):  1.2 us,  0.5 sy, ..." - $2 in awk is first number (us %)
            parts = line.split()
            for i in range(1, len(parts)):
                val = parts[i].rstrip(",")
                try:
                    float(val)
                    return val
                except ValueError:
                    continue
            break
    return ""


def getDiskSpace():
    """Return disk space as [total, used, free, percent] (units in output)."""
    result = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return ["", "", "", ""]
    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return ["", "", "", ""]
    parts = lines[1].split()
    if len(parts) < 5:
        return ["", "", "", ""]
    return parts[1:5]


def get_system_info():
    cpu_temp = getCPUtemperature()
    ram_info = getRAMinfo()
    cpu_use = getCPUuse()
    disk_info = getDiskSpace()

    # Format RAM values (convert KB to MB/GB for display)
    try:
        ram_total_kb = int(ram_info[0])
        ram_used_kb = int(ram_info[1])
        ram_free_kb = int(ram_info[2])
    except (ValueError, IndexError):
        ram_total_kb = ram_used_kb = ram_free_kb = 0

    def format_memory(kb):
        if kb >= 1024 * 1024:  # >= 1GB
            return f"{kb / (1024 * 1024):.1f}GB"
        return f"{kb / 1024:.0f}MB"

    return {
        "cpu_temp": cpu_temp,
        "ram": {"total": format_memory(ram_total_kb), "used": format_memory(ram_used_kb), "free": format_memory(ram_free_kb)},
        "cpu_use": cpu_use,
        "disk": {"total": disk_info[0] if len(disk_info) > 0 else "", "used": disk_info[1] if len(disk_info) > 1 else "", "free": disk_info[2] if len(disk_info) > 2 else "", "percent": disk_info[3] if len(disk_info) > 3 else ""},
    }


def reboot_pi():
    """Reboot the Raspberry Pi (requires appropriate system permissions)."""
    try:
        # This command typically requires passwordless sudo for the running user.
        subprocess.run(["sudo", "reboot", "now"], check=False)
    except Exception:
        # If reboot fails, just return; caller can decide how to surface errors.
        return