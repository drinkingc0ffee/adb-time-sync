# ADB Time Sync

A Python script to synchronize the time on Android devices connected via ADB with NTP servers. The script uses root shell access to set the device time accurately.

## Features

- **NTP Time Synchronization**: Gets accurate time from multiple NTP servers
- **Multi-Root Support**: Automatically detects and uses `su`, `sudo`, `rootshell`, or direct root access
- **Root Access Validation**: Comprehensive root access checking and capability testing
- **Multiple Device Support**: Can handle multiple connected ADB devices
- **Enhanced Verification**: Advanced time synchronization verification with tolerance checking
- **Device Analysis**: Gets device info, timezone, SELinux status, and time sync services
- **Comprehensive Diagnostics**: Optional detailed system analysis and root access diagnostics
- **Error Handling**: Robust error handling and fallback NTP servers
- **Cross-platform**: Works on macOS, Linux, and Windows

## Requirements

- Python 3.6 or higher
- ADB (Android Debug Bridge) installed and in PATH
- Android device with:
  - USB debugging enabled
  - Root access (for time setting)
  - At least one of: `su`, `sudo`, `rootshell`, or direct root access

## Installation

1. Clone or download the scripts to your local machine
2. Make the shell script executable:
   ```bash
   chmod +x adb_time_sync.sh
   ```

## Usage

### Quick Start

Use the shell wrapper for the easiest experience:

```bash
./adb_time_sync.sh
```

### Direct Python Usage

```bash
python3 adb_time_sync.py
```

### Advanced Options

```bash
# Sync time and verify
python3 adb_time_sync.py --verify

# Use specific device (when multiple devices are connected)
python3 adb_time_sync.py --device-id ABC123

# Use specific NTP server
python3 adb_time_sync.py --ntp-server time.google.com

# Set custom timeout
python3 adb_time_sync.py --timeout 10

# Only check root access (diagnostic mode)
python3 adb_time_sync.py --check-root-only

# Perform comprehensive system analysis
python3 adb_time_sync.py --comprehensive-check

# Combine options
python3 adb_time_sync.py --verify --comprehensive-check --ntp-server pool.ntp.org
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--verify` | Verify time synchronization after setting |
| `--device-id ID` | Specify device ID for multiple devices |
| `--ntp-server SERVER` | Use specific NTP server |
| `--timeout SECONDS` | NTP query timeout (default: 5) |
| `--check-root-only` | Only check root access, don't sync time |
| `--comprehensive-check` | Perform comprehensive time-related checks |
| `-h, --help` | Show help message |

## NTP Servers

The script tries multiple NTP servers in order of preference:

1. `time.google.com`
2. `time.windows.com`
3. `pool.ntp.org`
4. `time.nist.gov`
5. `time.apple.com`

## How It Works

1. **Device Detection**: Checks for connected ADB devices
2. **Root Access Check**: Tests for `su`, `sudo`, `rootshell`, or direct root access
3. **System Analysis**: Gets device info, timezone, SELinux status (optional)
4. **NTP Query**: Queries NTP servers to get accurate UTC time
5. **Time Conversion**: Converts UTC time to local timezone
6. **Root Time Setting**: Uses detected root method to set time
7. **Verification**: Optionally verifies the time was set correctly with tolerance checking

## Troubleshooting

### Common Issues

**"No ADB devices found"**
- Ensure USB debugging is enabled on your device
- Check that the device is properly connected
- Run `adb devices` to verify connection

**"ADB not found in PATH"**
- Install Android SDK Platform Tools
- Add ADB to your system PATH

**"Failed to set time"**
- Ensure the device has root access
- Run with `--check-root-only` to diagnose root access issues
- Check that at least one root method (`su`, `sudo`, `rootshell`) is available
- Verify SELinux isn't blocking time changes (check with `--comprehensive-check`)

