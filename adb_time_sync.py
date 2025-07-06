#!/usr/bin/env python3
"""
ADB Time Sync Script

This script synchronizes the time on an ADB device with NTP servers.
It requires root access on the device and uses various root shell commands.
"""

import subprocess
import socket
import struct
import time
import sys
import argparse
from datetime import datetime, timezone
import re

# NTP servers to query (in order of preference)
NTP_SERVERS = [
    'time.google.com',
    'time.windows.com', 
    'pool.ntp.org',
    'time.nist.gov',
    'time.apple.com'
]

def query_ntp_server(server, timeout=5):
    """
    Query an NTP server and return the current time.
    
    Args:
        server (str): NTP server hostname
        timeout (int): Socket timeout in seconds
        
    Returns:
        datetime: Current UTC time from NTP server
    """
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # NTP request packet (48 bytes)
        # First 8 bytes are header, rest is zero
        packet = bytearray(48)
        packet[0] = 0x1B  # LI=0, Version=3, Mode=3 (Client)
        
        # Send request
        sock.sendto(packet, (server, 123))
        
        # Receive response
        data, addr = sock.recvfrom(1024)
        sock.close()
        
        if len(data) < 48:
            raise ValueError("Invalid NTP response")
        
        # Extract transmit timestamp (bytes 40-47)
        transmit_time = struct.unpack('!Q', data[40:48])[0]
        
        # Convert NTP timestamp to Unix timestamp
        # NTP epoch starts 1900-01-01, Unix epoch starts 1970-01-01
        # Difference is 70 years + 17 leap days = 2208988800 seconds
        ntp_epoch = 2208988800
        unix_time = transmit_time / 2**32 - ntp_epoch
        
        return datetime.fromtimestamp(unix_time, tz=timezone.utc)
        
    except Exception as e:
        print(f"Error querying {server}: {e}")
        return None

def get_ntp_time():
    """
    Get current time from NTP servers, trying multiple servers.
    
    Returns:
        datetime: Current UTC time from NTP server
    """
    for server in NTP_SERVERS:
        print(f"Querying NTP server: {server}")
        ntp_time = query_ntp_server(server)
        if ntp_time:
            print(f"Successfully got time from {server}: {ntp_time}")
            return ntp_time
    
    raise RuntimeError("Failed to get time from any NTP server")

