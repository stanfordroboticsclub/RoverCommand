import sys
import time
from collections import namedtuple

import Tkinter as tk
import tkFont
from Tkinter import *
import ttk

from UDPComms import Subscriber
from UDPComms import Publisher
from UDPComms import timeout

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation

import threading

# UDP ports
DRIVE_TELEMETRY_PORT = 		8810
ARM_TELEMETRY_PORT = 		0 # TODO
SCIENCE_TELEMETRY_PORT = 	0 # TODO

ODRIVES = 					['front', 'middle', 'back']
NUM_AXES = 					2

MAX_QUEUE_SIZE = 			50
GRAPH_UPDATE_INTERVAL = 	50	# milliseconds

# Ploting min + max bounds and reference line
VBUS_VOLTAGE_MIN = 			30
VBUS_VOLTAGE_MAX = 			40
VBUS_VOLTAGE_THRESH = 		36
VBUS_VOLTAGE_BOUNDS =		(VBUS_VOLTAGE_MIN, VBUS_VOLTAGE_MAX, VBUS_VOLTAGE_THRESH)

CURRENT_MIN =				0
CURRENT_MAX =				5
CURRENT_THRESH =			3
CURRENT_BOUNDS =			(CURRENT_MIN, CURRENT_MAX, CURRENT_THRESH)


class TelemetryPanel:
	def __init__(self):
		self.root = tk.Tk()
		self.FONT_HEADER = tkFont.Font(family="Helvetica", size=14, weight=tkFont.BOLD)

		# Plotting data
		self.drive_status = False
		self.drive_currents = { odrive: [[] for i in range(NUM_AXES)] for odrive in ODRIVES }
		self.drive_voltages = []

		## UDPComms
		self.drive_telemetry = Subscriber(DRIVE_TELEMETRY_PORT, timeout=2)
		self.arm_telemetry = Subscriber(ARM_TELEMETRY_PORT, timeout=2)
		self.science_telemetry = Subscriber(SCIENCE_TELEMETRY_PORT, timeout=2)

		self.init_ui()

		self.root.after(50, self.update)
		self.root.mainloop()



	def init_ui(self):
		drive_frame = tk.Frame(self.root)
		drive_frame.grid(row=0, column=0)
		self.init_drive_ui(drive_frame)

		arm_frame = tk.Frame(self.root)
		arm_frame.grid(row=0, column=1)
		self.init_arm_ui(arm_frame)

		science_frame = tk.Frame(self.root)
		science_frame.grid(row=0, column=2)
		self.init_science_ui(science_frame)

	def init_drive_ui(self, frame):
		tk.Label(frame, text='DRIVE ', font=self.FONT_HEADER).grid(row=0, column=0, sticky='e')
		self.drive_status_up = tk.Label(frame, text=' Operational', fg="darkgreen")
		self.drive_status_down = tk.Label(frame, text=' Down', fg="red")
		self.drive_status_up.grid(row=0, column=1, sticky='w')
		self.drive_status_down.grid(row=0, column=1, sticky='w')
		self.drive_status_up.grid_remove()
		
		figure = Figure(figsize=(5,8), dpi=100)
		plot_canvas = FigureCanvasTkAgg(figure, frame)
		plot_canvas.get_tk_widget().grid(row=1, column=0, columnspan=2)

		# Create a new live-updating subplot of `figure`
		def subplot(subplot, lists, bounds, labels=None, title=None):
			bounds_min, bounds_max, bounds_thresh = bounds
			animated_plot = figure.add_subplot(subplot)

			# Animation (replotting) function to live update graph
			def animate(i):
				animated_plot.clear()
				
				for l in lists:
					animated_plot.plot(l)
				
				if labels is not None: animated_plot.legend(labels)
				if title is not None:  animated_plot.set_title(title)
				animated_plot.xaxis.set_visible(False)
				animated_plot.set_ylim(bounds_min, bounds_max)
				animated_plot.axhline(bounds_thresh, linewidth=2, color="gray", alpha=.7)

				plot_canvas.draw()

			ani = animation.FuncAnimation(figure, animate, interval=GRAPH_UPDATE_INTERVAL)
			plot_canvas.show()

		subplot(411, lists=[self.drive_voltages], 			bounds=VBUS_VOLTAGE_BOUNDS,	title="Voltage")
		subplot(412, lists=self.drive_currents['front'], 	bounds=CURRENT_BOUNDS,		title="Front Current",	labels=['axis0', 'axis1'])
		subplot(413, lists=self.drive_currents['middle'],	bounds=CURRENT_BOUNDS,		title="Middle Current", labels=['axis0', 'axis1'])
		subplot(414, lists=self.drive_currents['back'],		bounds=CURRENT_BOUNDS,		title="Back Current", 	labels=['axis0', 'axis1'])

	def init_arm_ui(self, frame):
		tk.Label(frame, text=' ARM', font=self.FONT_HEADER).grid(row=0, column=0, sticky='n')

	def init_science_ui(self, frame):
		tk.Label(frame, text=' SCIENCE', font=self.FONT_HEADER).grid(row=0, column=0, sticky='n')



	def update_drive_telemetry(self):
		try:
			drive = self.drive_telemetry.get()
		except timeout:
			# If this is our first dropped drive telemetry packet after being up, update status
			if self.drive_status == True:
				self.drive_status_up.grid_remove()
				self.drive_status_down.grid()
				self.drive_status = False

			sys.stdout.write('.')
			sys.stdout.flush()
		else:
			# If this is our first drive telemetry packet after being down, update status
			if self.drive_status == False:
				self.drive_status_down.grid_remove()
				self.drive_status_up.grid()
				self.drive_status = True

			for odrive in drive:
				vals = drive[odrive]
				voltage, current_axis0, current_axis1 = vals

				if odrive == 'front':
					self.drive_voltages.append(voltage)
					if len(self.drive_voltages) > MAX_QUEUE_SIZE: 
						self.drive_voltages.pop(0)

				self.drive_currents[odrive][0].append(current_axis0)
				if len(self.drive_currents[odrive][0]) > MAX_QUEUE_SIZE: 
					self.drive_currents[odrive][0].pop(0)
				self.drive_currents[odrive][1].append(current_axis1)
				if len(self.drive_currents[odrive][1]) > MAX_QUEUE_SIZE: 
					self.drive_currents[odrive][1].pop(0)


	def update(self):
		self.update_drive_telemetry()
		self.root.after(50, self.update)


if __name__ == "__main__":
	a = TelemetryPanel()