**"Failed to get time from any NTP server"**
- Check your internet connection
- Try using a specific NTP server with `--ntp-server`
- Increase timeout with `--timeout`

### Debug Mode

For troubleshooting, you can run the script with verbose output:

```bash
python3 -v adb_time_sync.py
```

## Security Notes

- This script requires root access on the Android device
- The `rootshell -c` command executes with elevated privileges
- Only use on devices you own and trust
- Be cautious when setting system time as it can affect system stability

## Examples

### Basic Usage
```bash
$ ./adb_time_sync.sh
[INFO] ADB Time Sync Tool
[INFO] ==================
[INFO] Checking for connected ADB devices...
[INFO] Connected devices:
List of devices attached
ABC123    device
[INFO] Running time synchronization...
🔍 Checking root access on device...
  Checking for 'su' command...
  ✅ Found 'su' at: /system/bin/su
  ✅ 'su' command works - root access confirmed
  Checking for 'sudo' command...
  ❌ 'sudo' command not found
  Checking for 'rootshell' command...
  ❌ 'rootshell' command not found

📋 Root Access Summary:
  Has root access: ✅ Yes
  Root method: su
  Available root commands: su
  Can modify time: ✅ Yes
  SELinux status: Permissive

Getting current time from NTP servers...
Querying NTP server: time.google.com
Successfully got time from time.google.com: 2024-01-15 10:30:45+00:00
Setting device time to: 2024-01-15 10:30:45-05:00
Using root method: su
Running command: adb shell 'su -c "date -s 011510302024.45"'
Time set successfully!
[INFO] Time synchronization completed successfully!
```

### Root Access Check Only
```bash
$ python3 adb_time_sync.py --check-root-only
ADB Time Sync Script
==================================================
🔍 Checking root access on device...
  Checking for 'su' command...
  ✅ Found 'su' at: /system/bin/su
  ✅ 'su' command works - root access confirmed
  Checking for 'sudo' command...
  ❌ 'sudo' command not found
  Checking for 'rootshell' command...
  ✅ Found 'rootshell' at: /system/bin/rootshell
  ✅ 'rootshell' command works - root access confirmed
  Checking if already running as root...
  ❌ Not running as root
  Checking SELinux status...
  ℹ️  SELinux status: Permissive
  Getting device information...
  Current device time: Mon Jan 15 10:25:30 EST 2024
  ✅ Time modification capability confirmed

📋 Root Access Summary:
  Has root access: ✅ Yes
  Root method: su
  Available root commands: su, rootshell
  Can modify time: ✅ Yes
  SELinux status: Permissive
  Device info:
    ro.build.version.release: 11
    ro.product.model: SM-G973F
    ro.build.version.sdk: 30

✅ Root access check completed
```

### Comprehensive Analysis
```bash
$ python3 adb_time_sync.py --comprehensive-check --verify
ADB Time Sync Script
==================================================
🔍 Checking root access on device...
[... root access checks ...]

🕐 Performing comprehensive time checks...
  Checking NTP server reachability from device...
  ✅ NTP servers are reachable from device
  Getting timezone information...
  ℹ️  Device timezone: America/New_York
  Checking for time synchronization services...
  ❌ No standard time sync services found
  ℹ️  System info: Linux version 4.14.117-perf+ (build@build-server) (gcc version 4.9.x-google)...

📋 Time Check Summary:
  ntp_reachable: True
  system_time_source: kernel
  timezone_info: America/New_York
  time_sync_services: []
  time_permissions: False

Getting current time from NTP servers...
[... time sync process ...]
🔍 Verifying time synchronization...
Device time: Mon Jan 15 10:30:45 EST 2024
Current NTP time: 2024-01-15 15:30:47+00:00
✅ Time synchronization verified (within 10 seconds)

Time synchronization completed successfully!
```

## License

This script is provided as-is for educational and development purposes. Use at your own risk.

## Contributing

Feel free to submit issues and enhancement requests! 