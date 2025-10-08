# sway-haptic-focus
The script listens to window focus events through `i3ipc` and triggers the MX Master 4’s internal haptic motor.   It auto-recovers after suspend, unplug, or reboot (handles `/dev/hidraw` changes automatically).
