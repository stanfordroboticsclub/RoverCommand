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
mode = "safe"
# Prints the values for axis0
while True:
#    print("running")
#    mode_file.seek(0)
#    mode = mode_file.read()
    
    pygame.event.pump()

    
    PS  = (pygame.joystick.Joystick(0).get_button(12)) 
    hat = pygame.joystick.Joystick(0).get_hat(0)

    if(PS and hat[1] == -1):
        mode = "safe"
    elif(PS and hat[1] == 1):
        mode = "drive"
    elif(PS and hat[0] == 1):
        mode = "arm"
    print(mode)

    if mode.startswith('drive'):
        forward_left = (pygame.joystick.Joystick(0).get_axis(1))
        forward_right = (pygame.joystick.Joystick(0).get_axis(5))
        twist = (pygame.joystick.Joystick(0).get_axis(2))
        forward_left = forward_left*abs(forward_left)
        twist = twist*abs(twist)
        on_right = (pygame.joystick.Joystick(0).get_button(5))
        on_left = (pygame.joystick.Joystick(0).get_button(4))


        r_trigger  = (pygame.joystick.Joystick(0).get_axis(4))
        l_trigger = (pygame.joystick.Joystick(0).get_axis(3))

        square  = (pygame.joystick.Joystick(0).get_button(0))
        cross  = (pygame.joystick.Joystick(0).get_button(1))
        circle  = (pygame.joystick.Joystick(0).get_button(2))
        triangle  = (pygame.joystick.Joystick(0).get_button(3))
        forward = 0
        turn = 0
        if on_left:
            forward = -forward_left
            turn = twist
        elif on_right:
            forward = -forward_right
            turn = twist
        vel = 1 if r_trigger > .5 else 0
        cur = 1 if l_trigger > .5 else 0
        drive_pub.send({'f':forward,'t':turn, 'power_left':square, 'power_back':cross, 'power_right':circle, 'power_mid': triangle,'vel':vel,'cur':cur})
        print({'f':forward,'t':turn, 'power_left':square, 'power_back':cross, 'power_right':circle, 'power_mid': triangle,'vel':vel,'cur':cur})
   
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
