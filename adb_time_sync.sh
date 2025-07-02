#!/bin/bash
# ADB Time Sync Shell Wrapper
# Quick script to synchronize time on ADB devices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python script exists
if [ ! -f "adb_time_sync.py" ]; then
    print_error "adb_time_sync.py not found in current directory"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if ADB is available
if ! command -v adb &> /dev/null; then
    print_error "ADB is required but not found in PATH"
    print_warning "Please install Android SDK Platform Tools"
    exit 1
fi

# Make Python script executable
chmod +x adb_time_sync.py

print_status "ADB Time Sync Tool"
print_status "=================="

# Check for connected devices
print_status "Checking for connected ADB devices..."
if ! adb devices | grep -q "device$"; then
    print_error "No ADB devices found. Please connect a device and enable USB debugging."
    exit 1
fi

# Show connected devices
print_status "Connected devices:"
adb devices

# Run the Python script with all arguments passed through
print_status "Running time synchronization..."
python3 adb_time_sync.py "$@"

if [ $? -eq 0 ]; then
    print_status "Time synchronization completed successfully!"
else
    print_error "Time synchronization failed!"
    exit 1
fi 