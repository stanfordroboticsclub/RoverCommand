from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

import math, time


class Obstacle:
    def __init__(self, dictionary):
        self.lat = dictionary['lat']
        self.lon = dictionary['lon']
        self.radius = dictionary['radius']



class PathPlan:
    def __init__(self):
        self.gps  = Subscriber(8280, timeout=2)
        self.gyro = Subscriber(8220, timeout=1)

        # publishes the point the robot should be driving to
        # self.auto_control  = {"target": {"lat":0, "lon":0}, "command":"off"}
        self.auto_control_sub = Subscriber(8310)

        # the path the autonomous module has chosen, drawn as blue lines
        self.path_pub = Publisher(8320)

        # obstacles from the interface, displayed pink trasparent
        self.obstacles_sub = Subscriber(8330, timeout=3)

        # obstacles from the robots sensors, displayed red tranparent.
        self.auto_obstacle_sub = Publisher(8340)

        self.next_point = Publisher(8350)

        while 1:
            self.update()
            time.sleep(1)

    def update(self):
        command =  self.auto_obstacle_sub.get()

        if command['command'] == 'off':
            pass
        elif command['command'] == 'path':
            self.plan_path()
        elif command['command'] == 'auto':
            self.plan_path()

    def plan_path(self):
        pass


if __name__ == "__main__":
    a = PathPlan()
        

