# SPDX-FileCopyrightText: Copyright (c) 2022 Guillaume Bellegarda. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Copyright (c) 2022 EPFL, Guillaume Bellegarda

""" Run CPG """
import time
import numpy as np
import matplotlib

# adapt as needed for your system
# from sys import platform
# if platform =="darwin":
#   matplotlib.use("Qt5Agg")
# else:
#   matplotlib.use('TkAgg')

from matplotlib import pyplot as plt

from env.hopf_network import HopfNetwork
from env.quadruped_gym_env import QuadrupedGymEnv


ADD_CARTESIAN_PD = True 
TIME_STEP = 0.001
foot_y = 0.0838 # this is the hip length 
sideSign = np.array([-1, 1, -1, 1]) # get correct hip sign (body right is negative)

# 创建——环境类 
# 环境类创建过程中会一起创建 四足机器人实例  
# (Cearte env class)
# (Create the quadruped robot class at the same time)
env = QuadrupedGymEnv(render=True,              # visualize
                    on_rack=False,              # useful for debugging! 
                    isRLGymInterface=False,     # not using RL
                    time_step=TIME_STEP,
                    action_repeat=1,
                    motor_control_mode="TORQUE",
                    add_noise=False,    # start in ideal conditions
                    # record_video=True
                    )

# 创建——中央发生器类 
# (Create CPG class)
# initialize Hopf Network, supply gait
cpg = HopfNetwork(time_step=TIME_STEP)
# cpg.use_RL = True #00FF00 调用强化学习测试
cpg._set_gait("TROT") #00FF00 "TROT" "PACE" "BOUND" "WALK"

TEST_STEPS = int(10 / (TIME_STEP))
t = np.arange(TEST_STEPS)*TIME_STEP

# [#0000FF TODO] initialize data structures to save CPG and robot states


# 设置 PID 参数 (Set PID Parameter)
# joint PD gains
kp=np.array([100,100,100])
kd=np.array([2,2,2])
# Cartesian PD gains
kpCartesian = np.diag([500]*3)
kdCartesian = np.diag([20]*3)

for j in range(TEST_STEPS):
  # initialize torque array to send to motors
  action = np.zeros(12) 
  # get desired foot positions from CPG 
  xs,zs = cpg.update()
  
  #0000FF TODO：get current motor angles and velocities for joint PD, see GetMotorAngles(), GetMotorVelocities() in quadruped.py
  q  = env.robot.GetMotorAngles()     # 获取所有(12个)电机角度 Get all (12) motors' angle
  dq = env.robot.GetMotorVelocities() # 获取所有(12个)电机速度 Get all (12) motors' velocity

  # 对四只脚进行计算
  # computation for 4 legs
  # loop through desired foot positions and calculate torques
  for i in range(4):
    # initialize torques for leg_i
    tau = np.zeros(3)

    # 足末端：目标位置
    # 注意：跟 Project 0 不一样，这里是三维的
    # get desired foot i pos (xi, yi, zi) in leg frame 
    # attension: it's 3 dimensional
    leg_xyz = np.array([xs[i],sideSign[i] * foot_y,zs[i]])
    
    # 1.使用逆运动学计算关节角度   1.Use inverse kinematics to compute the joint angle 
    # 2.使用PID输出力矩           2.Use PID to compute the output torque
    # [#0000FF TODO] call inverse kinematics to get corresponding joint angles (see ComputeInverseKinematics() in quadruped.py) 
    # [#0000FF TODO] Add joint PD contribution to tau for leg i (Equation 4)  

    # [#00FF00] 获取实际参数     # Get actuall angle and angular velocity
    real_q  = q[3*i:3*i+3]
    real_dq = dq[3*i:3*i+3]

    des_q  = env.robot.ComputeInverseKinematics(legID = i, xyz_coord = leg_xyz) 
    des_dq = np.zeros(3)

    tau += kp * (des_q - real_q) + kd * (des_dq - real_dq)   

    # 增加 笛卡尔坐标 PD (add Cartesian PD contribution)
    if ADD_CARTESIAN_PD:
      # [#0000FF TODO] Get current Jacobian and foot position in leg frame (see ComputeJacobianAndPosition() in quadruped.py)
      J, real_p = env.robot.ComputeJacobianAndPosition(i)
      
      # [#0000FF TODO] Get current foot velocity in leg frame (Equation 2)
      real_dp = J @ real_dq

      # [#0000FF TODO] Calculate torque contribution from Cartesian PD (Equation 5) [Make sure you are using matrix multiplications]
      des_p  = leg_xyz
      des_dp = np.zeros(3)
      tau += J.T @ ((kpCartesian @ (des_p - real_p) + kdCartesian @ (des_dp - real_dp))) 

    # Set tau for leg_i in action vector
    action[3*i:3*i+3] = tau

  # send torques to robot and simulate TIME_STEP seconds 
  env.step(action) 

  # [#0000FF TODO] save any CPG or robot states



##################################################### 
# PLOTS
#####################################################
# example
# fig = plt.figure()
# plt.plot(t,joint_pos[1,:], label='FR thigh')  #00FF00 joint_pos 这个变量上面没有
# plt.legend(['x','y','z'])
# plt.show()