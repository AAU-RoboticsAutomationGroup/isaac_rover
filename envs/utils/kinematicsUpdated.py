#!/usr/bin/env python
from binascii import crc32
import numpy as np
#from .locomotion_modes import LocomotionMode
import math

import torch
import time
def timeG(lin_vel,ang_vel):
    start = time.time()
    Ackermann(lin_vel, ang_vel)
    end = time.time()
    return (end-start)


@torch.jit.script
def Ackermann(lin_vel, ang_vel):
    # type: (Tensor, Tensor) -> Tuple[Tensor, Tensor]
    lin_vel = lin_vel * 30 # Vi ganger med 30 for at få velocities imellem -30 og 30
    ang_vel = ang_vel * 30 
    
    wheel_x = 12.0
    wheel_y = 20.0
    # Distance from center og the rover to the top (centimeters):
    y_top = 16 # check if it's correct
    y_top_tensor = torch.tensor(y_top,device='cuda:0').repeat(lin_vel.size(dim=0))
    y_bottom = 13.8 # check if it's correct
    y_bottom_tensor = torch.tensor(y_bottom,device='cuda:0').repeat(lin_vel.size(dim=0))
    # Distance from center of the rover to the side (centimeters):
    x_side = 10.1 # check if it's correct

    # Calculate radius for each robot
    radius = torch.where(ang_vel != 0, torch.div(torch.abs(lin_vel),torch.abs(ang_vel))*100,torch.zeros(lin_vel.size(dim=0),device='cuda:0'))

    # Initiate zero tensors
    motor_velocities = torch.zeros(lin_vel.size(dim=0),6,device='cuda:0')
    steering_angles = torch.zeros(lin_vel.size(dim=0),6,device='cuda:0') ################### Hvorfor ikke ang_vel? ########################

    #         """
    #         Steering angles conditions 
    #         """
    #steering_condition0 = (ang_vel == 0)
    steering_condition1 = (radius <= x_side)
    steering_condition2 = ((torch.logical_not(radius <= x_side)) & (((ang_vel > 0) & ((torch.sign(lin_vel) > 0))) | ((ang_vel < 0) & ((torch.sign(lin_vel)) < 0))))
    steering_condition3 = ((torch.logical_not(radius <= x_side)) & (((ang_vel < 0) & ((torch.sign(lin_vel) > 0))) | ((ang_vel > 0) & ((torch.sign(lin_vel)) < 0))))
    #         """
    #         Steering angles calculation 
    #         """   
    # If the ang_vel is 0, the steering angles is set to 0:
    #steering_angles[:,0] = torch.where(steering_condition0, 0, steering_angles[:,0])
    #steering_angles[:,1] = torch.where(steering_condition0, 0, steering_angles[:,1])
    #steering_angles[:,2] = torch.where(steering_condition0, 0, steering_angles[:,2])
    #steering_angles[:,3] = torch.where(steering_condition0, 0, steering_angles[:,3])
    #steering_angles[:,4] = torch.where(steering_condition0, 0, steering_angles[:,4])
    #steering_angles[:,5] = torch.where(steering_condition0, 0, steering_angles[:,5])
    
    # If the turning point is within the chassis of the robot, turn on the spot:
    turn_on_the_spot_top = torch.tensor(torch.atan2(y_top,x_side),device='cuda:0').repeat(lin_vel.size(dim=0))
    turn_on_the_spot_bottom = torch.tensor(torch.atan2(y_bottom,x_side),device='cuda:0').repeat(lin_vel.size(dim=0))
    steering_angles[:,0] = torch.where(steering_condition1, turn_on_the_spot_top, steering_angles[:,0])
    steering_angles[:,1] = torch.where(steering_condition1, -turn_on_the_spot_top, steering_angles[:,1])
    #steering_angles[:,2] = torch.where(steering_condition1, 0, steering_angles[:,2])
    #steering_angles[:,3] = torch.where(steering_condition1 0, steering_angles[:,3])
    steering_angles[:,4] = torch.where(steering_condition1, -turn_on_the_spot_bottom, steering_angles[:,4])
    steering_angles[:,5] = torch.where(steering_condition1, turn_on_the_spot_bottom, steering_angles[:,5])
    
    # Steering angles if turning anticlockwise moving forward or clockwise moving backwards
    steering_angles[:,0] = torch.where(steering_condition2, -torch.atan2(y_top_tensor,(radius-x_side)), steering_angles[:,0])
    steering_angles[:,1] = torch.where(steering_condition2, -torch.atan2(y_top_tensor,(radius+x_side)), steering_angles[:,1])
    #steering_angles[:,2] = torch.where(steering_condition2, 0, steering_angles[:,2])
    #steering_angles[:,3] = torch.where(steering_condition2, 0, steering_angles[:,3])
    steering_angles[:,4] = torch.where(steering_condition2, torch.atan2(y_bottom_tensor,(radius-x_side)), steering_angles[:,4])
    steering_angles[:,5] = torch.where(steering_condition2, torch.atan2(y_bottom_tensor,(radius+x_side)), steering_angles[:,5])

    # Steering angles if turning clockwise moving forward or anticlockwise moving backwards
    steering_angles[:,0] = torch.where(steering_condition3,torch.atan2(y_top_tensor,(radius+x_side)), steering_angles[:,0])
    steering_angles[:,1] = torch.where(steering_condition3,torch.atan2(y_top_tensor,(radius-x_side)), steering_angles[:,1])
    #steering_angles[:,2] = torch.where(steering_condition3, 0, steering_angles[:,2])
    #steering_angles[:,3] = torch.where(steering_condition3, 0, steering_angles[:,3])
    steering_angles[:,4] = torch.where(steering_condition3,-torch.atan2(y_bottom_tensor,(radius+x_side)), steering_angles[:,4])
    steering_angles[:,5] = torch.where(steering_condition3,-torch.atan2(y_bottom_tensor,(radius-x_side)), steering_angles[:,5])



    #    
    #  Motor speeds conditions
    #  
    velocity_condition0 = (ang_vel == 0)
    velocity_condition1 = (radius <= x_side) & (ang_vel > 0)
    velocity_condition2 = (radius <= x_side) & (ang_vel < 0) #  elif radius[idx] <= x_side and ang_vel[idx] < 0: 
    velocity_condition3 = torch.logical_not((radius <= x_side)) & (ang_vel > 0)# ang_vel[idx] > 0:
    velocity_condition4 = torch.logical_not((radius <= x_side)) & (ang_vel < 0)# ang_vel[idx] < 0:
    #         """
    #         Motor speeds calculation 
    #         """
    # Speed moving forward/backward = linear velocity
    motor_velocities[:,0] = torch.where(velocity_condition0, lin_vel, motor_velocities[:,0])
    motor_velocities[:,1] = torch.where(velocity_condition0, lin_vel, motor_velocities[:,1])
    motor_velocities[:,2] = torch.where(velocity_condition0, lin_vel, motor_velocities[:,2])
    motor_velocities[:,3] = torch.where(velocity_condition0, lin_vel, motor_velocities[:,3])
    motor_velocities[:,4] = torch.where(velocity_condition0, lin_vel, motor_velocities[:,4])
    motor_velocities[:,5] = torch.where(velocity_condition0, lin_vel, motor_velocities[:,5])

    # Speed turning in place (counter clockwise), velocity of corner wheels = angular velocity 
    frontLeft = torch.sqrt((y_top*y_top)+(x_side*x_side))*abs(ang_vel)
    rearLeft = torch.sqrt((y_bottom*y_bottom)+(x_side*x_side))*abs(ang_vel)
    centerLeft = x_side*abs(ang_vel)
    relationCenterFront = centerLeft/frontLeft # relation between corner wheel and center wheel velocity (center wheels slower)
    relationRearFront = rearLeft/frontLeft
    motor_velocities[:,0] = torch.where(velocity_condition1, -torch.abs(ang_vel), motor_velocities[:,0])
    motor_velocities[:,1] = torch.where(velocity_condition1, torch.abs(ang_vel), motor_velocities[:,1])
    motor_velocities[:,2] = torch.where(velocity_condition1, -torch.abs(ang_vel)*relationCenterFront, motor_velocities[:,2])
    motor_velocities[:,3] = torch.where(velocity_condition1, torch.abs(ang_vel)*relationCenterFront, motor_velocities[:,3])
    motor_velocities[:,4] = torch.where(velocity_condition1, -torch.abs(ang_vel)*relationRearFront, motor_velocities[:,4])
    motor_velocities[:,5] = torch.where(velocity_condition1, torch.abs(ang_vel)*relationRearFront, motor_velocities[:,5])

    # Speed turning in place (clockwise), velocity of corner wheels = angular velocity 
    frontLeft = torch.sqrt((y_top*y_top)+(x_side*x_side))*abs(ang_vel)
    rearLeft = torch.sqrt((y_bottom*y_bottom)+(x_side*x_side))*abs(ang_vel)
    centerLeft = x_side*abs(ang_vel)
    relationCenterFront = centerLeft/frontLeft # relation between corner wheel and center wheel velocity (center wheels slower)
    relationRearFront = rearLeft/frontLeft

    motor_velocities[:,0] = torch.where(velocity_condition2, torch.abs(ang_vel),   motor_velocities[:,0])
    motor_velocities[:,1] = torch.where(velocity_condition2, -torch.abs(ang_vel), motor_velocities[:,1])
    motor_velocities[:,2] = torch.where(velocity_condition2, torch.abs(ang_vel)*relationCenterFront, motor_velocities[:,2])
    motor_velocities[:,3] = torch.where(velocity_condition2, -torch.abs(ang_vel)*relationCenterFront, motor_velocities[:,3])
    motor_velocities[:,4] = torch.where(velocity_condition2, torch.abs(ang_vel)*relationRearFront, motor_velocities[:,4])
    motor_velocities[:,5] = torch.where(velocity_condition2, -torch.abs(ang_vel)*relationRearFront, motor_velocities[:,5])

    # Speed turning anticlockwise moving forward/backward, velocity of frontRight wheel = linear velocity 
    frontLeft = (torch.sqrt((y_top_tensor*y_top_tensor)+((radius-x_side)*(radius-x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    frontRight = (torch.sqrt((y_top_tensor*y_top_tensor)+((radius+x_side)*(radius+x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    relationFront = frontLeft/frontRight # relation of speed between the front wheels (frontLeft is slower)
    rearLeft = (torch.sqrt((y_bottom_tensor*y_bottom_tensor)+((radius-x_side)*(radius-x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    rearRight = (torch.sqrt((y_bottom_tensor*y_bottom_tensor)+((radius+x_side)*(radius+x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    relationRear = rearLeft/rearRight # relation of speed between the front wheels (frontLeft is slower)
    centerLeft = ((radius-x_side)*torch.abs(ang_vel))*torch.sign(lin_vel)
    centerRight = ((radius+x_side)*torch.abs(ang_vel))*torch.sign(lin_vel)
    relationCenter = centerLeft/centerRight # relation of speed between the center wheels (centerLeft is slower)
    relationCenterFront = centerRight/frontRight # relation between center and front wheels (center is slower)
    relationRearFront = rearRight/frontRight
    
    motor_velocities[:,0] = torch.where(velocity_condition3, lin_vel*relationFront, motor_velocities[:,0])
    motor_velocities[:,1] = torch.where(velocity_condition3, lin_vel, motor_velocities[:,1])
    motor_velocities[:,2] = torch.where(velocity_condition3, lin_vel*relationCenterFront*relationCenter, motor_velocities[:,2])
    motor_velocities[:,3] = torch.where(velocity_condition3, lin_vel*relationCenterFront, motor_velocities[:,3])
    motor_velocities[:,4] = torch.where(velocity_condition3, lin_vel*relationRearFront*relationRear, motor_velocities[:,4])
    motor_velocities[:,5] = torch.where(velocity_condition3, lin_vel*relationRearFront, motor_velocities[:,5])

    # Speed turning clockwise moving forward/backward, velocity of frontLeft wheel = linear velocity
    frontLeft = (torch.sqrt((y_top_tensor*y_top_tensor)+((radius+x_side)*(radius+x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    frontRight = (torch.sqrt((y_top_tensor*y_top_tensor)+((radius-x_side)*(radius-x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    relationFront = frontRight/frontLeft # relation of speed between the front wheels (frontRight is slower)
    rearLeft = (torch.sqrt((y_bottom_tensor*y_bottom_tensor)+((radius+x_side)*(radius+x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    rearRight = (torch.sqrt((y_bottom_tensor*y_bottom_tensor)+((radius-x_side)*(radius-x_side)))*torch.abs(ang_vel))*torch.sign(lin_vel)
    relationRear = rearRight/rearLeft # relation of speed between the front wheels (frontRight is slower)
    centerLeft = ((radius+x_side)*torch.abs(ang_vel))*torch.sign(lin_vel)
    centerRight = ((radius-x_side)*torch.abs(ang_vel))*torch.sign(lin_vel)
    relationCenter = centerRight/centerLeft # relation of speed between the center wheels (centerRight is slower)
    relationCenterFront = centerLeft/frontLeft # relation between center and front wheels (center is slower)
    relationRearFront = rearLeft/frontLeft
    
    motor_velocities[:,0] = torch.where(velocity_condition4, lin_vel, motor_velocities[:,0])
    motor_velocities[:,1] = torch.where(velocity_condition4, lin_vel*relationFront, motor_velocities[:,0])
    motor_velocities[:,2] = torch.where(velocity_condition4, lin_vel*relationCenterFront, motor_velocities[:,0])
    motor_velocities[:,3] = torch.where(velocity_condition4, lin_vel*relationCenterFront*relationCenter, motor_velocities[:,0])
    motor_velocities[:,4] = torch.where(velocity_condition4, lin_vel*relationRearFront, motor_velocities[:,0])
    motor_velocities[:,5] = torch.where(velocity_condition4, lin_vel*relationRearFront*relationRear, motor_velocities[:,0])
    
    return steering_angles, motor_velocities

