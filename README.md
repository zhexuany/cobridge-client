
In this intelligent vehicle competition, real-time performance, resource utilization, and stability are crucial requirements for the control system. Many participants initially use rosbridge when building their control platforms, but quickly discover that it struggles under high concurrency and low bandwidth environments.

Therefore, based on practical scenario requirements, we designed and implemented cobridge — a high-performance communication bridge implemented in C++ to replace rosbridge, building a more stable, low-latency vehicle control system.

# Why rosbridge is no longer suitable?

Although rosbridge provides a complete set of WebSocket interfaces that allow non-ROS environments to implement map publishing, command issuing, and keyboard control, enabling developers to read and write to ROS systems in non-ROS environments, it is implemented in Python and has the following issues:

- High resource consumption: Python's interpreted execution mechanism naturally leads to relatively high CPU and memory usage.
- High network latency: Lack of flow control mechanisms during data transmission easily leads to accumulation or stuttering.
- Lack of real-time mechanisms: The absence of message priority management can cause high-priority control commands to be overwhelmed.

# cobridge: Our redefined intelligent vehicle communication bridge

To solve the series of pain points with rosbridge, we developed cobridge based on C++, which fundamentally optimizes system performance with the following advantages:

- ✅ High performance with low resource consumption: C++ compiled execution efficiency far exceeds Python, uses fewer resources, and runs more stably.
- ⏱️ Strong real-time capability: Built-in priority queue actively discards low-priority packets during network fluctuations, ensuring critical control information is transmitted in real-time.
- 🔁 Full version compatibility: Supports ROS1 (Indigo to Noetic) and ROS2 (Foxy to Jazzy), eliminating version fragmentation concerns.
- 🌐 Cloud-friendly: Comes with coStudio client, ready to use without building your own client, saving significant development time.
- 🧠 URDF rendering support: Combined with coStudio and cloud platform, can directly render robot models, which rosbridge cannot accomplish.

# User Guide:
🚗 Vehicle-side Deployment Steps
- All vehicle-side files are stored in the "/Car" directory of the compressed package. Before starting, copy this directory to the mainboard of your vehicle. All subsequent operations should be performed in the /Car directory.
1. Ensure Python version ≥ 3.8 and install required dependencies:
  

```
📁 File Structure & Usage Flow
BRIDGE_CLIENT/                 ← Root directory, contains all code for vehicle and control sides
│
├── Car/                       ← Vehicle system related files (deployed on the vehicle)
│   ├── cobridge_client.py     ← Vehicle-side main control script, controls vehicle via ROS2, handles maps and signals
│   ├── config.yaml            ← Vehicle-side parameter configuration file (speed, map paths, etc.)
│   ├── map.png                ← Grayscale map image, used to generate OccupancyGrid map
│   └── requirements-car.txt   ← List of Python third-party dependencies for vehicle side
│
├── Pc/                        ← Control side (PC) related files
│   ├── config.yaml            ← Control side configuration file (vehicle IP, speed parameters, etc.)
│   ├── control.py             ← Control side main program, sends commands to vehicle via TCP
│   ├── coStudio-v24.471-win.exe ← coStudio executable for visualization and control (Windows only, Ubuntu version available at: https://www.coscene.cn/download)
│   └── requirement-pc.txt     ← List of Python third-party dependencies for control side
│
└── README.md                 ← Project documentation, covers background, deployment methods and usage guide
```

Final Notes:
A more standardized approach to node management and information publishing will help everyone develop better coding practices!
- Instead of "hardcoding" maps and control logic in Windows, we recommend:
  - Using ROS native OccupancyGrid type for map publishing (see publish_map() function).
  - Implementing QoS configurations to ensure communication reliability.
  - Utilizing the control-side "signal mechanism" and "speed adjustment features" for more precise driving tests.
