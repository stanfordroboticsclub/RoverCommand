

from __future__ import division

import time
import Tkinter as tk
from Tkinter import *
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

from math import sin,cos,pi


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
        self.radius = radius

class Point:
    def __init__(self):
        pass
    
    @classmethod
    def from_gps(cls, mp, lat,lon):
        point = cls()
        point.map = mp
        point.latitude = lat
        point.longitude = lon
        point.plot = None
        return point

    @classmethod
    def from_map(cls, mp, x,y):
        point = cls()
        point.map = mp
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
        y = self.map.size[0] * (self.latitude - self.map.top_left[0]) / ( self.map.bottom_right[0] - self.map.top_left[0])
        x = self.map.size[1] * (self.longitude - self.map.top_left[1]) / ( self.map.bottom_right[1] - self.map.top_left[1])
        return (y,x)

    def xy(self):
        pass

class GPSPannel:

    def __init__(self):

        #### config
        EQuad = Map('maps/zoomed_small.gif', (949, 1440), 
                     (37.430638, -122.176173), (37.426803, -122.168855))

        campus = Map('maps/campus.gif', (750, 1160), 
                     (37.432565, -122.180000), (37.421642, -122.158724))

        oval = Map('maps/oval.gif', (949, 1440), 
                     ((37.432543, -122.170674), (37.429054, -122.167716 ))

        zoomed_oval = Map('maps/zoomed_oval.gif', (750, 1160), 
                     (37.431282, -122.170513), (37.429127, -122.168238))


        self.map = campus


        self.base_pt = None
        self.rover_pt = None
        self.selected_pt = None
        self.arrow = None
        self.pub_pt = None


        ## UDPComms
        self.gps  = Subscriber(8280, timeout=2)
        self.gyro = Subscriber(8870, timeout=1)
        self.gps_base = Subscriber(8290, timeout=2)

        # publishes the point the robot should be driving to
        self.target_pub = Publisher(8310)

        # obstacles from the interface, displayed pink trasparent
        self.obstacles = []
        self.obstacles_pub = Publisher(9999)

        # obstacles from the robots sensors, displayed red tranparent.
        self.auto_obstacle_sub = Publisher(9999)

        # the path the autonomous module has chosen, drawn as blue lines
        self.path_sub = Subscriber(9999)


        ### tkinter setup
        self.root = tk.Tk()
        self.listbox = tk.Listbox(self.root)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical")
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.grid(row=4, column=0)


        ### label display
        self.gps_data = tk.StringVar()
        tk.Label(self.root, textvariable = self.lat_var).grid()
        self.gps_data.set("Lat: ")


        ### numeric input display
        tk.Label(self.root, text="Latitude: ").grid(row=0, column=0)
        tk.Label(self.root, text="Longitude: ").grid(row=0, column=2)
        self.e1 = tk.Entry(self.root)
        self.e2 = tk.Entry(self.root)
        self.e1.grid(row=0 ,column=1)
        self.e2.grid(row=0, column=3)

        tk.Button(self.root, text='Create Point',command=self.plot_numeric_point).grid(row=0, column=4)

        tk.Button(self.root, text='Create Obstacle',command=self.plot_numeric_point).grid(row=0, column=4)

        tk.Button(self.root, text='Plot Course',command=self.plot_numeric_point).grid(row=0, column=4)
        tk.Button(self.root, text='Run Autonomy',command=self.plot_numeric_point).grid(row=0, column=4)
        tk.Button(self.root, text='STOP Autonomy',command=self.plot_numeric_point).grid(row=0, column=4)

        ### point library display
        self.pointLibrary = {}
        tk.Label(self.root, text="Point Library").grid(row=1, column=0)
        self.listbox.grid(row=2, column=0)
        # tk.Button(self.root, text='Delete Point', command=self.del_point(self.selected_pt)).grid(row=5, column=0)
        self.numPoints = 0;

        ### canvas display
        self.canvas=tk.Canvas(self.root, width= self.map.size[1], height= self.map.size[0])
        self.canvas.grid(row=1, column=1, rowspan=10, columnspan=10)

        self.canvas.create_image(0, 0, image=self.map.image, anchor=tk.NW)


        # none, waypoint, obstacle, obstacle_radius
        self.mouse_mode = "none"
        self.canvas.bind("<Button-1>", self.mouse_callback)

        self.root.after(50, self.update)
        self.root.mainloop()


    def update_rover(self):
        try:
            rover = self.gps.get()
        except timeout:
            print("GPS TIMED OUT")
        else:
            if self.rover_pt is not None:
                self.del_point(self.rover_pt)

            self.rover_pt = self.plot_point(rover['lat'], rover['lon'], 3, '#ff6400')

            if rover['local'][0]:
                print("x", rover['local'][1], "y", rover['local'][2])

        try:
            base =  self.gps_base.get()
        except timeout:
            pass
            print("GPSBase TIMED OUT")
        else:
            if self.base_pt is not None:
                self.del_point(self.base_pt)
            self.base_pt = self.plot_point(base['lat'], base['lon'], 3, '#ff0000')

            
        if self.arrow is not None:
            self.canvas.delete(self.arrow)


        angle = self.gyro.get()['angle'][0]
        y,x = self.gps_to_map( (rover['lat'], rover['lon']) )
        r = 20
        self.arrow = self.canvas.create_line(x, y, x + r*sin(angle * pi/180),
                                                   y - r*cos(angle * pi/180),
                                                      arrow=tk.LAST)

    def update_listbox(self):
        self.items = self.listbox.curselection()
        for i in self.items:
            title = self.listbox.get(i)
            self.selected_pt = self.plot_selected_point(self.pointLibrary[title]["latitude"], self.pointLibrary[title]["longitude"])


    def update(self):
        self.update_listbox()
        self.update_rover()

        if self.pub_pt is not None:
            self.target_pub.send([self.lat_selected, self.lon_selected] )

        self.obstacles_pub.send(self.obstacles)

        self.root.after(50, self.update)


    def mouse_callback(self, event):
        print "clicked at", event.x, event.y

        if self.mouse_mode == "waypoint":
            self.lat_click, self.lon_click = self.map_to_gps(event.x, event.y)

            self.new_point(self.lat_click, self.lon_click)
            self.selected_pt = self.plot_selected_point(self.lat_click, self.lon_click)

        elif self.mouse_mode == "obstacle":
            self.map_to_gps(event.x, event.y)
            pass
            self.mouse_mode = "obstacle_radius"

        elif self.mouse_mode == "obstacle_radius":
            self.map_to_gps(event.x, event.y)
            pass
            self.mouse_mode = "waypoint"
        else:
            print "ERROR"

    def plot_point(self, point, radius, color):
        if point.plot != None:
            self.del_point(point)
        r = radius
        y,x = point.map()
        point.plot = self.canvas.create_oval( x + r, y + r , x - r , y - r, fill=color)

    def del_point(self, point):
        self.canvas.delete(point.plot)

    def plot_numeric_point(self):
        self.new_point(float(self.e1.get()), float(self.e2.get()))
        self.plot_selected_point(float(self.e1.get()), float(self.e2.get()))

    def new_point(self, lat, lon):

        self.lat_new, self.lon_new = lat, lon
        # if self.pub_pt is not None:
        #    self.del_point(self.pub_pt)
        self.pub_pt = self.plot_point(lat, lon, 3, 'cyan')
        self.pub_pt = Point("Point " + str(self.numPoints), self.lat_new, self.lon_new, self.pub_pt)
        self.listbox.insert("end", self.pub_pt.title)
        localPoint = {"plotPoint" : self.pub_pt,
                      "latitude" : self.pub_pt.latitude,
                      "longitude" : self.pub_pt.longitude,
                      }
        self.pointLibrary[self.pub_pt.title] = localPoint
        self.numPoints += 1

    def plot_selected_point(self, lat, lon):
        self.lat_selected = lat
        self.lon_selected = lon
        if self.selected_pt is not None:
            self.del_point(self.selected_pt.plotPoint)

        self.selected_pt = self.plot_point(lat, lon, 8, 'purple')
        self.selected_pt = Point("Point " + str(self.numPoints), self.lat_selected, self.lon_selected, self.selected_pt)
        return self.selected_pt


if __name__ == "__main__":
    a = GPSPannel()

