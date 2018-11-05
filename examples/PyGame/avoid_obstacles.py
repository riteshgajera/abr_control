"""
Running operational space control with the PyGame display, using the
obstacle avoidance signal. The obstacle location can be moved
by clicking on the background.
"""
import numpy as np

from abr_control.arms import threejoint as arm
# from abr_control.arms import twojoint as arm
from abr_control.interfaces import PyGame
from abr_control.controllers import OSC, signals


# initialize our robot config
robot_config = arm.Config(use_cython=True)
# create our arm simulation
arm_sim = arm.ArmSim(robot_config)


def on_click(self, mouse_x, mouse_y):
    self.circles[0][0] = mouse_x
    self.circles[0][1] = mouse_y


# create our interface
interface = PyGame(robot_config, arm_sim,
                   on_click=on_click)
interface.connect()

# create operational space controller
ctrlr = OSC(robot_config, kp=20, vmax=10)
# create avoid obstacles additive controller
avoid = signals.AvoidObstacles(robot_config, threshold=1)

# create an obstacle
interface.add_circle(xyz=[0, 0, 0], radius=.2)

# create a target [x, y, z]]
target_xyz = [0, 2, 0]
# create a target orientation [alpha, beta, gamma]
target_angles = [0, 0, 0]
interface.set_target(target_xyz)

# control (x, y) out of [x, y, z, alpha, beta, gamma]
ctrlr_dof = [True, True, False, False, False, False]


try:
    print('\nSimulation starting...')
    print('Click to move the obstacle.\n')

    count = 0
    while 1:
        # get arm feedback
        feedback = interface.get_feedback()
        hand_xyz = robot_config.Tx('EE', feedback['q'])

        target = np.hstack([target_xyz, target_angles])
        # generate an operational space control signal
        u = ctrlr.generate(
            q=feedback['q'],
            dq=feedback['dq'],
            target=target,
            ctrlr_dof=ctrlr_dof,
            )

        # add in obstacle avoidance
        obs_xy = interface.get_mousexy()
        if obs_xy is not None:
            avoid.set_obstacles(obstacles=[[obs_xy[0], obs_xy[1], 0, .2]])
        u += avoid.generate(q=feedback['q'])

        # apply the control signal, step the sim forward
        interface.send_forces(
            u, update_display=True if count % 20 == 0 else False)

        # change target location once hand is within
        # 5mm of the target
        if (np.sqrt(np.sum((target_xyz - hand_xyz)**2)) < .005):
            target_xyz = np.array([
                np.random.random() * 2 - 1,
                np.random.random() * 2 + 1,
                0])
            # update the position of the target
            interface.set_target(target_xyz)

        count += 1

finally:
    # stop and reset the simulation
    interface.disconnect()

    print('Simulation terminated...')
