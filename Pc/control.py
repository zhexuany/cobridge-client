import socket
import time
from pynput import keyboard
import yaml
import os

# === Load Config ===
default_config = {
    "ip": "127.0.0.1",
    "port": 9000,
    "linear": 0.25,
    "angular": 3.14,
    "dert": 0.3
}
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print("⚠️ config.yaml not found. Using default configuration.")
    config = default_config

ROBOT_IP = config.get("ip", default_config["ip"])
PORT = config.get("port", default_config["port"])
linear = config.get("linear", default_config["linear"])
angular = config.get("angular", default_config["angular"])
dert = config.get("dert", default_config["dert"])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((ROBOT_IP, PORT))
print(f"✅ Connected to robot at {ROBOT_IP}:{PORT}")
print("🕹️ Controls: w/s/a/d to move, 5/6 to signal, arrows adjust speed, q to quit")

key_state = set()
running = True

last_cmd = None  # 新增，放在函数定义之前

def safe_send(data):
    if sock._closed:
        print("⚠️ Socket is closed. Cannot send data.")
        return
    try:
        sock.sendall(data)
    except BrokenPipeError:
        print("❌ Broken pipe: connection lost.")

def send_cmd():
    global last_cmd
    cmd = None
    if 'w' in key_state:
        cmd = f"CMD_VEL:{linear},0.0\n"
    elif 's' in key_state:
        cmd = f"CMD_VEL:{-linear},0.0\n"
    elif 'a' in key_state:
        cmd = f"CMD_VEL:0.0,{angular}\n"
    elif 'd' in key_state:
        cmd = f"CMD_VEL:0.0,{-angular}\n"
    elif 'p' in key_state:
        cmd = "CMD_VEL:0.0,0.0\n"
        print("⏸️ Paused.")
    elif 'r' in key_state:
        print("▶️ Resumed.")
    elif '5' in key_state:
        cmd = "SIGN:5\n"
    elif '6' in key_state:
        cmd = "SIGN:6\n"

    if cmd and cmd != last_cmd:
        safe_send(cmd.encode())
        last_cmd = cmd

def on_press(key):
    global running, linear, angular
    try:
        k = key.char
        if k == 'q':
            print("🛑 Exiting.")
            running = False
        else:
            key_state.add(k)
    except AttributeError:
        if key == keyboard.Key.up:
            linear += dert
            print(f"↑ Increase linear speed: {linear:.2f}")
        elif key == keyboard.Key.down:
            linear = max(0.0, linear - dert)
            print(f"↓ Decrease linear speed: {linear:.2f}")
        elif key == keyboard.Key.right:
            angular += dert
            print(f"→ Increase angular speed: {angular:.2f}")
        elif key == keyboard.Key.left:
            angular = max(0.0, angular - dert)
            print(f"← Decrease angular speed: {angular:.2f}")

def on_release(key):
    try:
        k = key.char
        key_state.discard(k)
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

try:
    while running:
        send_cmd()
        time.sleep(0.1)
finally:
    sock.close()
