"""
Mock version of pi_info.py for simulation/testing.
Returns simulated system information values.
"""
import random

# Simulated base values that will vary slightly
_base_cpu_temp = 45.0
_base_ram_total = 1024 * 1024  # 1GB in KB
_base_ram_used = 512 * 1024     # 512MB in KB
_base_cpu_use = 15.0
_base_disk_total = "32G"
_base_disk_used = "16G"
_base_disk_free = "16G"
_base_disk_percent = "50%"

# Return CPU temperature as a character string
def getCPUtemperature():
    # Simulate temperature between 40-50°C with slight variation
    temp = _base_cpu_temp + random.uniform(-2.0, 5.0)
    return f"{temp:.1f}"

# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM
def getRAMinfo():
    # Simulate RAM usage with slight variation
    used = _base_ram_used + random.randint(-50 * 1024, 50 * 1024)
    used = max(0, min(used, _base_ram_total))
    free = _base_ram_total - used
    return [str(_base_ram_total), str(int(used)), str(int(free))]

# Return % of CPU used by user as a character string
def getCPUuse():
    # Simulate CPU usage between 10-20%
    cpu_use = _base_cpu_use + random.uniform(-5.0, 5.0)
    cpu_use = max(0.0, min(100.0, cpu_use))
    return f"{cpu_use:.1f}"

# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used
def getDiskSpace():
    # Return simulated disk space values
    return [_base_disk_total, _base_disk_used, _base_disk_free, _base_disk_percent]

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
        'cpu_temp': cpu_temp,
        'ram': {
            'total': format_memory(ram_total_kb),
            'used': format_memory(ram_used_kb),
            'free': format_memory(ram_free_kb)
        },
        'cpu_use': cpu_use,
        'disk': {
            'total': disk_info[0],
            'used': disk_info[1],
            'free': disk_info[2],
            'percent': disk_info[3]
        }
    }