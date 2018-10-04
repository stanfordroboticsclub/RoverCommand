# RoverCommand


Panel
----
- Can be used anywhere (tested on mac). Drive with arrow keys
- Launched using `python Panel.py`


Joystick
----
- Can only be used on Rpi becasue PS4 controller doesn't work on mac
- Make sure ds4drv is installed 
- Put contoller into pairing mode (hold share and PS button)
- Lanuch ds4drv using `sudo ds4drv &` (TODO: move to systemd services)
- Lanch script using `sudo python3 joystick.py`