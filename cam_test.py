import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import time
import requests


class App:
    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.title(window_title)
        self.video_source = video_source

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)


        self.window.bind("<space>", lambda e:self.send_command(0) )
        self.window.bind("w", lambda e:self.send_command(2) )
        self.window.bind("s", lambda e:self.send_command(1) )
        self.window.bind("a", lambda e:self.send_command(3) )
        self.window.bind("d", lambda e:self.send_command(4) )

        # self.window.bind("<KeyRelease-w>", lambda e:self.send_command(0) )
        # self.window.bind("<space>", lambda e:self.send_command(0) )
        # self.window.bind("<space>", lambda e:self.send_command(0) )
        # self.window.bind("<space>", lambda e:self.send_command(0) )

        self.canvas.pack()


        # Button that lets the user take a snapshot
        # self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=50, command=self.snapshot)
        # self.btn_snapshot.pack(anchor=tkinter.CENTER, expand=True)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update()

        self.window.mainloop()

    def test(self):
        print("hello")

    def send_command(self, number):
        print("sending", number)
        url ='http://10.0.0.41/form/setPTZCfg?_=1550025976653'
        data = {"command":number, "ZFSpeed":0, "PTSpeed":0, "panSpeed":8, "tiltSpeed":8, "focusSpeed":2, "zoomSpeed":2}
        requests.post(url, data, auth=('admin','admin'))



    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def update(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)

        self.window.after(self.delay, self.update)


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

# Create a window and pass it to the Application object
# App(tkinter.Tk(), "Tkinter and OpenCV", "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov")

# App(tkinter.Tk(), "Tkinter and OpenCV", "rtsp://10.0.0.41:8554/1/h264major")
App(tkinter.Tk(), "Tkinter and OpenCV", "rtsp://10.0.0.41:8554/1/h264minor")

