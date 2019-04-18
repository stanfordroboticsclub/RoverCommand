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

#mode_file = open("/tmp/robot_joystick_mode.txt","r")

# Prints the values for axis0
while True:

#    mode_file.seek(0)
#    mode = mode_file.read()
    mode = 'drive'

    pygame.event.pump()

    if mode.startswith('drive'):
        forward = (pygame.joystick.Joystick(0).get_axis(3))
        twist = (pygame.joystick.Joystick(0).get_axis(2))
        on = (pygame.joystick.Joystick(0).get_button(5))

        if on:
            print({'f':-150*forward,'t':-80*twist})
            drive_pub.send({'f':-150*forward,'t':-80*twist})
        else:
            drive_pub.send({'f':0,'t':0})
    else:
        pass

    pygame.time.wait(100)
