

from __future__ import division

import time
import Tkinter as tk
from Tkinter import *
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

from math import sin,cos,pi,sqrt

from Queue import PriorityQueue
from collections import defaultdict


import networkx as nx


class Map:
    def __init__(self, fil, size, top_left, bottom_right):
        self.file = fil
        self.top_left = top_left
        self.bottom_right = bottom_right
        self.size = size
        self.image = tk.PhotoImage(file=self.file)

class Obstacle:
    def __init__(self, location, radius):
        self.location = location
        self.radius   = radius
    def serialize(self):
        gps = self.location.gps()
        return {"radius": self.radius, "lat": gps.latitude, "lon": gps.longitude}

class Point:
    def __init__(self):
        pass
    
    @classmethod
    def from_gps(cls, mp, lat,lon):
        point = cls()
        point._map = mp
        point.latitude = lat
        point.longitude = lon
        point.plot = None
        return point

    @classmethod
    def from_map(cls, mp, x,y):
        point = cls()
        point._map = mp
        point.latitude = (y * (mp.bottom_right[0] - mp.top_left[0]) / (mp.size[0])) + mp.top_left[0]
        point.longitude = (x * (mp.bottom_right[1] - mp.top_left[1]) / (mp.size[1])) + mp.top_left[1]
        point.plot = None
        return point

    @classmethod
    def from_xy(cls, mp, x_m,y_m):
        pass

    def gps(self):
        return (self.latitude,self.longitude)

    def map(self):
        # y = lat = 0
        # x = lon = 1
        y = self._map.size[0] * (self.latitude - self._map.top_left[0]) / ( self._map.bottom_right[0] - self._map.top_left[0])
        x = self._map.size[1] * (self.longitude - self._map.top_left[1]) / ( self._map.bottom_right[1] - self._map.top_left[1])
        return (int(y),int(x))

    def xy(self):
        pass


class AStar:

    def __init__(self, start, end, neigbour, heuristic):
        self.start = start
        self.end = end
        self.neigbour = neigbour
        self.heuristic = heuristic

        self.queue = PriorityQueue()
        self.queue.put(( heuristic(start,end), self.start))

        self.visited = set()

        self.came_from = {}

        self.gscore = defaultdict(lambda: float("inf"))
        self.gscore[self.start] = 0

        self.fscore = defaultdict(lambda: float("inf"))
        self.fscore[self.start] = heuristic(start,end)

    def run(self):
        # self.visit = []
        while not self.queue.empty():
            current = self.queue.get()[1]
            # if current in self.visit:
            #     raise
            # self.visit.append(current)
            print(current)
            # print('current',current, self.queue.qsize)
            if current == self.end:
                return self.reconstruct_path(current)

            self.visited.add(current)
            for neigbour in self.neigbour(current):
                # print('neigbour',neigbour)
                # print("visting neoughtou")
                if neigbour in self.visited:
                    # print("in visited")
                    continue
                tentative_gscore = self.gscore[current] + 1

                if neigbour not in self.queue.queue:
                    # print("adding to queu", neigbour)
                    self.queue.put(  (self.heuristic(neigbour,self.end),  neigbour) )
                    # print "ADDing", neigbour
                elif tentative_gscore >= gscore[neigbour]:
                    continue

                self.came_from[neigbour] = current
                self.gscore[neigbour] = tentative_gscore
                self.fscore[neigbour] = tentative_gscore + self.heuristic(neigbour, self.end)

    def reconstruct_path(self,current):
        print("PATH RECPNST")
        total_path = [current]
        while current != self.start:
            current = self.came_from[current]
            total_path.append(current)

        return total_path





