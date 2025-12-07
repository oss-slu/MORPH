# **SMART: SLU Mobile Autonomous Robotics Toolkit**
## Getting Started (ROS2 Jazzy)
### Clone the repository
```bash
git clone https://github.com/oss-slu/SmartRobot.git
cd SmartRobot
```
### Build the ROS2 components
```bash
git clone https://github.com/oss-slu/SmartRobot.git
cd ros2_ws
rosdep install
colcon build --symlink-install
```

### Running the full ROS2 launch
To bring up the robot URDF/xacro in compatibility with the specific Waveshare servos/joints, use our custom Waveshare launch command. This will also launch a `ros2_control` differential drive model based on real life specs and joint descriptions, creating a twist-controller and estimate encoder odometry:
```bash
cd ros2_ws # if not already
source install/setup.bash
ros2 launch waveshare_servos example.launch.py
```

## Getting Started (Desktop client)
### Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```
### Install dependencies
```bash
pip install -r requirements.txt
```
### Run the application
```bash
python app.py
```
### Open in browser
```bash
Visit: http://127.0.0.1:5000/
```

## About
SMART/MORPH is an open-source electronics platform. By working with the OpenSource@SLU, we hope to bring modern robotics education access to the next generation of students.
