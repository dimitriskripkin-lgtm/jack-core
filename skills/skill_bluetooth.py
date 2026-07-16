import sys, time, subprocess
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
from jack_android import _sh, adb_setup
def run():
    adb_setup()
    _sh("am start -n com.android.settings/.bluetooth.BluetoothSettings", root=True)
    time.sleep(2.5)
    subprocess.run("adb -s 127.0.0.1:5555 shell input tap 225 301", shell=True)
    return {"ok": True, "skill": "bluetooth", "element": "Bluetooth"}
if __name__ == "__main__":
    print(run())