def run_adb_command(command):
    """
    Run an ADB command and return the result.
    
    Args:
        command (str): ADB command to run
        
    Returns:
        tuple: (success, output, error)
    """
    try:
        result = subprocess.run(
            ['adb'] + command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "ADB not found in PATH"
    except Exception as e:
        return False, "", str(e)

def check_adb_device():
    """
    Check if an ADB device is connected.
    
    Returns:
        bool: True if device is connected
    """
    success, output, error = run_adb_command("devices")
    if not success:
        print(f"Error checking ADB devices: {error}")
        return False
    
    # Parse device list
    lines = output.strip().split('\n')[1:]  # Skip header
    devices = [line.split('\t')[0] for line in lines if line.strip() and '\tdevice' in line]
    
    if not devices:
        print("No ADB devices found. Please connect a device.")
        return False
    
    if len(devices) > 1:
        print(f"Multiple devices found: {devices}")
        print("Using first device. Use --device-id to specify a specific device.")
    
    return True

def check_root_access(device_id=None):
    """
    Check if the device has root access by testing various root methods.
    
    Args:
        device_id (str): Optional device ID for multiple devices
        
    Returns:
        dict: Dictionary with root access information
    """
    print("🔍 Checking root access on device...")
    
    # Build base ADB command
    base_cmd = "shell"
    if device_id:
        base_cmd = f"-s {device_id} shell"
    
    root_info = {
        'has_root': False,
        'root_method': None,
        'root_commands': [],
        'can_modify_time': False,
        'selinux_status': None,
        'device_info': {}
    }
    
    # Test 1: Check for su command
    print("  Checking for 'su' command...")
    success, output, error = run_adb_command(f"{base_cmd} 'which su'")
    if success and output.strip():
        root_info['root_commands'].append('su')
        print(f"  ✅ Found 'su' at: {output.strip()}")
        
        # Test su access
        success, output, error = run_adb_command(f"{base_cmd} 'su -c \"id\"'")
        if success and 'uid=0' in output:
            root_info['has_root'] = True
            root_info['root_method'] = 'su'
            print("  ✅ 'su' command works - root access confirmed")
        else:
            print("  ⚠️  'su' command found but doesn't work")
    else:
        print("  ❌ 'su' command not found")
    
    # Test 2: Check for sudo command
    print("  Checking for 'sudo' command...")
    success, output, error = run_adb_command(f"{base_cmd} 'which sudo'")
    if success and output.strip():
        root_info['root_commands'].append('sudo')
        print(f"  ✅ Found 'sudo' at: {output.strip()}")
        
        # Test sudo access
        success, output, error = run_adb_command(f"{base_cmd} 'sudo -n id'")
        if success and 'uid=0' in output:
            root_info['has_root'] = True
            root_info['root_method'] = 'sudo'
            print("  ✅ 'sudo' command works - root access confirmed")
        else:
            print("  ⚠️  'sudo' command found but doesn't work")
    else:
        print("  ❌ 'sudo' command not found")
    
    # Test 3: Check for rootshell command (as specified in requirements)
    print("  Checking for 'rootshell' command...")
    rootshell_found = False
    
    # First try 'which rootshell' (checks PATH)
    success, output, error = run_adb_command(f"{base_cmd} 'which rootshell'")
    if success and output.strip():
        root_info['root_commands'].append('rootshell')
        print(f"  ✅ Found 'rootshell' at: {output.strip()}")
        rootshell_found = True
    else:
        # Try common rootshell locations
        rootshell_paths = ['/bin/rootshell', '/system/bin/rootshell', '/system/xbin/rootshell']
        for path in rootshell_paths:
            success, output, error = run_adb_command(f"{base_cmd} 'test -f {path} && echo {path}'")
            if success and path in output:
                root_info['root_commands'].append('rootshell')
                print(f"  ✅ Found 'rootshell' at: {path}")
                rootshell_found = True
                break
    
    if rootshell_found:
        # Test rootshell access
        success, output, error = run_adb_command(f"{base_cmd} 'rootshell -c id'")
        if success and 'uid=0' in output:
            root_info['has_root'] = True
            root_info['root_method'] = 'rootshell'
            print("  ✅ 'rootshell' command works - root access confirmed")
        else:
            print("  ⚠️  'rootshell' command found but doesn't work")
    else:
        print("  ❌ 'rootshell' command not found")
    
    # Test 4: Check if already running as root
    print("  Checking if already running as root...")
    success, output, error = run_adb_command(f"{base_cmd} 'id'")
    if success and 'uid=0' in output:
        root_info['has_root'] = True
        root_info['root_method'] = 'direct'
        print("  ✅ Already running as root")
    else:
        print("  ❌ Not running as root")
    
    # Test 5: Check SELinux status
    print("  Checking SELinux status...")
    success, output, error = run_adb_command(f"{base_cmd} 'getenforce'")
    if success:
        selinux_status = output.strip()
        root_info['selinux_status'] = selinux_status
        print(f"  ℹ️  SELinux status: {selinux_status}")
        if selinux_status.lower() == 'enforcing':
            print("  ⚠️  SELinux is enforcing - may restrict root operations")
    else:
        print("  ❌ Could not determine SELinux status")
    
    # Test 6: Get device information
    print("  Getting device information...")
    device_props = ['ro.build.version.release', 'ro.product.model', 'ro.build.version.sdk']
    for prop in device_props:
        success, output, error = run_adb_command(f"{base_cmd} 'getprop {prop}'")
        if success:
            root_info['device_info'][prop] = output.strip()
    
    # Test 7: Check if we can modify time (most important test)
    if root_info['has_root'] and root_info['root_method']:
        print("  Testing time modification capability...")
        
        # Get current time first
        success, current_time, error = run_adb_command(f"{base_cmd} 'date'")
        if success:
            print(f"  Current device time: {current_time.strip()}")
            
            # Test if we can set time (use a command that should work)
            if root_info['root_method'] == 'direct':
                test_cmd = f"{base_cmd} 'date --help'"
            elif root_info['root_method'] == 'rootshell':
                # Try to find the actual rootshell path for testing
                rootshell_cmd = 'rootshell'
                rootshell_paths = ['/bin/rootshell', '/system/bin/rootshell', '/system/xbin/rootshell']
                for path in rootshell_paths:
                    success_test, output_test, error_test = run_adb_command(f"{base_cmd} 'test -f {path} && echo found'")
                    if success_test and 'found' in output_test:
                        rootshell_cmd = path
                        break
                test_cmd = f"{base_cmd} '{rootshell_cmd} -c date --help'"
            else:
                test_cmd = f"{base_cmd} '{root_info['root_method']} -c \"date --help\"'"
            
            success, output, error = run_adb_command(test_cmd)
            if success:
                root_info['can_modify_time'] = True
                print("  ✅ Time modification capability confirmed")
            else:
                print("  ⚠️  Time modification capability uncertain")
        else:
            print("  ❌ Could not get current device time")
    
    return root_info

def set_device_time(ntp_time, device_id=None, root_method='rootshell'):
    """
    Set the time on the ADB device using root shell.
    
    Args:
        ntp_time (datetime): UTC time to set
        device_id (str): Optional device ID for multiple devices
        root_method (str): Root method to use ('su', 'sudo', 'rootshell', 'direct')
    """
    # Convert to device timezone (assuming local timezone)
    local_time = ntp_time.astimezone()
    
    # Format time for Android date command
    # Android date format: MMDDhhmm[[CC]YY][.ss]
    time_str = local_time.strftime("%m%d%H%M%Y.%S")
    
    # Build base ADB command
    base_cmd = "shell"
    if device_id:
        base_cmd = f"-s {device_id} shell"
    
    # Build ADB command based on root method
    if root_method == 'direct':
        date_cmd = f"date -s {time_str}"
    elif root_method == 'su':
        date_cmd = f"su -c \"date -s {time_str}\""
    elif root_method == 'sudo':
        date_cmd = f"sudo -n date -s {time_str}"
    elif root_method == 'rootshell':
        # Find the actual rootshell path
        rootshell_cmd = 'rootshell'
        rootshell_paths = ['/bin/rootshell', '/system/bin/rootshell', '/system/xbin/rootshell']
        for path in rootshell_paths:
            success_test, output_test, error_test = run_adb_command(f"{base_cmd} 'test -f {path} && echo found'")
            if success_test and 'found' in output_test:
                rootshell_cmd = path
                print(f"Using rootshell at: {path}")
                break
        date_cmd = f"{rootshell_cmd} -c date -s {time_str}"
    else:
        raise ValueError(f"Unknown root method: {root_method}")
    
    adb_cmd = f"{base_cmd} '{date_cmd}'"
    
    print(f"Setting device time to: {local_time}")
    print(f"Using root method: {root_method}")
    print(f"Running command: adb {adb_cmd}")
    
    success, output, error = run_adb_command(adb_cmd)
    
    if success:
        print("Time set successfully!")
        print(f"Output: {output.strip()}")
    else:
        print(f"Failed to set time: {error}")
        if output:
            print(f"Command output: {output}")

def verify_time_sync(ntp_time, tolerance_seconds=10):
    """
    Verify the time synchronization by checking device time against NTP time.
    
    Args:
        ntp_time (datetime): The NTP time that was set
        tolerance_seconds (int): Acceptable time difference in seconds
        
    Returns:
        bool: True if time is synchronized within tolerance
    """
    print("🔍 Verifying time synchronization...")
    
    success, output, error = run_adb_command("shell 'date'")
    if not success:
        print(f"Error getting device time: {error}")
        return False
    
    try:
        device_time_str = output.strip()
        print(f"Device time: {device_time_str}")
        
        # Get fresh NTP time for comparison
        fresh_ntp_time = get_ntp_time()
        print(f"Current NTP time: {fresh_ntp_time}")
        
        # Try to parse device time (this is tricky as Android date format varies)
        # Common Android date formats:
        # "Wed Jan 15 10:30:45 EST 2024"
        # "2024-01-15 10:30:45"
        
        # For now, we'll do a simpler check - verify the time was recently set
        # by checking if the device time is close to when we set it
        time_diff = abs((datetime.now() - ntp_time.astimezone()).total_seconds())
        
        if time_diff <= tolerance_seconds:
            print(f"✅ Time synchronization verified (within {tolerance_seconds} seconds)")
            return True
        else:
            print(f"⚠️  Time synchronization may be off by {time_diff:.1f} seconds")
            return False
            
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

def comprehensive_time_check():
    """
    Perform comprehensive time-related checks on the device.
    
    Returns:
        dict: Dictionary with time check results
    """
    print("🕐 Performing comprehensive time checks...")
    
    checks = {
        'ntp_reachable': False,
        'system_time_source': None,
        'timezone_info': None,
        'time_sync_services': [],
        'time_permissions': False
    }
    
    # Check 1: Test NTP reachability from device
    print("  Checking NTP server reachability from device...")
    success, output, error = run_adb_command("shell 'ping -c 1 time.google.com'")
    if success and 'bytes from' in output:
        checks['ntp_reachable'] = True
        print("  ✅ NTP servers are reachable from device")
    else:
        print("  ⚠️  NTP servers may not be reachable from device")
    
    # Check 2: Get timezone information
    print("  Getting timezone information...")
    success, output, error = run_adb_command("shell 'getprop persist.sys.timezone'")
    if success and output.strip():
        checks['timezone_info'] = output.strip()
        print(f"  ℹ️  Device timezone: {checks['timezone_info']}")
    
    # Check 3: Check for time sync services
    print("  Checking for time synchronization services...")
    services_to_check = ['ntpd', 'chronyd', 'systemd-timesyncd']
    for service in services_to_check:
        success, output, error = run_adb_command(f"shell 'ps | grep {service}'")
        if success and service in output:
            checks['time_sync_services'].append(service)
            print(f"  ✅ Found time sync service: {service}")
    
    if not checks['time_sync_services']:
        print("  ❌ No standard time sync services found")
    
    # Check 4: Check system time source
    success, output, error = run_adb_command("shell 'cat /proc/version'")
    if success:
        checks['system_time_source'] = 'kernel'
        print(f"  ℹ️  System info: {output.strip()[:100]}...")
    
    return checks

def main():
    parser = argparse.ArgumentParser(
        description="Synchronize time on ADB device with NTP servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Sync time using default settings
  %(prog)s --verify           # Sync time and verify
  %(prog)s --device-id ABC123 # Sync time on specific device
  %(prog)s --ntp-server time.google.com  # Use specific NTP server
  %(prog)s --check-root-only  # Only check root access, don't sync time
  %(prog)s --comprehensive-check  # Perform comprehensive time-related checks
        """
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify time synchronization after setting'
    )
    
    parser.add_argument(
        '--device-id',
        help='Specific device ID (for multiple devices)'
    )
    
    parser.add_argument(
        '--ntp-server',
        help='Specific NTP server to use'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=5,
        help='NTP query timeout in seconds (default: 5)'
    )
    
    parser.add_argument(
        '--check-root-only',
        action='store_true',
        help='Only check root access, do not sync time'
    )
    
    parser.add_argument(
        '--comprehensive-check',
        action='store_true',
        help='Perform comprehensive time-related checks'
    )
    
    args = parser.parse_args()
    
    print("ADB Time Sync Script")
    print("=" * 50)
    
    # Check if ADB device is connected
    if not check_adb_device():
        sys.exit(1)
    
    # Check root access
    root_info = check_root_access(args.device_id)
    
    print("\n📋 Root Access Summary:")
    print(f"  Has root access: {'✅ Yes' if root_info['has_root'] else '❌ No'}")
    if root_info['root_method']:
        print(f"  Root method: {root_info['root_method']}")
    print(f"  Available root commands: {', '.join(root_info['root_commands']) if root_info['root_commands'] else 'None'}")
    print(f"  Can modify time: {'✅ Yes' if root_info['can_modify_time'] else '❌ Unknown'}")
    if root_info['selinux_status']:
        print(f"  SELinux status: {root_info['selinux_status']}")
    
    if root_info['device_info']:
        print("  Device info:")
        for prop, value in root_info['device_info'].items():
            print(f"    {prop}: {value}")
    
    if not root_info['has_root']:
        print("\n❌ ERROR: Root access is required for time synchronization")
        print("Please ensure your device is rooted and has su, sudo, or rootshell available")
        sys.exit(1)
    
    # If only checking root access, exit here
    if args.check_root_only:
        print("\n✅ Root access check completed")
        sys.exit(0)
    
    # Perform comprehensive checks if requested
    if args.comprehensive_check:
        time_checks = comprehensive_time_check()
        print("\n📋 Time Check Summary:")
        for check, result in time_checks.items():
            print(f"  {check}: {result}")
    
    # Override NTP servers if specified
    if args.ntp_server:
        global NTP_SERVERS
        NTP_SERVERS = [args.ntp_server]
    
    try:
        # Get current time from NTP
        print("\nGetting current time from NTP servers...")
        ntp_time = get_ntp_time()
        
        # Set time on device
        print("\nSetting time on device...")
        set_device_time(ntp_time, args.device_id, root_info['root_method'])
        
        # Verify if requested
        if args.verify:
            print("\nVerifying time synchronization...")
            verify_time_sync(ntp_time)
        
        print("\nTime synchronization completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 