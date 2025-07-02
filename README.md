# ADB Time Sync

A Python script to synchronize the time on Android devices connected via ADB with NTP servers. The script uses root shell access to set the device time accurately.

## Features

- **NTP Time Synchronization**: Gets accurate time from multiple NTP servers
- **Root Shell Support**: Uses `rootshell -c` for privileged time setting
- **Multiple Device Support**: Can handle multiple connected ADB devices
- **Verification**: Optional time synchronization verification
- **Error Handling**: Robust error handling and fallback NTP servers
- **Cross-platform**: Works on macOS, Linux, and Windows

## Requirements

- Python 3.6 or higher
- ADB (Android Debug Bridge) installed and in PATH
- Android device with:
  - USB debugging enabled
  - Root access (for time setting)
  - `rootshell` command available

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

# Combine options
python3 adb_time_sync.py --verify --ntp-server pool.ntp.org
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--verify` | Verify time synchronization after setting |
| `--device-id ID` | Specify device ID for multiple devices |
| `--ntp-server SERVER` | Use specific NTP server |
| `--timeout SECONDS` | NTP query timeout (default: 5) |
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
2. **NTP Query**: Queries NTP servers to get accurate UTC time
3. **Time Conversion**: Converts UTC time to local timezone
4. **Root Shell Command**: Uses `rootshell -c "date -s MMDDhhmmYYYY.SS"` to set time
5. **Verification**: Optionally verifies the time was set correctly

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
- Verify `rootshell` command is available on the device
- Check that the device allows time setting via root shell

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
Querying NTP server: time.google.com
Successfully got time from time.google.com: 2024-01-15 10:30:45+00:00
Setting device time to: 2024-01-15 10:30:45-05:00
Running command: adb shell 'rootshell -c "date -s 011510302024.45"'
Time set successfully!
[INFO] Time synchronization completed successfully!
```

### With Verification
```bash
$ python3 adb_time_sync.py --verify --ntp-server pool.ntp.org
ADB Time Sync Script
==================================================
Getting current time from NTP servers...
Querying NTP server: pool.ntp.org
Successfully got time from pool.ntp.org: 2024-01-15 10:30:45+00:00
Setting time on device...
Setting device time to: 2024-01-15 10:30:45-05:00
Running command: adb shell 'rootshell -c "date -s 011510302024.45"'
Time set successfully!
Verifying time synchronization...
Device time: Mon Jan 15 10:30:45 EST 2024
NTP time: 2024-01-15 10:30:45+00:00
Time synchronization verification completed.
Time synchronization completed successfully!
```

## License

This script is provided as-is for educational and development purposes. Use at your own risk.

## Contributing

Feel free to submit issues and enhancement requests! 