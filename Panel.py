


import Tkinter as tk
from UDPComms import Publisher


class CommandPannel:

    def __init__(self):
        self.root = tk.Tk()

        self.fd=Tk.Button(root,text='Forwards',command=d1_Euler_wrapper)
        self.bk=Tk.Button(root,text='Back',command=d1_Euler_wrapper)
        self.rt=Tk.Button(root,text='Right',command=d1_Euler_wrapper)
        self.lt=Tk.Button(root,text='Left',command=d1_Euler_wrapper)




def publish():
    pub.send()
    root.after(100, publish)

root.after(100, publish)



root.mainloop()
