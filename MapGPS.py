

from __future__ import division

import time
import Tkinter as tk
import tkFont
from Tkinter import *
import ttk
from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

from math import sin,cos,pi,sqrt

import csv

### GUI constants
WAYPOINT_POINT_RADIUS =     8
ROVER_POINT_RADIUS =        3

WAYPOINT_DEFAULT_COLOR =    'purple'
WAYPOINT_SELECTED_COLOR =   'cyan'



class Map:
    def __init__(self, file, size, top_left, bottom_right):
        self.file = file
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

class GPSPanel:

    def __init__(self):
        self.root = tk.Tk()

        self.FONT_HEADER = tkFont.Font(family="Helvetica", size=14, weight=tkFont.BOLD)

        ### LOAD MAPS
        self.load_maps()
        self.map = self.maps[self.maps.keys()[0]]
        self.map = self.maps['oval']


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


        # none, waypoint, obstacle, obstacle_radius
        self.mouse_mode = "none"
        self.last_mouse_click = (0,0)
        self.temp_obstace = None



        ### AUTONOMY MODE
        self.auto_mode_dis = tk.StringVar()
        left_row = 0
        tk.Label(self.root, textvariable = self.auto_mode_dis, font=("Courier", 44)).grid(row=left_row, column=0)
        self.auto_mode_dis.set("")

        left_row += 1
        ttk.Separator(self.root, orient=VERTICAL).grid(row=left_row, column=0, sticky='ew')



        ### EXISTING WAYPOINT ACTIONS AND LISTBOX
        # frame for holding all components associated with point library        
        listbox_frame = tk.Frame(self.root)
        left_row += 1
        listbox_frame.grid(row=left_row, column=0)

        self.display_curr_waypoint_frame(listbox_frame)
        left_row += 1
        ttk.Separator(self.root, orient=VERTICAL).grid(row=left_row, column=0, sticky='ew')
        
        # stores tuples of (title, point):
        #   title is the string that's displayed in listbox
        #   point is a point object instance
        self.pointLibrary = []
        # what to call the next added point
        self.pointIncrement = 0



        ### CREATE WAYPOINT ACTIONS
        left_row += 1
        create_frame = tk.Frame(self.root)
        create_frame.grid(row=left_row, column=0)

        self.display_create_waypoint_frame(create_frame)
        self.root.bind("<Escape>",                      lambda: self.change_mouse_mode('none'))
        left_row += 1
        ttk.Separator(self.root, orient=VERTICAL).grid(row=left_row, column=0, sticky='ew')



        ### AUTONOMOUS MODE ACTIONS
        auto_frame = tk.Frame(self.root)
        left_row += 1
        auto_frame.grid(row=left_row, column=0)

        self.display_auto_actions_frame(auto_frame)
        left_row += 1
        ttk.Separator(self.root, orient=VERTICAL).grid(row=left_row, column=0, sticky='ew')



        ### CHANGE MAP ACTIONS
        map_frame = tk.Frame(self.root)
        left_row += 1
        map_frame.grid(row=left_row, column=0)

        self.display_change_map_actions_frame(map_frame)



        top_col = 1
        ttk.Separator(self.root, orient=VERTICAL).grid(row=0, column=top_col, sticky='ns')

        ### MOUSE LOCATION INFO
        mouse_info_frame = tk.Frame(self.root)
        top_col += 1
        mouse_info_frame.grid(row=0, column=top_col)

        self.display_mouse_info_frame(mouse_info_frame)
        top_col += 1
        ttk.Separator(self.root, orient=VERTICAL).grid(row=0, column=top_col, sticky='ns')


        ### ROVER LOCATION INFO
        location_frame = tk.Frame(self.root)
        top_col += 1
        location_frame.grid(row=0, column=top_col)

        self.display_location_info_frame(location_frame)




        ### canvas display
        self.canvas = tk.Canvas(self.root, width= self.map.size[1], height= self.map.size[0])
        self.canvas.grid(row=1, column=1, rowspan=8, columnspan=5)

        self.canvas_img = self.canvas.create_image(0, 0, image=self.map.image, anchor=tk.NW)



        # mouse callbacks
        self.canvas.bind("<Button-1>", self.mouse_click_callback)
        self.canvas.bind("<Motion>", self.mouse_motion_callback)

        self.root.after(50, self.update)
        self.root.mainloop()


    def load_maps(self):
        self.maps = {}

        with open('maps/info.csv') as maps_csv:
            csv_reader = csv.DictReader(maps_csv, delimiter=',')
            for row in csv_reader:
                filename = row['filename']
                name = filename[:filename.find('.')]

                size = (float(row['height']), float(row['width']))
                top_left = (float(row['top_left_lat']), float(row['top_left_lon']))
                bottom_right = (float(row['bottom_right_lat']), float(row['bottom_right_lon']))
                
                self.maps[name] = Map('maps/{}'.format(filename), \
                                      size=size, \
                                      top_left=top_left, \
                                      bottom_right=bottom_right)

    '''
    begin: GUI LAYOUT FUNCTIONS
    '''
    def display_curr_waypoint_frame(self, frame):
        # title
        tk.Label(frame, text='EDIT WAYPOINTS', font=self.FONT_HEADER).grid(row=0, column=0, columnspan=4)

        # actions on listbox of points
        tk.Button(frame, text='Delete',    command=lambda: self.delete_selected_waypoint() ) \
            .grid(row=1, column=0)
        # reorder: move up
        tk.Button(frame, text=u'\u2B06',   command=lambda: self.reorder_selected_waypoint(direction=-1) ) \
            .grid(row=1, column=1)
        # reorder: move down
        tk.Button(frame, text=u'\u2B07',   command=lambda: self.reorder_selected_waypoint(direction=1) ) \
            .grid(row=1, column=2)

        # listbox displaying points
        self.listbox = tk.Listbox(frame)
        self.listbox.grid(row=2, column=0, columnspan=4)
        self.listbox.bind('<FocusOut>',            lambda: self.listbox.selection_clear(0, END))

    def display_create_waypoint_frame(self, frame):
        # title
        tk.Label(frame, text='ADD TO MAP', font=self.FONT_HEADER).grid(row=0, column=0, columnspan=2)
        
        ### click to add waypoint functions
        create_click_frame = tk.Frame(frame)
        create_click_frame.grid(row=4, column=0)

        tk.Label(create_click_frame, text='Click to add:').grid(row=0, column=0, columnspan=2)

        tk.Button(create_click_frame, text='Waypoint', command=lambda: self.change_mouse_mode('waypoint') ).grid(row=1, column=0)
        tk.Button(create_click_frame, text='Obstacle', command=lambda: self.change_mouse_mode('obstacle') ).grid(row=1, column=1)
        tk.Button(create_click_frame, text='None', command=lambda: self.change_mouse_mode('none') ).grid(row=2, column=0, columnspan=2)
        

        ### manual add waypoint functions
        create_manual_frame = tk.Frame(frame)
        create_manual_frame.grid(row=5, column=0)

        tk.Label(create_manual_frame, text='Manual add:').grid(row=0, column=0, columnspan=2)
        
        # text entry labels
        tk.Label(create_manual_frame, text='Lat').grid(row=1, column=0, sticky=E)
        tk.Label(create_manual_frame, text='Lon').grid(row=2, column=0, sticky=E)
        tk.Label(create_manual_frame, text='Name').grid(row=3, column=0, sticky=E)
        
        # text entry boxes
        self.lat_entry = tk.Entry(create_manual_frame)
        self.lon_entry = tk.Entry(create_manual_frame)
        self.name_entry = tk.Entry(create_manual_frame)
        self.lat_entry.grid(row=1 ,column=1)
        self.lon_entry.grid(row=2, column=1)
        self.name_entry.grid(row=3, column=1)
        # button
        tk.Button(create_manual_frame, text='Create Point', command=self.plot_numeric_point).grid(row=4, column=0, columnspan=2)

    def display_auto_actions_frame(self, frame):
        tk.Label(frame, text='AUTONOMOUS ACTIONS', font=self.FONT_HEADER).grid(row=0, column=0, columnspan=2)

        tk.Button(frame, text='Plot Course',command=lambda: self.change_auto_mode('plot')).grid(row=1, column=0)
        tk.Button(frame, text='Auto',       command=lambda: self.change_auto_mode('auto')).grid(row=1, column=1)
        tk.Button(frame, text='STOP',       command=lambda: self.change_auto_mode('off')).grid(row=2, column=0, columnspan=2)

    def display_change_map_actions_frame(self, frame):
        tk.Label(frame, text="CHANGE MAP", font=self.FONT_HEADER).grid(row=0, column=0)
        
        map_choices = self.maps.keys()

        self.map_str_var = tk.StringVar()
        self.map_str_var.set(map_choices[0])
        self.map_str_var.trace('w', self.change_map)

        tk.OptionMenu(frame, self.map_str_var, *map_choices).grid(row=1, column=0)

    def display_location_info_frame(self, frame):
        col = 0

        # Rover location
        tk.Label(frame, text=' ROVER LOCATION ', font=self.FONT_HEADER).grid(row=0, column=col, columnspan=2)

        tk.Label(frame, text='Lat:').grid(row=1, column=col, sticky=E)
        tk.Label(frame, text='Lon:').grid(row=2, column=col, sticky=E)

        self.rover_lat_str_var = tk.StringVar()
        self.rover_lon_str_var = tk.StringVar()
        tk.Label(frame, textvariable=self.rover_lat_str_var).grid(row=1, column=col+1, sticky=W)
        tk.Label(frame, textvariable=self.rover_lon_str_var).grid(row=2, column=col+1, sticky=W)

    def display_mouse_info_frame(self, frame):
        col = 0

        # Mouse location
        tk.Label(frame, text=' MOUSE LOCATION ', font=self.FONT_HEADER).grid(row=0, column=col, columnspan=2)

        tk.Label(frame, text='Lat:').grid(row=1, column=col, sticky=E)
        tk.Label(frame, text='Lon:').grid(row=2, column=col, sticky=E)

        self.mouse_lat_str_var = tk.StringVar()
        self.mouse_lon_str_var = tk.StringVar()
        tk.Label(frame, textvariable=self.mouse_lat_str_var).grid(row=1, column=col+1, sticky=W)
        tk.Label(frame, textvariable=self.mouse_lon_str_var).grid(row=2, column=col+1, sticky=W)

        col += 2
        # Mouse mode
        tk.Label(frame, text=' MOUSE MODE ', font=self.FONT_HEADER).grid(row=0, column=col)
        self.mouse_mode_str = tk.StringVar()
        self.mouse_mode_str.set(self.mouse_mode)
        tk.Label(frame, textvariable=self.mouse_mode_str).grid(row=1, column=col)

        


    '''
    end: GUI LAYOUT FUNCTIONS
    '''



    def change_mouse_mode(self,mode):
        self.mouse_mode = mode

    def change_auto_mode(self,mode):
        assert (mode == "off") or (mode == 'auto') or (mode == 'plot')
        self.auto_control[u'command'] = unicode(mode, "utf-8")

    def change_map(self, *args):
        self.map = self.maps[self.map_str_var.get()]
        self.canvas.config(width=self.map.size[1], height=self.map.size[0])
        self.canvas.itemconfig(self.canvas_img, image=self.map.image)



    def update_rover(self):
        try:
            rover = self.gps.get()
        except timeout:
            pass
            # print("GPS TIMED OUT")
            self.rover_lon_str_var.set("No GPS")
            self.rover_lat_str_var.set("No GPS")
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

            self.rover_lon_str_var.set(rover['lat'])
            self.rover_lat_str_var.set(rover['lon'])

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
            self.mouse_mode_str.set(self.mouse_mode)

            self.update_waypoints()
            self.update_rover()

            self.auto_control_pub.send(self.auto_control)
            # self.obstacles_pub.send(self.obstacles)
        except:
            raise
        finally:
            self.root.after(50, self.update)

    def mouse_motion_callback(self, event):
        x, y = event.x, event.y
        mouse_point = Point.from_map(self.map, x, y)
        self.mouse_lat_str_var.set(round(mouse_point.latitude, 5))
        self.mouse_lon_str_var.set(round(mouse_point.longitude, 5))


    def mouse_click_callback(self, event):
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
    a = GPSPanel()

