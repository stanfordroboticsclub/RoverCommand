


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
        self.root = tk.Tk()


        self.lat_var = tk.StringVar()
        self.lon_var = tk.StringVar()

        self.lat = tk.Label(self.root, textvariable = self.lat_var)
        self.lon = tk.Label(self.root, textvariable = self.lon_var)

        self.lat_var.set("Lat: ")
        self.lon_var.set("Lon: ")

        self.lat.pack()
        self.lon.pack()

        self.canvas=tk.Canvas(self.root,width=1440, height=949)
        self.canvas.pack()


        self.map = tk.PhotoImage(file='maps/zoomed_small.gif')

        self.canvas.create_image(0, 0, image=self.map, anchor=tk.NW)


        # self.gps = Subscriber(self.fields,self.typ,self.port)

        # self.root.after(100, self.update)
        self.root.mainloop()


    def update(self):
        try:
            msg = self.gps.recv()
        except:
            pass

        self.root.after(100, self.update)


if __name__ == "__main__":
    a = GPSPannel()



