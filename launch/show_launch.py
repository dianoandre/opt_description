import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution, FindExecutable,LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():

    # --- Setup environment variables
    MDL_ENV_VAR = "IGN_GAZEBO_RESOURCE_PATH"
    if MDL_ENV_VAR in os.environ:
        os.environ[MDL_ENV_VAR] += ":" + os.path.join(
            get_package_prefix("opt_description"), "share"
        )
    else:
        os.environ[MDL_ENV_VAR] = os.path.join(
            get_package_prefix("opt_description"), "share"
        )

    LIB_ENV_VAR = "IGN_GAZEBO_SYSTEM_PLUGIN_PATH"
    if LIB_ENV_VAR in os.environ:
        os.environ[LIB_ENV_VAR] += ":/opt/ros/humble/lib"
    else:
        os.environ[LIB_ENV_VAR] = "/opt/ros/humble/lib"


    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Start RViz2 automatically with this launch file.",
        )
    )
    gui = LaunchConfiguration("gui")

    # Generate the robot description from the Xacro file
    opt_description_content = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            PathJoinSubstitution(
                [
                    get_package_share_directory("opt_description"),
                    "urdf",
                    "opt_table.xacro",
                ]
            ),
        ]
    )
    # Robot description parameter
    robot_description = {"robot_description": opt_description_content}
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("opt_description"), "rviz", "opt.rviz"]
    )
 
    # Define the joint_state_publisher_gui node
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
    )

    # Define the robot_state_publisher node
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    # Define the joint_state_broadcaster and robot_controller spawners
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_position_controller", "--controller-manager", "/controller_manager"],
    )
    # Define the RViz node
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        condition=IfCondition(gui),
    )

    # gazebo nodes
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments=[("gz_args", " -r -v 3 empty.sdf")],
        condition=IfCondition(gui),
    )

    # Define the headless Gazebo node
    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments=[("gz_args", ["--headless-rendering -s -r -v 3 empty.sdf"])],
        condition=UnlessCondition(gui),
    )

    # Gazebo bridge
    gazebo_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # Spawn robot node
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "/robot_description",
            "-name",
            "rrbot_system_position",
            "-allow_renaming",
            "true",
        ],
    )
    
    clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # Return the LaunchDescription with all nodes
    nodes = [
        gazebo,
        gazebo_headless,
        gazebo_bridge,
        node_robot_state_publisher,
        gz_spawn_entity,
        joint_state_broadcaster_spawner,
        robot_controller_spawner,
        rviz_node,
    ]

    return LaunchDescription(declared_arguments + nodes)
