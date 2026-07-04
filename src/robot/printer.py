from abc import ABC, abstractmethod
import serial
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
    def move_relative(self, x=None, y=None, z=None, feed_rate=1500):
        pass


class SerialPrinter(Printer):
    def __init__(self, baudrate: int = 250000):
        """
        Initializes the serial printer configuration.
        Default GRBL baudrate is typically 115200.
        """
        self.baudrate = baudrate
        self.connection = None
        self.port = None

    def connect(self):
        """Establishes connection to the GRBL controller and wakes it up."""
        for port in range(10):
            try:
                print(f"Connecting to GRBL on {port}...")
                self.connection = serial.Serial(f"COM{port}", self.baudrate, timeout=0.5)
                
                # GRBL resets on serial connection. Give it a moment to boot up.
                print("Waiting...")
                time.sleep(2)
                
                print("Connected successfully.")
                self.port = port
                break
            except serial.SerialException as e:
                self.connection = None
        
        self.send_command("M502") # Load settings from code (instead of EEPROM) 
        self.home()
        self.send_command("G90") # Absolute coordinates
        # self.send_command("$1=25") # remove power when a motor is idle

    def send_command(self, command: str) -> str:
        """
        Sends a raw G-code string, blocks until GRBL responds with 'ok' or 'error',
        and returns the response.
        """
        if not self.connection or not self.connection.is_open:
            raise ConnectionError("Printer is not connected. Call connect() first.")

        # Clean command and ensure it ends with a newline character
        cmd = command.strip() + "\r\n"
        self.connection.write(cmd.encode('utf-8'))
        
        response_lines = []
        while True:
            line = self.connection.readline().decode('utf-8').strip()
            if line:
                response_lines.append(line)
                # GRBL acknowledges completion/receipt with 'ok' or an 'error'
                if line.lower() == 'ok' or line.lower().startswith('error'):
                    break
        
        return "\n".join(response_lines)

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

    def move_relative(self, x: float = None, y: float = None, z: float = None, feed_rate: float = 1500):
        """
        Moves relative to the current position by the specified offsets.
        Toggles G91 for the move, then reverts to G90 for state safety.
        """
        if x is None and y is None and z is None:
            print("No offsets provided for relative movement.")
            return

        # 1. Switch to Relative mode (G91) and perform linear move (G1)
        self.send_command("G91")
        gcode = "G1"
        
        if x is not None:
            gcode += f" X{x:.3f}"
        if y is not None:
            gcode += f" Y{y:.3f}"
        if z is not None:
            gcode += f" Z{z:.3f}"
            
        gcode += f" F{feed_rate}"
        
        response = self.send_command(gcode)
        
        # 2. Immediately restore state to Absolute mode (G90) so we don't break other routines
        self.send_command("G90")
        
        return response

    def disconnect(self):
        """Closes the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Disconnected from printer.")