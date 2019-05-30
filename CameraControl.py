


import time
import Tkinter as tk
from UDPComms import Publisher
import os


class PTZPannel:
    def __init__(self):
        self.pub = Publisher(8120)
        self.root = tk.Tk()

        self.fd=tk.Button(self.root,text='Up',command=lambda : self.upKey(None))
        self.bk=tk.Button(self.root,text='Down',command=lambda : self.downKey(None))
        self.rt=tk.Button(self.root,text='Right',command=lambda : self.rightKey(None))
        self.lt=tk.Button(self.root,text='Left',command=lambda : self.leftKey(None))
        self.cam2=tk.Button(self.root,text='POV',command=lambda : self.launchCam('camera2'))
        self.cam3=tk.Button(self.root,text='Side',command=lambda : self.launchCam('camera3'))
        self.ptz=tk.Button(self.root,text='PTZ',command=lambda : self.launchCam('ptz'))
        self.drive=tk.Button(self.root,text='drive',command=lambda : self.launchCam('drive'))

        self.fd.pack()
        self.bk.pack()
        self.rt.pack()
        self.lt.pack()
        self.cam2.pack()
        self.cam3.pack()
        self.ptz.pack()
        self.drive.pack()

        self.root.bind('<Left>',  lambda x: self.leftKey(x))
        self.root.bind('<Right>', lambda x: self.rightKey(x))
        self.root.bind('<Up>',    lambda x: self.upKey(x))
        self.root.bind('<Down>',  lambda x: self.downKey(x))
        self.root.bind('<space>',  lambda x: self.spaceKey(x))

        self.pan = 0
        self.tilt = 0

        self.speed = 2
        self.time = time.time()

        self.root.after(100, self.update)
        self.root.mainloop()


    def launchCam(self, cam):
        os.system("bash launch_camera.sh "+cam+".local")

    def spaceKey(self, event):
        print "space"
        self.pan = 0
        self.tilt = 0
        self.time = time.time()

    def leftKey(self, event):
        print "left"
        self.pan = -self.speed
        self.tilt = 0
        self.time = time.time()
        
    def rightKey(self, event):
        print "right"
        self.pan = self.speed
        self.tilt = 0
        self.time = time.time()

    def upKey(self, event):
        print "up"
        self.pan = 0
        self.tilt = -self.speed
        self.time = time.time()

    def downKey(self, event):
        print "down"
        self.pan = 0
        self.tilt = self.speed
        self.time = time.time()

    def update(self):
        print('update')
        try:
            if (time.time() - self.time) > 0.3:
                self.pan = 0
                self.tilt = 0
            print('sending')
            self.pub.send({'pan': self.pan,'tilt':self.tilt})
        except:
            raise
        finally:
            self.root.after(100, self.update)


if __name__ == "__main__":
    a = PTZPannel()


