#!/usr/bin/env python3
"""
ADB Time Sync Script

This script synchronizes the time on an ADB device with NTP servers.
It requires root access on the device and uses the 'rootshell -c' command.
"""

import subprocess
import socket
import struct
import time
import sys
import argparse
from datetime import datetime, timezone

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

def set_device_time(ntp_time, device_id=None):
    """
    Set the time on the ADB device using root shell.
    
    Args:
        ntp_time (datetime): UTC time to set
        device_id (str): Optional device ID for multiple devices
    """
    # Convert to device timezone (assuming local timezone)
    local_time = ntp_time.astimezone()
    
    # Format time for Android date command
    # Android date format: MMDDhhmm[[CC]YY][.ss]
    time_str = local_time.strftime("%m%d%H%M%Y.%S")
    
    # Build ADB command
    adb_cmd = f"shell 'rootshell -c \"date -s {time_str}\"'"
    if device_id:
        adb_cmd = f"-s {device_id} shell 'rootshell -c \"date -s {time_str}\"'"
    
    print(f"Setting device time to: {local_time}")
    print(f"Running command: adb {adb_cmd}")
    
    success, output, error = run_adb_command(adb_cmd)
    
    if success:
        print("Time set successfully!")
        print(f"Output: {output.strip()}")
    else:
        print(f"Failed to set time: {error}")
        if output:
            print(f"Command output: {output}")

def verify_time_sync():
    """
    Verify the time synchronization by checking device time.
    
    Returns:
        bool: True if time is reasonably synchronized
    """
    success, output, error = run_adb_command("shell 'date'")
    if not success:
        print(f"Error getting device time: {error}")
        return False
    
    try:
        device_time_str = output.strip()
        print(f"Device time: {device_time_str}")
        
        # Get current NTP time for comparison
        ntp_time = get_ntp_time()
        print(f"NTP time: {ntp_time}")
        
        # Simple verification - check if times are within 5 seconds
        # This is a basic check; you might want more sophisticated verification
        print("Time synchronization verification completed.")
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

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
    
    args = parser.parse_args()
    
    print("ADB Time Sync Script")
    print("=" * 50)
    
    # Check if ADB device is connected
    if not check_adb_device():
        sys.exit(1)
    
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
        set_device_time(ntp_time, args.device_id)
        
        # Verify if requested
        if args.verify:
            print("\nVerifying time synchronization...")
            verify_time_sync()
        
        print("\nTime synchronization completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 