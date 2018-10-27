

from __future__ import division

import time
import Tkinter as tk
from UDPComms import Subscriber



# zoomed out
# top left: 37.432565, -122.180000
# bottom right: 37.421642, -122.158724

# zoomed in:
# top left:37.430638, -122.176173
# bottom right:  37.426803, -122.168855


class GPSPannel:

    fields = "forward twist"
    typ = "ff"
    port = 8830

    def __init__(self):

        #### config
        self.top_left =     (37.430638, -122.176173)
        self.bottom_right = (37.426803, -122.168855)

        self.map_size = (949, 1440)
        self.map_file = 'maps/zoomed_small.gif'


        ### tkinter setup
        self.root = tk.Tk()
        self.lat_var = tk.StringVar()
        self.lon_var = tk.StringVar()

        ### label display
        self.lat = tk.Label(self.root, textvariable = self.lat_var)
        self.lon = tk.Label(self.root, textvariable = self.lon_var)

        self.lat_var.set("Lat: ")
        self.lon_var.set("Lon: ")

        self.lat.pack()
        self.lon.pack()

        ### canvas display
        self.canvas=tk.Canvas(self.root,width= self.map_size[1], height=self.map_size[0])
        self.canvas.pack()

        self.map = tk.PhotoImage(file=self.map_file)
        self.canvas.create_image(0, 0, image=self.map, anchor=tk.NW)

        self.canvas.bind("<Button-1>", self.mouse_callback)

        self.gps = Subscriber(self.fields,self.typ,self.port)
        pt = self.plot_point( 37.429, -122.170, "#ff6400")


        # self.root.after(100, self.update)
        self.root.mainloop()

    def update(self):
        try:
            msg = self.gps.recv()
        except:
            pass
        # self.root.after(100, self.update)



    def mouse_callback(self, event):
        print "clicked at", event.x, event.y

    def gps_to_map(self, gps_pos):
        # y = lat = 0
        # x = lon = 1
        y = self.map_size[0] * (gps_pos[0] - self.top_left[0]) / ( self.bottom_right[0] - self.top_left[0])
        x = self.map_size[1] * (gps_pos[1] - self.top_left[1]) / ( self.bottom_right[1] - self.top_left[1])
        return (y,x)

    def plot_point(self, lat, lon, color):
        r = 10
        y,x = self.gps_to_map( (lat, lon) )
        print x,y
        return self.canvas.create_oval( x + r, y +r , x -r , y-r, fill=color)

    def del_point(self, point):
        self.canvas.delete(point)

if __name__ == "__main__":
    a = GPSPannel()



