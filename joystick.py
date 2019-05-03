import os
import pygame
from UDPComms import Publisher

os.environ["SDL_VIDEODRIVER"] = "dummy"
drive_pub = Publisher(8830)
arm_pub = Publisher(8410)

pygame.display.init()
pygame.joystick.init()

# wait untill joystick is connected
while 1:
    try:
        pygame.joystick.Joystick(0).init()
        break
    except pygame.error:
        pygame.time.wait(500)

# Prints the joystick's name
JoyName = pygame.joystick.Joystick(0).get_name()
print("Name of the joystick:")
print(JoyName)
# Gets the number of axes
JoyAx = pygame.joystick.Joystick(0).get_numaxes()
print("Number of axis:")
print(JoyAx)

mode_file = open("/tmp/robot_joystick_mode.txt","r")

# Prints the values for axis0
while True:

    mode_file.seek(0)
    mode = mode_file.read()
    
    pygame.event.pump()

    if mode.startswith('drive'):
        forward = (pygame.joystick.Joystick(0).get_axis(1))
        twist = (pygame.joystick.Joystick(0).get_axis(2))
        on = (pygame.joystick.Joystick(0).get_button(5))

        if on:
            drive_pub.send({'f':-150*forward,'t':-80*twist})
        else:
            drive_pub.send({'f':0,'t':0})

    if mode.startswith('arm'):
        r_forward  = -(pygame.joystick.Joystick(0).get_axis(5))
        r_side = (pygame.joystick.Joystick(0).get_axis(2))

        l_forward  = -(pygame.joystick.Joystick(0).get_axis(1))
        l_side = (pygame.joystick.Joystick(0).get_axis(0))

        r_shoulder  = (pygame.joystick.Joystick(0).get_button(5))
        l_shoulder  = (pygame.joystick.Joystick(0).get_button(4))

        r_trigger  = (pygame.joystick.Joystick(0).get_axis(4))
        l_trigger = (pygame.joystick.Joystick(0).get_axis(3))

        square  = (pygame.joystick.Joystick(0).get_button(0))
        cross  = (pygame.joystick.Joystick(0).get_button(1))
        circle  = (pygame.joystick.Joystick(0).get_button(2))
        triangle  = (pygame.joystick.Joystick(0).get_button(3))

        PS  = (pygame.joystick.Joystick(0).get_button(12)) 

        # print("button")
        # for i in range(14):
        #     print(i, pygame.joystick.Joystick(0).get_button(i))
        # print("axis")
        # for i in range(12):
        #     print(i, pygame.joystick.Joystick(0).get_axis(i))

        hat = pygame.joystick.Joystick(0).get_hat(0)

        reset = (PS == 1) and (triangle == 1)

        if(PS == 0):
              target_vel = {"x": l_side,
                      "y": l_forward,
                      "z": (r_trigger - l_trigger)/2,
                      "yaw": r_side,
                      "pitch": r_forward,
                      "roll": (r_shoulder - l_shoulder),
                      "grip": cross - square,
                      "hat": hat,
                      "reset": reset,
                      "trueXYZ": circle}
        else:
              target_vel = {"x": 0,
                      "y": 0,
                      "z": 0,
                      "yaw": 0,
                      "pitch": 0,
                      "roll": 0,
                      "grip": 0,
                      "hat": (0,0),
                      "reset": reset,
                      "trueXYZ": 0}
        print(target_vel)
        arm_pub.send(target_vel)
    else:
        pass

    pygame.time.wait(100)
