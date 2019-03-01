import os
import pygame
from UDPComms import Publisher

os.environ["SDL_VIDEODRIVER"] = "dummy"
arm_vel = Publisher(8410)

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

# Prints the values for axis0
while True:
    pygame.event.pump()

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

    print("button")
    for i in range(14):
        print(i, pygame.joystick.Joystick(0).get_button(i))
    print("axis")
    for i in range(12):
        print(i, pygame.joystick.Joystick(0).get_axis(i))

    hat = pygame.joystick.Joystick(0).get_hat(0)

    target_vel = {"x": r_side,
                  "y": r_forward,
                  "z": (r_trigger - l_trigger)/2,
                  "yaw": l_side,
                  "pitch": l_forward,
                  "roll": (r_shoulder - l_shoulder),
                  "grip": cross - square,
                  "hat": hat}

    print(target_vel)
    arm_vel.send(target_vel)

    pygame.time.wait(100)
