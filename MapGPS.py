

from __future__ import division

import time
import Tkinter as tk
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

from math import sin,cos,pi



# zoomed out
# top left: 37.432565, -122.180000
# bottom right: 37.421642, -122.158724

# zoomed in:
# top left:37.430638, -122.176173
# bottom right:  37.426803, -122.168855


class GPSPannel:



    def __init__(self):

        #### config
        # self.top_left =     (37.430638, -122.176173)
        # self.bottom_right = (37.426803, -122.168855)

        self.top_left =     (37.432565, -122.180000)
        self.bottom_right = (37.421642, -122.158724)

        self.rover_pt = None
        self.arrow = None
        self.pub_pt = None

        # self.map_size = (949, 1440) ## (height, width)
        self.map_size = (750, 1160) ## (height, width)
        ### self.smaller_map = self.map.zoom(2, 2).subsample(3, 3)
        ### self.smaller_map = self.map.subsample(2, 2)

        # self.map_file = 'maps/zoomed_small.gif'
        self.map_file = 'maps/campus.gif'

        ## UDPComms
        self.gps =      Subscriber(8280, timeout=2)
        self.gps_base = Subscriber(8290, timeout=2)
        self.target_pub = Publisher(8310)

        self.gyro = Subscriber(8870, timeout=1)
        self.angle = 0

        ### tkinter setup
        self.root = tk.Tk()
        self.lat_var = tk.StringVar()
        self.lon_var = tk.StringVar()

        ### label display
        self.lat = tk.Label(self.root, textvariable = self.lat_var)
        self.lon = tk.Label(self.root, textvariable = self.lon_var)

        self.lat_var.set("Lat: ")
        self.lon_var.set("Lon: ")


        ### numeric input display
        tk.Label(self.root, text="Latitude").grid(row=0, column=0)
        tk.Label(self.root, text="Longitude").grid(row=0, column=2)
        self.e1 = tk.Entry(self.root)
        self.e2 = tk.Entry(self.root)
        self.e1.grid(row=0 ,column=1)
        self.e2.grid(row=0, column=3)
        tk.Button(self.root, text='Create Point',command=self.plot_numeric_point).grid(row=0, column=4)

        ### canvas display
        self.canvas=tk.Canvas(self.root, width= self.map_size[1], height= self.map_size[0])
        self.canvas.grid(row=1, column=0, rowspan=10, columnspan=10)

        self.map = tk.PhotoImage(file=self.map_file)
        self.canvas.create_image(0, 0, image=self.map, anchor=tk.NW)

        self.canvas.bind("<Button-1>", self.mouse_callback)

        self.root.after(50, self.update)
        self.root.mainloop()

    def update(self):

        try:
            rover = self.gps.get()
        except timeout:
            print("GPS TIMED OUT")
        else:
            if self.rover_pt is not None:
                self.del_point(self.rover_pt)
            self.rover_pt = self.plot_point(rover['lat'], rover['lon'], '#ff6400')

            if rover['local'][0]:
                print("x", rover['local'][1], "y", rover['local'][2])

        try:
            base =  self.gps_base.get()
        except timeout:
            print("GPS TIMED OUT")
        else:
            if self.base_pt is not None:
                self.del_point(self.base_pt)
            self.base_pt = self.plot_point(rover['lat'], rover['lon'], '#ff0000')

            
        # if self.arrow is not None:
        #     self.canvas.delete(self.arrow)


        # y,x = self.gps_to_map( (msg['lat'], msg['lon']) )
        # r = 20
        # self.arrow = self.canvas.create_line(x, y, x + r*sin(self.angle * pi/180),
        #                                            y - r*cos(self.angle * pi/180),
        #                                               arrow=tk.LAST)

        if self.pub_pt is not None:
            self.target_pub.send([self.lat_new, self.lon_new] )

        self.root.after(50, self.update)


    def mouse_callback(self, event):

        print "clicked at", event.x, event.y
        self.map_to_gps(event.x, event.y)
        self.lat_click, self.lon_click = self.map_to_gps(event.x, event.y)

        self.new_point(self.lat_click, self.lon_click)


    def gps_to_map(self, gps_pos):
        # y = lat = 0
        # x = lon = 1
        y = self.map_size[0] * (gps_pos[0] - self.top_left[0]) / ( self.bottom_right[0] - self.top_left[0])
        x = self.map_size[1] * (gps_pos[1] - self.top_left[1]) / ( self.bottom_right[1] - self.top_left[1])
        return (y,x)

    def plot_point(self, lat, lon, color):
        r = 3
        y,x = self.gps_to_map( (lat, lon) )
        print x,y
        return self.canvas.create_oval( x + r, y +r , x -r , y-r, fill=color)

    def del_point(self, point):
        self.canvas.delete(point)

    def map_to_gps(self, x, y):
        lat_click = (y * (self.bottom_right[0] - self.top_left[0]) / (self.map_size[0])) + self.top_left[0]
        lon_click = (x * (self.bottom_right[1] - self.top_left[1]) / (self.map_size[1])) + self.top_left[1]
        return lat_click, lon_click

    def plot_numeric_point(self):
        self.new_point(float(self.e1.get()), float(self.e2.get()))

    def new_point(self, lat, lon):

        self.lat_new, self.lon_new = lat, lon
        if self.pub_pt is not None:
            self.del_point(self.pub_pt)

        self.pub_pt = self.plot_point(lat, lon, 'cyan')



if __name__ == "__main__":
    a = GPSPannel()

