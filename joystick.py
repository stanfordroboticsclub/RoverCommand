import os
import pygame
from UDPComms import Publisher

os.environ["SDL_VIDEODRIVER"] = "dummy"
a = Publisher(8830)

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
    forward = (pygame.joystick.Joystick(0).get_axis(5))
    twist = (pygame.joystick.Joystick(0).get_axis(2))
    on = (pygame.joystick.Joystick(0).get_button(5))

    if on:
        a.send({'f':-150*forward,'t':-80*twist})
    else:
        a.send({'f':0,'t':0})

    pygame.time.wait(100)
