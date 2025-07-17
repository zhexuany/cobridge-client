#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import Int32
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy
import cv2
import yaml
import os
import sys
import platform
import subprocess
import signal
import atexit
from threading import Thread
from time import sleep
from cv_bridge import CvBridge
from builtin_interfaces.msg import Time
import rclpy.clock

class Ros2ControlNode(Node):
    def __init__(self):
        super().__init__('ros2_control_node')

        import socket
        self.get_logger().info(f"🌐 Detected hostname: {socket.gethostname()}")
        self.get_logger().info(f"🌐 Resolved IP: {socket.gethostbyname(socket.gethostname())}")

        self.bridge = CvBridge()
        self.linear = 0.25
        self.angular = 3.14
        self.dert = 0.3
        self.image_path = 'map.png'
        self.isStartTelemetry = False
        self.isOverTelemetry = False
        self.signFlag = False
        self.signMsg = Int32()

        self.load_config()
        self.init_keymap()
        self.qos = QoSProfile(
            depth=10,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE
        )
        self.init_publishers()
        self.init_subscribers()
        self.publish_map()
        self.start_keyboard_thread()
        self.print_help()
        self.start_tcp_server()

    def load_config(self):
        if os.path.exists('config.yaml'):
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            self.image_path = config.get('map_path', self.image_path)
            self.linear = float(config.get('linear', self.linear))
            self.angular = float(config.get('angular', self.angular))
            self.dert = float(config.get('dert', self.dert))

    def init_publishers(self):
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', self.qos)
        self.map_pub = self.create_publisher(OccupancyGrid, '/map', self.qos)
        self.sign_pub = self.create_publisher(Int32, '/sign_foxglove', self.qos)

    def init_subscribers(self):
        self.create_subscription(Int32, '/sign4return', self.sign_callback, self.qos)

    def init_keymap(self):
        self.key_mapping = {
            'stop': self.make_twist(0.0, 0.0),
            'up': self.make_twist(self.linear, 0.0),
            'down': self.make_twist(-self.linear, 0.0),
            'left': self.make_twist(0.0, self.angular),
            'right': self.make_twist(0.0, -self.angular),
            'up_left': self.make_twist(self.linear, self.angular),
            'up_right': self.make_twist(self.linear, -self.angular),
            'down_left': self.make_twist(-self.linear, self.angular),
            'down_right': self.make_twist(-self.linear, -self.angular)
        }

    def make_twist(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        return msg

    def publish_map(self):
        if not os.path.exists(self.image_path):
            self.get_logger().warn(f"Map file not found: {self.image_path}")
            return

        image = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        image = cv2.flip(image, -1)
        image = cv2.flip(image, 1)

        height, width = image.shape
        resolution = 5.0 / width
        data = [0 if pixel < 128 else -1 for row in image for pixel in row]

        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom_combined'
        msg.info.width = width
        msg.info.height = height
        msg.info.resolution = resolution
        msg.info.origin.position.x = 0.0
        msg.info.origin.position.y = 0.0
        msg.info.origin.orientation.w = 1.0
        msg.data = data

        self.map_pub.publish(msg)
        self.sign_pub.publish(Int32(data=0))

    def sign_callback(self, msg):
        if msg.data == 5:
            self.get_logger().info("Received telemetry start signal")
            self.isStartTelemetry = True
        elif msg.data == 6:
            self.get_logger().info("Received telemetry stop signal")
            self.isOverTelemetry = True
        self.signMsg = msg
        self.signFlag = True

    def start_keyboard_thread(self):
        thread = Thread(target=self.keyboard_listener, daemon=True)
        thread.start()

    def keyboard_listener(self):
        import sys
        import tty
        import termios

        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

        print("\n🌐 Terminal Control Mode (press 'q' to quit)")
        print("[w/a/s/d] Move, [p] Pause, [r] Resume, [t] Help")

        while rclpy.ok():
            key = getch()

            if key == 'q':
                print("🔚 Exit requested.")
                break
            elif key == 'w':
                self.vel_pub.publish(self.key_mapping['up'])
            elif key == 's':
                self.vel_pub.publish(self.key_mapping['down'])
            elif key == 'a':
                self.vel_pub.publish(self.key_mapping['left'])
            elif key == 'd':
                self.vel_pub.publish(self.key_mapping['right'])
            elif key == 'p':
                print("⏸️ Paused.")
                self.vel_pub.publish(self.key_mapping['stop'])
            elif key == 'r':
                print("▶️ Resumed.")
            elif key == 't':
                self.print_help()
            elif key == '\x1b':  # handle arrow keys (escape sequences)
                next1 = getch()
                next2 = getch()
                if next1 == '[':
                    if next2 == 'A':
                        self.linear += self.dert
                        self.update_keymap()
                    elif next2 == 'B':
                        self.linear = max(0.0, self.linear - self.dert)
                        self.update_keymap()
                    elif next2 == 'C':
                        self.angular += self.dert
                        self.update_keymap()
                    elif next2 == 'D':
                        self.angular = max(0.0, self.angular - self.dert)
                        self.update_keymap()
            else:
                print("❓ Unknown command. Press 't' for help.")

    def update_keymap(self):
        self.init_keymap()
        print(f"Updated speed: linear={self.linear:.2f} m/s, angular={self.angular:.2f} rad/s")

    def print_help(self):
        print("\n键盘控制说明:")
        print("  [ w ] 前进   [ s ] 后退")
        print("  [ a ] 左转   [ d ] 右转")
        print("  [ p ] 暂停控制")
        print("  [ r ] 继续控制")
        print("  [ t ] 显示帮助")
        print("  方向键调整线速度和角速度")

    def start_tcp_server(self):
        thread = Thread(target=self.tcp_listener, daemon=True)
        thread.start()

    def tcp_listener(self):
        import socket
        HOST = '0.0.0.0'
        PORT = 9000
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1000)
            self.get_logger().info(f"🚪 TCP server listening on port {PORT}")
            self.get_logger().info("⏳ Waiting for incoming TCP connections...")
            while rclpy.ok():
                try:
                    conn, addr = s.accept()
                    self.get_logger().info(f"📡 Connection established from {addr}")
                    self.get_logger().info(f"📶 Accepted connection from {addr}")
                    Thread(target=self.handle_tcp_client, args=(conn, addr), daemon=True).start()
                except Exception as e:
                    self.get_logger().error(f"❌ Exception while accepting connection: {e}")

    def handle_tcp_client(self, conn, addr):
        import socket
        import traceback
        with conn:
            try:
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except Exception as e:
                self.get_logger().warn(f"⚠️ Failed to set SO_KEEPALIVE for {addr}: {e}")
            self.get_logger().info(f"🧲 Ready to receive data from {addr}")
            try:
                while rclpy.ok():
                    data = conn.recv(1024)
                    self.get_logger().debug(f"📥 Received raw data from {addr}: {data}")
                    if not data:
                        self.get_logger().info(f"🔌 TCP connection from {addr} closed by client.")
                        break
                    msg = data.decode().strip()
                    self.get_logger().info(f"📝 Decoded command from {addr}: {msg}")
                    if msg.startswith("CMD_VEL:"):
                        payload = msg.replace("CMD_VEL:", "")
                        linear, angular = map(float, payload.split(','))
                        twist = Twist()
                        twist.linear.x = linear
                        twist.angular.z = angular
                        self.vel_pub.publish(twist)
                    elif msg == "PUBLISH_MAP":
                        self.publish_map()
                    elif msg.startswith("SIGN:"):
                        val = int(msg.split(':')[1])
                        self.sign_pub.publish(Int32(data=val))
                    else:
                        self.get_logger().warn(f"❓ Unknown TCP command from {addr}: {msg}")
            except Exception as e:
                self.get_logger().error(f"❌ Error in client handler {addr}: {e}\n{traceback.format_exc()}")

def main():
    rclpy.init()
    node = Ros2ControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()