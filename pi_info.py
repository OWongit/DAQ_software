import os


# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen("vcgencmd measure_temp").readline()
    return res.replace("temp=", "").replace("'C\n", "")


# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM
def getRAMinfo():
    p = os.popen("free")
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i == 2:
            return line.split()[1:4]


# Return % of CPU used by user as a character string
def getCPUuse():
    return str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip())


# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i == 2:
            return line.split()[1:5]


def get_system_info():
    cpu_temp = getCPUtemperature()
    ram_info = getRAMinfo()
    cpu_use = getCPUuse()
    disk_info = getDiskSpace()

    # Format RAM values (convert KB to MB/GB for display)
    ram_total_kb = int(ram_info[0])
    ram_used_kb = int(ram_info[1])
    ram_free_kb = int(ram_info[2])

    # Convert to MB or GB for display
    def format_memory(kb):
        if kb >= 1024 * 1024:  # >= 1GB
            return f"{kb / (1024 * 1024):.1f}GB"
        else:
            return f"{kb / 1024:.0f}MB"

    return {
        "cpu_temp": cpu_temp,
        "ram": {"total": format_memory(ram_total_kb), "used": format_memory(ram_used_kb), "free": format_memory(ram_free_kb)},
        "cpu_use": cpu_use,
        "disk": {"total": disk_info[0], "used": disk_info[1], "free": disk_info[2], "percent": disk_info[3]},
    }
