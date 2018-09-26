


import Tkinter as tk
from UDPComms import Publisher


class CommandPannel:

    def __init__(self):
        self.root = tk.Tk()

        self.fd=tk.Button(self.root,text='Forwards',command=self.ha)
        self.bk=tk.Button(self.root,text='Back',command=self.ha)
        self.rt=tk.Button(self.root,text='Right',command=self.ha)
        self.lt=tk.Button(self.root,text='Left',command=self.ha)


        self.fd.pack()
        self.bk.pack()
        self.rt.pack()
        self.lt.pack()




        self.root.bind('<Left>', self.leftKey)


        self.root.mainloop()

    @staticmethod
    def ha():
        print "ha"

    @staticmethod
    def leftKey(veent):
        print "leftKey"

        


    def publish(self):
        self.pub.send()
        self.root.after(100, publish)

    # self.root.after(100, publish)


if __name__ == "__main__":
    a = CommandPannel()



