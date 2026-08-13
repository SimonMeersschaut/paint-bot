from robot import SerialPrinter
# from robot import Camera
from webserver import WebApp


printer = SerialPrinter()
WebApp.init(printer=printer, on_fan_change=printer.set_fan)
WebApp.start_server() # handles the ExecutionDaemon