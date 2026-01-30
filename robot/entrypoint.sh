#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
python3 ./broadcast.py &
ros2 launch foxglove_bridge foxglove_bridge_launch.xml address:=0.0.0.0 &
wait