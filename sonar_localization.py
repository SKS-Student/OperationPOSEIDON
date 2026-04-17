"""
Sonar Object Localization
=========================
Sensor inputs (7 values per frame):
  yaw, pitch, roll          — IMU angles in degrees
  sonar_dist                — underwater ultrasound distance (m)
  us_forward                — ultrasonic distance to forward obstacle (m)
  us_side                   — ultrasonic distance to side obstacle (m)
  servo_angle               — servo angle in degrees (-45 to +45, 0 = straight down -Y)

Coordinate frame (world, right-hand):
  +X = device's initial forward direction
  +Y = up
  +Z = device's initial right direction
  Origin = device's starting position (0, 0, 0)

Position estimation:
  - The device floats on water, so its Y position stays at 0 (water surface).
  - Forward/side ultrasonics measure distance to obstacles ahead and to the right.
  - We track how those obstacle distances *change* over time to infer movement
    (delta-ranging odometry): if the forward obstacle gets 0.1 m closer, the
    device moved 0.1 m forward in its heading direction.
  - Yaw rotates the device's heading in the world XZ plane.
  - Pitch and roll are applied only to rotate the sonar beam direction,
    not to move the device (it stays on the water surface).

Sonar beam direction:
  - The servo swings in the device's local roll axis (front-to-back plane).
  - servo_angle = 0  → beam points straight down  (-Y world, adjusted for pitch/roll)
  - servo_angle = +45 → beam tilts 45° forward of down
  - servo_angle = -45 → beam tilts 45° behind down
  - The full device orientation (yaw, pitch, roll) is then applied to rotate
    the beam into world coordinates.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class SensorFrame:
    yaw: float          # degrees, rotation around world Y (compass heading)
    pitch: float        # degrees, nose-up positive
    roll: float         # degrees, right-side-down positive
    sonar_dist: float   # metres, underwater ultrasound range
    us_forward: float   # metres, ultrasonic distance to forward obstacle
    us_side: float      # metres, ultrasonic distance to side obstacle (right)
    servo_angle: float  # degrees, -45 (behind) to +45 (forward), 0 = straight down


@dataclass
class LocalizationResult:
    device_position: np.ndarray        # [x, y, z] of device in world frame
    object_position: np.ndarray        # [x, y, z] of detected object in world frame
    sonar_beam_direction: np.ndarray   # unit vector of sonar beam in world frame
    frame: SensorFrame


def rotation_matrix_yaw_pitch_roll(yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """
    Build a rotation matrix from yaw, pitch, roll (intrinsic ZYX / aerospace convention).
    Applied as: R = R_yaw @ R_pitch @ R_roll
    Rotates vectors from device-local frame to world frame.
    """
    yaw   = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll  = math.radians(roll_deg)

    # Rotation about Y axis (yaw / heading)
    cy, sy = math.cos(yaw), math.sin(yaw)
    R_yaw = np.array([
        [ cy,  0, sy],
        [  0,  1,  0],
        [-sy,  0, cy],
    ])

    # Rotation about Z axis (pitch, nose up)
    cp, sp = math.cos(pitch), math.sin(pitch)
    R_pitch = np.array([
        [cp, -sp, 0],
        [sp,  cp, 0],
        [ 0,   0, 1],
    ])

    # Rotation about X axis (roll, right side down)
    cr, sr = math.cos(roll), math.sin(roll)
    R_roll = np.array([
        [1,   0,   0],
        [0,  cr, -sr],
        [0,  sr,  cr],
    ])

    return R_yaw @ R_pitch @ R_roll


def sonar_beam_in_device_frame(servo_angle_deg: float) -> np.ndarray:
    """
    Compute the sonar beam unit vector in the device's local frame.

    Device local axes:
      +X_local = forward
      +Y_local = up
      +Z_local = right

    servo_angle = 0   → beam points straight down = (0, -1, 0) local
    servo_angle = +45 → beam tilts 45° forward of down, rotating around local +Z (roll axis)
    servo_angle = -45 → beam tilts 45° behind down

    Rotation of (0,-1,0) around +Z by servo_angle:
      new_x =  sin(servo_angle)   (forward component)
      new_y = -cos(servo_angle)   (downward component)
      new_z = 0
    """
    a = math.radians(servo_angle_deg)
    local_beam = np.array([
        math.sin(a),    # X: forward tilt
        -math.cos(a),   # Y: downward
        0.0             # Z: no side component (servo is in roll plane)
    ])
    return local_beam / np.linalg.norm(local_beam)


class SonarLocalizer:
    """
    Stateful localizer that tracks device position via delta-ranging odometry
    and computes world-frame XYZ of each sonar detection.
    """

    def __init__(self, us_forward_noise_threshold: float = 0.02,
                 us_side_noise_threshold: float = 0.02):
        """
        Args:
            us_forward_noise_threshold: ignore forward delta smaller than this (m) as noise
            us_side_noise_threshold:    ignore side delta smaller than this (m) as noise
        """
        self.device_position = np.array([0.0, 0.0, 0.0])
        self._prev_us_forward: Optional[float] = None
        self._prev_us_side: Optional[float] = None
        self._prev_yaw: Optional[float] = None
        self.us_forward_noise_threshold = us_forward_noise_threshold
        self.us_side_noise_threshold = us_side_noise_threshold
        self.history: List[LocalizationResult] = []

    def _update_device_position(self, frame: SensorFrame):
        """
        Estimate device movement using delta-ranging from the ultrasonic sensors.

        If the forward obstacle gets closer by Δd, the device moved +Δd forward.
        If the side obstacle gets closer by Δd, the device moved +Δd to the right.
        Movement direction in world frame is determined by current yaw.
        """
        if self._prev_us_forward is None:
            self._prev_us_forward = frame.us_forward
            self._prev_us_side = frame.us_side
            self._prev_yaw = frame.yaw
            return

        delta_forward = self._prev_us_forward - frame.us_forward
        delta_side    = self._prev_us_side    - frame.us_side

        if abs(delta_forward) < self.us_forward_noise_threshold:
            delta_forward = 0.0
        if abs(delta_side) < self.us_side_noise_threshold:
            delta_side = 0.0

        yaw_rad = math.radians(frame.yaw)
        forward_world = np.array([ math.cos(yaw_rad), 0.0,  math.sin(yaw_rad)])
        right_world   = np.array([ math.sin(yaw_rad), 0.0, -math.cos(yaw_rad)])

        self.device_position += delta_forward * forward_world
        self.device_position += delta_side    * right_world
        # Y stays 0 — device floats on water surface

        self._prev_us_forward = frame.us_forward
        self._prev_us_side    = frame.us_side
        self._prev_yaw        = frame.yaw

    def process(self, frame: SensorFrame) -> LocalizationResult:
        """
        Process one sensor frame and return the world-frame XYZ of the detected object.
        """
        self._update_device_position(frame)

        local_beam = sonar_beam_in_device_frame(frame.servo_angle)

        R = rotation_matrix_yaw_pitch_roll(frame.yaw, frame.pitch, frame.roll)
        world_beam = R @ local_beam
        world_beam = world_beam / np.linalg.norm(world_beam)

        object_position = self.device_position + frame.sonar_dist * world_beam

        result = LocalizationResult(
            device_position=self.device_position.copy(),
            object_position=object_position,
            sonar_beam_direction=world_beam,
            frame=frame,
        )
        self.history.append(result)
        return result


def compute_object_position_stateless(
    yaw: float, pitch: float, roll: float,
    sonar_dist: float,
    us_forward: float, us_side: float,
    servo_angle: float,
    device_position: np.ndarray = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stateless single-frame computation. You must supply device_position externally.
    Returns: (device_position, object_position)
    """
    if device_position is None:
        device_position = np.zeros(3)

    local_beam = sonar_beam_in_device_frame(servo_angle)
    R = rotation_matrix_yaw_pitch_roll(yaw, pitch, roll)
    world_beam = R @ local_beam
    world_beam /= np.linalg.norm(world_beam)
    object_position = device_position + sonar_dist * world_beam
    return device_position, object_position