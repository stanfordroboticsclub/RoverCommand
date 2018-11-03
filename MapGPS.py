

from __future__ import division

import time
import Tkinter as tk
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout



# zoomed out
# top left: 37.432565, -122.180000
# bottom right: 37.421642, -122.158724

# zoomed in:
# top left:37.430638, -122.176173
# bottom right:  37.426803, -122.168855


class GPSPannel:

    fields = "time sats lat lon alt error_lat error_lon error_alt"
    fields_out = "lat lon"
    typ = "ii3f3f"
    typ_out = "2f"
    port = 8860
    port_out = 8890
    pub = Publisher(fields_out, typ_out, port_out)


    def __init__(self):

        #### config
        self.top_left =     (37.430638, -122.176173)
        self.bottom_right = (37.426803, -122.168855)
        self.pt = None
        self.pt_new = None

        self.map_size = (949, 1440) ## (height, width)
        ### self.smaller_map = self.map.zoom(2, 2).subsample(3, 3)
        ### self.smaller_map = self.map.subsample(2, 2)
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

        ## self.lat.grid()
        ## self.lon.grid()

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

        self.gps = Subscriber(self.fields,self.typ,self.port, 2)



        self.root.after(100, self.update)
        self.root.mainloop()


    def update(self):
        try:
           msg = self.gps.recv()
        except timeout:
            self.root.after(100, self.update)
            return

        if self.pt is not None:
            self.del_point(self.pt)

        self.pt = self.plot_point(msg.lat, msg.lon, '#ff6400')

        if self.pt_new is not None:
            self.pub.send(self.lat_new, self.lon_new)


        self.root.after(100, self.update)



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
        r = 10
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
        self.lat_input = float(self.e1.get())
        self.lon_input = float(self.e2.get())

        self.new_point(self.lat_input, self.lon_input)

    def new_point(self, lat, lon):

        self.lat_new, self.lon_new = lat, lon
        if self.pt_new is not None:
            self.del_point(self.pt_new)

        self.pt_new = self.plot_point(lat, lon, 'cyan')










if __name__ == "__main__":
    a = GPSPannel()

