from threading import Thread, Event

import time
import smbus
from flask.ext.socketio import SocketIO, emit, disconnect

##
##
## Methods required for the i2c communication
##
##

class i2cCommunication():
    def __init__(self, bus):
        self.bus = bus
        self.cmd = 0
        self.READ = 0
        self.WRITE = 1
        self.ANALOG = 0
        self.DIGITAL = 1
        self.timeSleep = 0.2
    
    def digitalWrite(self, pin, address, val):
        (self.bus).write_i2c_block_data(address, self.cmd, [pin, self.WRITE, self.DIGITAL, val])
    
    def digitalRead(self, pin, address):
        (self.bus).write_i2c_block_data(address, self.cmd, [pin, self.READ, self.DIGITAL, 0])
        time.sleep(self.timeSleep)
        return (self.bus).read_byte(address)
        
    def analogWrite(self, pin, address, val):
        (self.bus).write_i2c_block_data(address, self.cmd, [pin, self.WRITE, self.ANALOG, val])
    
    def analogRead(self, pin, address):
        (self.bus).write_i2c_block_data(address, self.cmd, [pin, self.READ, self.ANALOG, 0])
        time.sleep(self.timeSleep)
        return (self.bus).read_byte(address)
    
    def setCmd(self, val):
        self.cmd = val
    
    def getCmd(self):
        return self.cmd

##
##
## Threading for sending and receiving data
##
##

class CommunicationThread(Thread, i2cCommunication):
    def __init__(self, name, address, pin, A_D, R_W, val, bus, sleep, socketio):
        Thread.__init__(self)
        self.name = name
        self.address = address
        self.pin = pin
        self.A_D = A_D
        self.R_W = R_W
        self.value = val
        self.bus = bus
        self.sleep = sleep
        self.exitFlag = Event()
        self.socketio = socketio
        
        self.cmd = 0
        self.READ = 0
        self.WRITE = 1
        self.ANALOG = 0
        self.DIGITAL = 1
        self.timeSleep = 0.2
    
    def setExitFlag(self):
        print 'flag set'
        self.exitFlag.set()

    def clearExitFlag(self):
        self.exitFlag.clear()
        
    def getExitFlag(self):
        return self.exitFlag
    
        
    def sendSocketMessage(self, data):
        (self.socketio).emit('message',
                  {'data': data}, namespace='/test')
    
    def run(self):
        while not (self.exitFlag).is_set():
            try:
                if self.R_W == 0:   #Read
                    if self.A_D == 0: #Analog Read
                        data = i2cCommunication.analogRead(self, self.pin, self.address)
                    elif self.A_D == 1: #Digital Read
                        data = i2cCommunication.digitalRead(self, self.pin, self.address)
                    
                    self.sendSocketMessage(data)
                    time.sleep(self.sleep)
                    
                elif self.R_W == 1: #Write
                    if self.A_D == 0:   #Analog Write
                        i2cCommunication.analogWrite(self, self.pin, self.address, self.value)
                        self.setExitFlag()
                        break
                    elif self.A_D == 1: #Digital Write
                        i2cCommunication.digitalWrite(self, self.pin, self.address, self.value)
                        self.setExitFlag()
                        break
                    
                else:
                    data = 'Command not recognised'
                    self.sendSocketMessage(data)
                    self.setExitFlag()
                    break
                        
            except Exception, e:
                data = str(e)
                self.sendSocketMessage(data)
                self.setExitFlag()
                break
        
        print 'exited'


def create_CommunicationThread(name, address, pin, A_D, R_W, val, bus, sleep, socketio):
    return CommunicationThread(name, address, pin, A_D, R_W, val, bus, sleep, socketio)

