# Copyright 2024 The Autoware Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def launch_setup(context, *args, **kwargs):
    pkg_prefix = FindPackageShare('f1tenth_launch')
    trajectory_loader_param_file = PathJoinSubstitution(
        [pkg_prefix, 'config/planning/trajectory_loader.param.yaml']
    )
    env_perceiver_param_file = PathJoinSubstitution(
        [pkg_prefix, 'config/planning/env_perceiver_params.param.yaml']
    )
    traj_selector_param_file = PathJoinSubstitution(
        [pkg_prefix, 'config/planning/traj_selector_params.param.yaml']
    )
    trajectory_csv_path = PathJoinSubstitution(
        [LaunchConfiguration('map_path'), 'trajectory.csv']
    )

    trajectory_loader_launch = GroupAction([
        PushRosNamespace('planning'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                launch_file_path=PathJoinSubstitution([
                    FindPackageShare('trajectory_loader'), 'launch', 'trajectory_loader.launch.py'
                ])
            ),
            launch_arguments={
                'trajectory_loader_param_file': trajectory_loader_param_file,
                'csv_path': trajectory_csv_path,
                'output_trajectory_topic': 'racing_planner/trajectory'
            }.items(),
            condition=IfCondition(LaunchConfiguration('use_trajectory_loader'))
        )
    ])

    traj_selector_node = Node(
        package='traj_selector',
        executable='traj_selector',
        name='traj_selector',
        parameters=[traj_selector_param_file],
        remappings=[
            ("/traj", "/planning/racing_planner/trajectory"),
            ("/odom", "/localization/kinematic_state")
        ]
    )

    env_perceiver_node = Node(
        package='env_perceiver',
        executable='env_perceiver',
        name='env_perceiver',
        parameters=[env_perceiver_param_file]
        remappings=[
            ("/lidar", "/sensing/lidar/scan"),
            ("/odom", "/localization/kinematic_state"),
            ("/lidar", "/sensing/lidar/scan"),
            ("/traj", "/planning/racing_planner/trajectory")
        ]
    )

    return [
        trajectory_loader_launch,
        traj_selector_node,
        env_perceiver_node,
    ]

def generate_launch_description():
    declared_arguments = []

    def add_launch_arg(name: str, default_value: str = None):
        declared_arguments.append(
            DeclareLaunchArgument(name, default_value=default_value)
        )

    add_launch_arg('map_path')
    add_launch_arg('use_trajectory_loader', 'true')

    return LaunchDescription([
        *declared_arguments,
        OpaqueFunction(function=launch_setup)
    ])