class GPSPannel:

    def __init__(self):
        self.root = tk.Tk()
        #### config
        EQuad = Map('maps/zoomed_small.gif', (949, 1440), \
                     (37.430638, -122.176173), (37.426803, -122.168855))

        campus = Map('maps/campus.gif', (750, 1160), \
                     (37.432565, -122.180000), (37.421642, -122.158724))

        # oval = Map('maps/oval.gif', (1, 1), \
        #              (37.432543, -122.170674), (37.429054, -122.167716 ))

        zoomed_oval = Map('maps/zoomed_oval_copy.gif', (1936/2, 1616/2), \
                     (37.431282, -122.170513), (37.429127, -122.168238))


        # self.map = zoomed_oval
        self.map = zoomed_oval

        ## UDPComms
        self.gps  = Subscriber(8280, timeout=2)
        # self.rover_pt = None
        self.rover_pt = Point.from_gps(self.map, *self.map.bottom_right)

        self.gyro = Subscriber(8220, timeout=1)
        self.arrow = None

        self.gps_base = Subscriber(8290, timeout=2)
        self.base_pt = None

        # publishes the point the robot should be driving to
        self.auto_control  = {"target": {"lat":0, "lon":0}, "command":"off"}
        self.auto_control_pt = None
        # self.auto_control_pub = Publisher(8310)

        # the path the autonomous module has chosen, drawn as blue lines
        self.path = []
        self.path_pub = Publisher(8320)

        # obstacles from the interface, displayed pink trasparent
        self.obstacles = []
        self.obstacles_pub = Publisher(8330)

        # obstacles from the robots sensors, displayed red tranparent.
        self.auto_obstacle_sub = Subscriber(8340, timeout=5)



        ### tkinter setup
        self.listbox = tk.Listbox(self.root)
        # self.scrollbar = tk.Scrollbar(self.root, orient="vertical")
        # self.scrollbar.config(command=self.listbox.yview)
        # self.scrollbar.grid(row=1, column=0)


        ### label display
        self.gps_data = tk.StringVar()
        tk.Label(self.root, textvariable = self.gps_data).grid(row=9, column=0, columnspan =6)
        self.gps_data.set("")

        self.auto_mode_dis = tk.StringVar()
        tk.Label(self.root, textvariable = self.auto_mode_dis, font=("Courier", 44)).grid(row=0, column=0)
        self.auto_mode_dis.set("")


        ### numeric input display
        tk.Label(self.root, text="Lat: ").grid(row=0, column=1)
        tk.Label(self.root, text="Lon: ").grid(row=0, column=3)
        self.e1 = tk.Entry(self.root)
        self.e2 = tk.Entry(self.root)
        self.e1.grid(row=0 ,column=2)
        self.e2.grid(row=0, column=4)
        tk.Button(self.root, text='Create Point',command=self.plot_numeric_point).grid(row=0, column=5)

        tk.Button(self.root, text='Delete',     command=lambda: None ).grid(row=2, column=0)
        tk.Button(self.root, text='Waypoint',   command=lambda: self.change_mouse_mode('waypoint') ).grid(row=3, column=0)
        tk.Button(self.root, text='Obstacle',   command=lambda: self.change_mouse_mode('obstacle') ).grid(row=4, column=0)

        self.root.bind("<Escape>",                      lambda: self.change_mouse_mode('none'))

        tk.Button(self.root, text='Plot Course',command=lambda: self.change_auto_mode('plot')).grid(row=5, column=0)
        tk.Button(self.root, text='Auto',       command=lambda: self.change_auto_mode('auto')).grid(row=6, column=0)
        tk.Button(self.root, text='STOP',       command=lambda: self.change_auto_mode('off')).grid(row=7, column=0)

        ### point library display
        self.pointLibrary = {}
        self.listbox.grid(row=1, column=0)
        self.numPoints = 0;

        ### canvas display
        self.canvas=tk.Canvas(self.root, width= self.map.size[1], height= self.map.size[0])
        self.canvas.grid(row=1, column=1, rowspan=8, columnspan=5)

        self.canvas.create_image(0, 0, image=self.map.image, anchor=tk.NW)

        # none, waypoint, obstacle, obstacle_radius
        self.mouse_mode = "none"
        self.last_mouse_click = (0,0)
        self.temp_obstace = None

        self.path_lines = []

        self.canvas.bind("<Button-1>", self.mouse_callback)

        self.root.after(50, self.update)
        self.root.mainloop()

    def change_mouse_mode(self,mode):
        self.mouse_mode = mode

    def change_auto_mode(self,mode):
        assert (mode == "off") or (mode == 'auto') or (mode == 'plot')
        if mode == 'plot':
            self.update_path2()
        self.auto_control['command'] = mode


    def update_path2(self):

        def dist(a,b): 
            # print('dist', a, b)
            # print(a.map(), b.map())
            return sqrt((a.map()[0]-b.map()[0])**2 + (a.map()[1]-b.map()[1])**2)

        start = self.rover_pt
        end = self.auto_control_pt
        def octagon(osb):
            r = obs.radius * 1.6
            # return ( (0.7*r,0.7*r),(-0.7*r,-0.7*r), \
            #         (0.7*r,-0.7*r) , (-0.7*r,0.7*r),\
            #         (0,r),(0,-r), (r,0),(-r,0))

            return ( (0.7*r,0.7*r), (r,0), (0.7*r,-0.7*r), (0, -r), \
                    (-0.7*r, -0.7*r), (-r, 0), (-0.7*r, 0.7*r), (0,r))
                    

        possible_point = []
        for obs in self.obstacles:
            for u,j in octagon(obs):
                y,x = obs.location.map()
                point = Point.from_map(self.map, x+u, y+j)
                possible_point.append(point)

        # possible_point += [start, end]

        min_start = Point.from_map(self.map, -100000,-100000)
        min_end   = Point.from_map(self.map, -100000,-100000)
        start_i = 0
        end_i = 0

        # print possible_point
        # print "MIN", min_end, min_start

        for i,x in enumerate(possible_point):
            # print x, min_start, min_end
            if dist(x,start) < dist(start,min_start):
                min_start = x
                start_i = i
            if dist(x,  end) < dist(end,  min_end):
                min_end = x
                end_i = i


        self.path = [start]

        i = start_i
        while i!= end_i:
            self.path.append(possible_point[i])
            i = i+1%len(possible_point)

        self.path.append(end)

        # self.plot_point(min_end, 6, 'black')
        # self.plot_point(min_start, 6, 'white')

        self.path_lines = []
        for a,b in zip( self.path[:-1], self.path[1:]):
            y1, x1 = a.map()
            y2, x2 = b.map()
            line = self.canvas.create_line(x1,y1,x2,y2, fill='blue')
            self.path_lines.append(line)


    #def update_path(self):


    #    #TODO: time limmmtingin

    #        # margin = 10
    #        # obstacles = []
    #        # for ob in[Obstacle(x.location,x.radius+margin) for x in self.obstacles]:
    #        #     self.canvas.cr

    #    def collides(x,y):
    #        if x<=0: return True
    #        if y<=0: return True

    #        if x>=self.map.size[0]: return True
    #        if y>=self.map.size[1]: return True

    #        ids = self.canvas.find_overlapping(x,y, x+1, y+1)
    #        print(len(ids))
    #        for i in ids:
    #            if i in [x.location.point for x in self.obstacles]:
    #                return True
    #        return False

    #    def find_neighbours(coords):
    #        y,x = coords
    #        out = []
    #        for i,j in ((1,1), (-1,1), (1,-1), (-1,-1)):
    #            new_x = x+i
    #            new_y = y+j
    #            # if not collides(x,y):
    #            out.append((new_y, new_x))

    #        # print(out)
    #        return out

    #    dist = lambda a,b: sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

    #    start = self.rover_pt.map()
    #    end = self.auto_control_pt.map()
        
    #    print("running act")
    #    As = AStar(start, end, find_neighbours, dist)
    #    path = As.run()
    #    print("ran act")

    #    # TODO Stragihtend path

    #    print path

    #    for pl in self.path_lines:
    #        self.canvas.delete(pl)

    #    self.path_lines = []
    #    points = [ Point.from_map(self.map, p[0], p[1]) for p in path]
    #    for a,b in zip( points[:-1], points[1:]):
    #        y1, x1 = a.map()
    #        y2, x2 = b.map()
    #        line = self.canvas.create_line(x1,x2,y1,y2, color='red')
    #        self.path_lines.append(line)



    def update_rover(self):
        try:
            rover = self.gps.get()
        except timeout:
            pass
            # print("GPS TIMED OUT")
            self.gps_data.set("MODE: "+self.mouse_mode+", no gps data recived")
        else:
            self.rover_pt = Point.from_gps(self.map, rover['lat'], rover['lon'])
            self.plot_point(self.rover_pt, 3, '#ff6400')

            if rover['local'][0]:
                print("x", rover['local'][1], "y", rover['local'][2])

            self.gps_data.set("MODE: "+self.mouse_mode+", "+ str(rover) )

        try:
            base =  self.gps_base.get()
        except timeout:
            pass
            # print("GPSBase TIMED OUT")
        else:
            self.base_pt = Point.from_gps(self.map, base['lat'], base['lon'])
            self.plot_point(self.base_pt, 3, '#ff0000')

            
        if self.arrow is not None:
            self.canvas.delete(self.arrow)
        try:
            angle = self.gyro.get()['angle'][0]
        except:
            pass
        else:
            y,x = self.rover_pt.map()
            r = 20
            self.arrow = self.canvas.create_line(x, y, x + r*sin(angle * pi/180),
                                                       y - r*cos(angle * pi/180),
                                                          arrow=tk.LAST)

    def update_listbox(self):
        for i in range(self.numPoints):
            title = self.listbox.get(i)
            point = self.pointLibrary[title] 
            if i in self.listbox.curselection():
                self.plot_selected_point(point)
                self.auto_control['target'] = {'lat': point.gps()[0], 'lon':point.gps()[1]}
                self.auto_control_pt = point
            else:
                self.plot_normal_point(point)



    def update(self):
        try:
            self.auto_mode_dis.set(self.auto_control['command'].upper())
            self.gps_data.set(self.mouse_mode)

            self.update_listbox()
            self.update_rover()
            # self.update_path()

            # self.auto_control_pub.send(self.auto_control)
            self.path_pub.send([x.gps() for x in self.path])

            # self.obstacles_pub.send(map(lambda x:x.serialize(), self.obstacles))
        except:
            raise
        finally:
            self.root.after(50, self.update)


    def mouse_callback(self, event):
        print "clicked at", event.x, event.y

        if self.mouse_mode == "waypoint":
            waypoint = Point.from_map(self.map, event.x, event.y)
            self.new_waypoint(waypoint)
            self.mouse_mode = "none"

        elif self.mouse_mode == "obstacle":
            self.temp_obstace = Point.from_map(self.map, event.x, event.y)
            self.mouse_mode = "obstacle_radius"

        elif self.mouse_mode == "obstacle_radius":
            assert self.temp_obstace != None
            edge_point = Point.from_map(self.map, event.x, event.y)
            y,x = edge_point.map()
            center_y, center_x = self.temp_obstace.map()
            radius = sqrt((center_x-x)**2 + (center_y-y)**2)

            self.plot_point(self.temp_obstace, radius, "#FF0000", activestipple='gray50',  width=0)

            DIS_SCALE = 1

            self.obstacles.append(Obstacle(self.temp_obstace, DIS_SCALE * radius))
            self.temp_obstace = None

            self.mouse_mode = "none"

        elif self.mouse_mode == "none":
            print "nothing to do"

        else:
            print "ERROR"

    def plot_point(self, point, radius, color, **kwargs):
        if point.plot != None:
            self.del_point(point)
        r = radius
        y,x = point.map()
        point.plot = self.canvas.create_oval( x + r, y + r , x - r , y - r, fill=color, **kwargs)

    def del_point(self, point):
        self.canvas.delete(point.plot)

    def plot_numeric_point(self):
        new_numeric = Point.from_gps(self.map, float(self.e1.get()), float(self.e2.get()))
        self.new_waypoint(new_numeric)

    def new_waypoint(self, point):
        self.plot_normal_point(point)
        title = "Point " + str(self.numPoints)

        self.listbox.insert("end", title)
        self.pointLibrary[title] = point
        self.numPoints += 1

    def plot_selected_point(self, point):
        self.plot_point(point, 8, 'purple')

    def plot_normal_point(self, point):
        self.plot_point(point, 3, 'cyan')



if __name__ == "__main__":
    a = GPSPannel()

