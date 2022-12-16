"""
followpath_behavior.py
"""

# Copyright 2022 Universidad Politécnica de Madrid
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the the copyright holder nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


__authors__ = "Miguel Fernández Cortizas, Pedro Arias Pérez, David Pérez Saura, Rafael Pérez Seguí"
__copyright__ = "Copyright (c) 2022 Universidad Politécnica de Madrid"
__license__ = "BSD-3-Clause"
__version__ = "0.1.0"

from typing import Union, TYPE_CHECKING

from nav_msgs.msg import Path
from geometry_msgs.msg import Pose
from geographic_msgs.msg import GeoPath
from as2_msgs.msg import PoseWithID, YawMode
from as2_msgs.srv import GeopathToPath
from as2_msgs.action import FollowPath

from .behavior_handler import BehaviorHandler
from ..tools.utils import path_to_list

if TYPE_CHECKING:
    from ..drone_interface_base import DroneInterfaceBase


class FollowPathBehavior(BehaviorHandler):
    """FollowPath Behavior"""

    def __init__(self, drone: 'DroneInterfaceBase') -> None:
        self.__drone = drone

        try:
            super().__init__(drone, FollowPath, 'FollowPathBehaviour')
        except self.BehaviorNotAvailable as err:
            self.__drone.get_logger().warn(str(err))

    def start(self, path: Union[list, tuple, Path, GeoPath, PoseWithID],
              speed: float, yaw_mode: int, yaw_angle: float,
              wait_result: bool = True) -> bool:
        goal_msg = FollowPath.Goal()
        goal_msg.header.stamp = self.__drone.get_clock().now().to_msg()
        goal_msg.header.frame_id = "earth"  # TODO
        goal_msg.path = self.__get_path(path)
        yaw_msg = YawMode()
        yaw_msg.angle = yaw_angle
        yaw_msg.mode = yaw_mode
        goal_msg.yaw = yaw_msg
        goal_msg.max_speed = speed
        return super().start(goal_msg, wait_result)

    def modify(self, path: Union[list, tuple, Path, GeoPath, PoseWithID],
               speed: float, yaw_mode: int, yaw_angle: float):
        goal_msg = FollowPath.Goal()
        goal_msg.header.stamp = self.__drone.get_clock().now().to_msg()
        goal_msg.header.frame_id = "earth"  # TODO
        goal_msg.path = self.__get_path(path)
        yaw_msg = YawMode()
        yaw_msg.angle = yaw_angle
        yaw_msg.mode = yaw_mode
        goal_msg.yaw = yaw_msg
        goal_msg.max_speed = speed
        return super().modify(goal_msg)

    def __get_path(self, path: Union[list, tuple, Path, GeoPath, PoseWithID]):
        """get trajectory msg"""

        point_list = []
        if isinstance(path, list):
            if not path:  # not empty
                raise self.GoalRejected("Goal format invalid")
            if isinstance(path[0], list):
                point_list = path
            else:
                point_list = [path]
        elif isinstance(path, tuple):
            point_list = [list(path)]
        elif isinstance(path, Path):
            point_list = path_to_list(path)
        elif isinstance(path, GeoPath):
            req = GeopathToPath.Request()
            req.geo_path = path
            resp = self.__drone.global_to_local_cli_.call(req)
            if not resp.success:
                self.__drone.get_logger().warn("Can't follow path since origin is not set")
                raise TimeoutError("GPS service not available")

            point_list = path_to_list(resp.path)
        elif isinstance(path, PoseWithID):
            return list(path)
        else:
            raise self.GoalRejected("Goal format invalid")

        pose_with_id_list = []
        id_ = 0
        for waypoint in point_list:
            pose_with_id = PoseWithID()
            pose_with_id.pose = Pose()
            pose_with_id.id = str(id_)
            pose_with_id.pose.position.x = waypoint[0]
            pose_with_id.pose.position.y = waypoint[1]
            pose_with_id.pose.position.z = waypoint[2]
            pose_with_id_list.append(pose_with_id)
            id_ += 1
        return pose_with_id_list
