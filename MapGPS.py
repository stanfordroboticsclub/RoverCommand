

from __future__ import division

import time
import Tkinter as tk
from Tkinter import *
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

from math import sin,cos,pi,sqrt

### GUI constants
WAYPOINT_POINT_RADIUS =     8
ROVER_POINT_RADIUS =        3

WAYPOINT_DEFAULT_COLOR =    'purple'
WAYPOINT_SELECTED_COLOR =   'cyan'



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


        self.map = EQuad


        ## UDPComms
        self.gps  = Subscriber(8280, timeout=2)
        self.rover_pt = None

        self.gyro = Subscriber(8220, timeout=1)
        self.arrow = None

        self.gps_base = Subscriber(8290, timeout=2)
        self.base_pt = None

        # publishes the point the robot should be driving to
        self.auto_control  = {u"waypoints": [], u"command":u"off"}
        self.auto_control_pub = Publisher(8310)
        self.pub_pt = None

        # obstacles from the interface, displayed pink trasparent
        self.obstacles = []
        self.obstacles_pub = Publisher(9999)

        # obstacles from the robots sensors, displayed red tranparent.
        self.auto_obstacle_sub = Publisher(9999)

        # the path the autonomous module has chosen, drawn as blue lines
        self.path_sub = Subscriber(9999)


        ### label display
        self.gps_data = tk.StringVar()
        tk.Label(self.root, textvariable = self.gps_data).grid(row=8, column=0)#, columnspan =6)
        self.gps_data.set("")

        self.auto_mode_dis = tk.StringVar()
        tk.Label(self.root, textvariable = self.auto_mode_dis, font=("Courier", 44)).grid(row=0, column=0)
        self.auto_mode_dis.set("")


        ### numeric input display
        self.root.bind("<Escape>",                      lambda: self.change_mouse_mode('none'))

        tk.Button(self.root, text='Plot Course',command=lambda: self.change_auto_mode('plot')).grid(row=5, column=0)
        tk.Button(self.root, text='Auto',       command=lambda: self.change_auto_mode('auto')).grid(row=6, column=0)
        tk.Button(self.root, text='STOP',       command=lambda: self.change_auto_mode('off')).grid(row=7, column=0)


        '''
        begin: EXISTING WAYPOINT ACTIONS AND LISTBOX
        '''

        # frame for holding all components associated with point library        
        self.listbox_frame = tk.Frame(self.root)
        self.listbox_frame.grid(row=1, column=0)

        # title
        tk.Label(self.listbox_frame, text='CURRENT WAYPOINTS').grid(row=0, column=0, columnspan=4)

        # actions on listbox of points
        tk.Button(self.listbox_frame, text='Delete',    command=lambda: self.delete_selected_waypoint() ) \
            .grid(row=1, column=0)
        # reorder: move up
        tk.Button(self.listbox_frame, text=u'\u2B06',   command=lambda: self.reorder_selected_waypoint(direction=-1) ) \
            .grid(row=1, column=1)
        # reorder: move down
        tk.Button(self.listbox_frame, text=u'\u2B07',   command=lambda: self.reorder_selected_waypoint(direction=1) ) \
            .grid(row=1, column=2)
        # tk.Button(self.listbox_frame, text='Deselect',  command=lambda: self.listbox.selection_clear(0, END) ) \
        #     .grid(row=1, column=3)

        # listbox displaying points
        self.listbox = tk.Listbox(self.listbox_frame)
        self.listbox.grid(row=2, column=0, columnspan=4)
        self.listbox.bind('<FocusOut>',                         lambda: self.listbox.selection_clear(0, END))
        
        # stores tuples of (title, point), 
        #   title is the string that's displayed in listbox
        #   point is a point object instance
        self.pointLibrary = []
        # what to call the next added point
        self.pointIncrement = 0
        
        '''
        end: EXISTING WAYPOINT ACTIONS AND LISTBOX
        '''


        '''
        begin: CREATE WAYPOINT ACTIONS
        '''

        # "add to map" frame
        self.create_frame = tk.Frame(self.root)
        self.create_frame.grid(row=3, column=0)

        # title
        tk.Label(self.create_frame, text='ADD TO MAP').grid(row=0, column=0, columnspan=2)
        
        # click to add waypoint functions
        self.create_click_frame = tk.Frame(self.create_frame)
        self.create_click_frame.grid(row=4, column=0)
        tk.Label(self.create_click_frame, text='Click to add:').grid(row=0, column=0, columnspan=2)
        tk.Button(self.create_click_frame, text='Waypoint', command=lambda: self.change_mouse_mode('waypoint') ).grid(row=1, column=0)
        tk.Button(self.create_click_frame, text='Obstacle', command=lambda: self.change_mouse_mode('obstacle') ).grid(row=1, column=1)
        tk.Button(self.create_click_frame, text='None', command=lambda: self.change_mouse_mode('none') ).grid(row=2, column=0, columnspan=2)
        
        # manual add waypoint functions
        self.create_manual_frame = tk.Frame(self.create_frame)
        self.create_manual_frame.grid(row=5, column=0)

        tk.Label(self.create_manual_frame, text='Manual add:').grid(row=0, column=0, columnspan=2)
        # text entry labels
        tk.Label(self.create_manual_frame, text='Lat').grid(row=1, column=0, sticky=E)
        tk.Label(self.create_manual_frame, text='Lon').grid(row=2, column=0, sticky=E)
        tk.Label(self.create_manual_frame, text='Name').grid(row=3, column=0, sticky=E)
        # text entry boxes
        self.lat_entry = tk.Entry(self.create_manual_frame)
        self.lon_entry = tk.Entry(self.create_manual_frame)
        self.name_entry = tk.Entry(self.create_manual_frame)
        self.lat_entry.grid(row=1 ,column=1)
        self.lon_entry.grid(row=2, column=1)
        self.name_entry.grid(row=3, column=1)
        # button
        tk.Button(self.create_manual_frame, text='Create Point', command=self.plot_numeric_point).grid(row=4, column=0, columnspan=2)

        '''
        end: CREATE WAYPOINT ACTIONS
        '''


        ### canvas display
        self.canvas=tk.Canvas(self.root, width= self.map.size[1] - 180, height= self.map.size[0] - 180)
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
        self.auto_control[u'command'] = unicode(mode, "utf-8")


    def update_rover(self):
        try:
            rover = self.gps.get()
        except timeout:
            pass
            # print("GPS TIMED OUT")
            self.gps_data.set("MODE: "+self.mouse_mode+", no gps data recived")
        else:
            # TODO: uggly
            tmp = None
            if self.rover_pt != None:
                tmp = self.rover_pt.plot
            self.rover_pt = Point.from_gps(self.map, rover['lat'], rover['lon'])
            if tmp is not None:
                self.rover_pt.plot = tmp
            self.plot_point(self.rover_pt, ROVER_POINT_RADIUS, '#ff6400')

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
            self.plot_point(self.base_pt, ROVER_POINT_RADIUS, '#ff0000')

            
        if self.arrow is not None:
            self.canvas.delete(self.arrow)
        try:
            angle = self.gyro.get()['angle'][0]
            print(angle)
        except:
            pass
        else:
            y,x = self.rover_pt.map()
            r = 20
            self.arrow = self.canvas.create_line(x, y, x + r*sin(angle * pi/180),
                                                       y - r*cos(angle * pi/180),
                                                          arrow=tk.LAST)

    def update_waypoints(self):
        for i, p in enumerate(self.pointLibrary):
            _, point = p
            if i in self.listbox.curselection():
                self.plot_selected_point(point)
            else:
                self.plot_normal_point(point)

        # populate UDPComms message with current ordered list of waypoints
        msg = [ {u'lat': point.gps()[0], u'lon': point.gps()[1]} for _, point in self.pointLibrary ]
        self.auto_control[u'waypoints'] = msg

    def update(self):
        try:
            self.auto_mode_dis.set(self.auto_control[u'command'].upper())
            self.gps_data.set(self.mouse_mode)

            self.update_waypoints()
            self.update_rover()

            self.auto_control_pub.send(self.auto_control)
            # self.obstacles_pub.send(self.obstacles)
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
            did_click_waypoint = False

            ### check if we clicked on a waypoint; if so, select it
            for i, p in enumerate(self.pointLibrary):
                title, point = p
                y, x = point.map()
                if abs(event.x - x) < WAYPOINT_POINT_RADIUS and abs(event.y - y) < WAYPOINT_POINT_RADIUS:
                    print 'you clicked on', title
                    self.listbox.selection_clear(0, END)
                    self.listbox.selection_set(i)
                    did_click_waypoint = True
                    break

            ### if clicked on the map but outside of waypoints, clear current selection
            if not did_click_waypoint:
                self.listbox.selection_clear(0, END)

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
        new_numeric = Point.from_gps(self.map, float(self.lat_entry.get()), float(self.lon_entry.get()))
        self.new_waypoint(new_numeric, self.name_entry.get())
        self.name_entry.delete(0, END)

    def new_waypoint(self, point, name=""):
        self.plot_normal_point(point)

        # optional name for the point
        if name == "":
            title = "Point " + str(self.pointIncrement)
        else:
            title = name

        self.listbox.insert("end", title)
        self.pointLibrary.append((title, point))
        self.pointIncrement += 1

    def delete_selected_waypoint(self):
        if len(self.listbox.curselection()) == 0:
            print "No waypoint to delete"
            return

        index = self.listbox.curselection()[0]
        
        _, point = self.pointLibrary[index]
        self.del_point(point)               # delete from map GUI
        del self.pointLibrary[index]        # delete from dict
        self.listbox.delete(index)          # delete from listbox GUI

    def reorder_selected_waypoint(self, direction):
        if len(self.listbox.curselection()) == 0:
            print "No waypoint to reorder"
            return
        assert direction == -1 or direction == 1

        index = self.listbox.curselection()[0]

        # if can't move up or down anymore, don't do anything
        if (index == 0 and direction == -1) or (index == len(self.pointLibrary) - 1 and direction == 1):
            return

        # reorder in pointLibrary
        title, _ = self.pointLibrary[index]
        self.pointLibrary.insert(index + direction, self.pointLibrary.pop(index))

        # reorder in listbox
        self.listbox.delete(index)
        self.listbox.insert(index + direction, title)


    def plot_selected_point(self, point):
        self.plot_point(point, WAYPOINT_POINT_RADIUS, WAYPOINT_SELECTED_COLOR)

    def plot_normal_point(self, point):
        self.plot_point(point, WAYPOINT_POINT_RADIUS, WAYPOINT_DEFAULT_COLOR)



if __name__ == "__main__":
    a = GPSPannel()

