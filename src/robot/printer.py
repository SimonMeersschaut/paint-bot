from abc import ABC, abstractmethod
import re
import serial
import serial.tools.list_ports
import time

# Defining the abstract base class based on your snippet
class Printer(ABC):
    @abstractmethod
    def __init__(self):
        pass
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def home(self):
        pass
    
    @abstractmethod
    def move_to(self, x=None, y=None, z=None, feed_rate=1500):
        pass

    @abstractmethod
    def get_position(self):
        pass


class SerialPrinter(Printer):
    def __init__(self, baudrate: int = 250000):
        """
        Initializes the serial printer configuration.
        Default baudrate is typically 115200.
        The printer is configured with Marlin Software.
        """
        self.baudrate = baudrate
        self.connection = None
        self.port = None

    def connect(self):
        """Establishes connection to the GRBL controller and wakes it up."""
        for port in serial.tools.list_ports.comports():
            if port.manufacturer == "Arduino (www.arduino.cc)": # make sure we are opening the correct port
                try:
                    print(f"Connecting to GRBL on {port.device}...")
                    self.connection = serial.Serial(port.device, self.baudrate, timeout=1.0) # Increased timeout slightly for initial shake
                    
                    time.sleep(2)
                    self.connection.reset_input_buffer()

                    print("Connected successfully.")
                    self.port = port
                    
                    if self.connection and self.connection.is_open:
                        self.send_command("M502") 
                        self.home()
                        self.send_command("G90")
                        return
                except serial.SerialException as e:
                    self.connection = None
                    print("Not connected!")
                    print(e)
                    exit()
        print("No connection found!")
        exit()

    def send_command(self, command: str) -> str:
        """
        Sends a raw G-code string, blocks until GRBL responds with 'ok' or 'error',
        and returns the response.
        """
        if not self.connection or not self.connection.is_open:
            raise ConnectionError("Printer is not connected. Call connect() first.")

        # Clean command and ensure it ends with a newline character
        cmd = command.strip() + "\r\n"
        self.connection.reset_input_buffer()
        self.connection.write(cmd.encode('utf-8'))
        
        response_lines = []
        while True:
            line = self.connection.readline().decode('utf-8').strip()
            if line:
                # Marlin acknowledges completion/receipt with 'ok' or an 'error'
                if line.lower().startswith("ok") or line.lower().startswith('error'):
                    break
                else:
                    response_lines.append(line)
        
        return "\n".join(response_lines)

    def move_and_wait(self, x, y, z):
        target_x, target_y, target_z = x, y, z
        timeout_seconds = 60.0
        poll_interval_seconds = 0.2
        tolerance = 0.05

        deadline = time.monotonic() + timeout_seconds
        self.move_to(x, y, z)
        while True:
            current_x, current_y, current_z = self.get_position()
            print(current_x, current_y, current_z)

            arrived = True
            if target_x is not None and abs(current_x - target_x) > tolerance:
                arrived = False
            if target_y is not None and abs(current_y - target_y) > tolerance:
                arrived = False
            if target_z is not None and abs(current_z - target_z) > tolerance:
                arrived = False

            if arrived:
                return current_x, current_y, current_z

            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Printer did not reach target position ({target_x}, {target_y}, {target_z})"
                )

            time.sleep(poll_interval_seconds)

    def get_position(self):
        """Query the current printer position using a M114."""
        
        response = self.send_command("M114")

        match = re.search(
            r"X:([+-]?\d+(?:\.\d+)?)\s+Y:([+-]?\d+(?:\.\d+)?)\s+Z:([+-]?\d+(?:\.\d+)?)",
            response,
        )
        if not match:
            raise ValueError(f"Could not parse position from printer response: {response}")

        return tuple(float(value) for value in match.groups())

    def home(self):
        """Executes the GRBL homing cycle ($H)."""
        self.send_command("G28")

    def move_to(self, x: float = None, y: float = None, z: float = None, feed_rate: float = 1500):
        """
        Moves to an absolute position using G1.
        Explicitly sets G90 for absolute positioning.
        """
        if x is None and y is None and z is None:
            print("No coordinates provided for movement.")
            return

        gcode = "G1"
        
        if x is not None:
            gcode += f" X{x:.3f}"
        if y is not None:
            gcode += f" Y{y:.3f}"
        if z is not None:
            gcode += f" Z{z:.3f}"
            
        gcode += f" F{feed_rate}"
        
        response = self.send_command(gcode)
        return response

    def disconnect(self):
        """Closes the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Disconnected from printer.")