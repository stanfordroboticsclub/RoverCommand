

from __future__ import division

import time
import Tkinter as tk
from Tkinter import *
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

from math import sin,cos,pi,sqrt


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
        return (y,x)

    def xy(self):
        pass

class GPSPannel:

    def __init__(self):
        self.root = tk.Tk()
        #### config
        EQuad = Map('maps/zoomed_small.gif', (949, 1440), \
                     (37.430638, -122.176173), (37.426803, -122.168855))

        campus = Map('maps/campus.gif', (750, 1160), \
                     (37.432565, -122.180000), (37.421642, -122.158724))

        oval = Map('maps/oval.gif', (1, 1), \
                     (37.432543, -122.170674), (37.429054, -122.167716 ))

        zoomed_oval = Map('maps/zoomed_oval.gif', (1, 1), \
                     (37.431282, -122.170513), (37.429127, -122.168238))


        self.map = campus

        ## UDPComms
        self.gps  = Subscriber(8280, timeout=2)
        self.rover_pt = None

        self.gyro = Subscriber(8220, timeout=1)
        self.arrow = None

        self.gps_base = Subscriber(8290, timeout=2)
        self.base_pt = None

        # publishes the point the robot should be driving to
        self.auto_control  = {"target": {"lat":0, "lon":0}, "command":"off"}
        self.auto_control_pub = Publisher(8310)
        self.pub_pt = None

        # the path the autonomous module has chosen, drawn as blue lines
        self.path_sub = Subscriber(8320, timeout = 5)

        # obstacles from the interface, displayed pink trasparent
        self.obstacles = []
        self.obstacles_pub = Publisher(8330)

        # obstacles from the robots sensors, displayed red tranparent.
        self.auto_obstacle_sub = Publisher(8340)



        ### tkinter setup
        self.listbox = tk.Listbox(self.root)
        # self.scrollbar = tk.Scrollbar(self.root, orient="vertical")
        # self.scrollbar.config(command=self.listbox.yview)
        # self.scrollbar.grid(row=1, column=0)


        ### label display
        self.gps_data = tk.StringVar()
        tk.Label(self.root, textvariable = self.gps_data).grid(row=8, column=0, columnspan =6)
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

        self.canvas.bind("<Button-1>", self.mouse_callback)

        self.root.after(50, self.update)
        self.root.mainloop()

    def change_mouse_mode(self,mode):
        self.mouse_mode = mode

    def change_auto_mode(self,mode):
        assert (mode == "off") or (mode == 'auto') or (mode == 'plot')
        self.auto_control['command'] = mode


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
            else:
                self.plot_normal_point(point)


    def update_path(self):
        for line in self.path_lines:
            self.canvas.delete(line)
        self.path_lines = []
        try:
            path = self.path_sub.get()
        except timeout:
            pass
        else:
            points = [ Point.from_gps(self.map, p['lat'], p['lon']) for p in path]
            for a,b in zip( points[:-1], points[1:]):
                y1, x1 = a.map()
                y2, x2 = b.map()
                line = self.canvas.create_line(x1,x2,y1,y2, color='red')
                self.path_lines.append(line)


    def update(self):
        try:
            self.auto_mode_dis.set(self.auto_control['command'].upper())
            self.gps_data.set(self.mouse_mode)

            self.update_listbox()
            self.update_rover()
            self.update_path()

            self.auto_control_pub.send(self.auto_control)
            self.obstacles_pub.send(map(lambda x:x.serialize(), self.obstacles))
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

