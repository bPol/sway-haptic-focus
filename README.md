# sway-haptic-focus

Add **haptic feedback** for window focus on **Sway / Wayland** using a **Logitech MX Master 4** connected via the **Logi Bolt receiver**.

The script listens to window focus events through `i3ipc` and triggers the MX Master 4’s internal haptic motor.  
It auto-recovers after suspend, unplug, or reboot (handles `/dev/hidraw` changes automatically).

---

## Features

- ✅ Haptic feedback on Sway window focus  
- 🔄 Auto-reconnect after suspend/restart (`Broken pipe` fix)  
- 🧠 Automatically detects the correct Bolt HID++ interface  
- ⚙️ Configurable vibration pattern and cooldown  
- 💡 Simple to autostart from Sway  

---

## Requirements

```bash
sudo apt install python3 python3-pip libhidapi-hidraw0
pip install i3ipc hidapi
