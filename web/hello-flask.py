from flask import Flask, render_template, request
import datetime

import smbus
import time

app = Flask(__name__)

#data to send to the html
templateData = {
		'title': 'HELLO!',
		'time': '',
                'chat': []
	}

#i2c bus init
numberBus = 1
bus = smbus.SMBus(numberBus)

#i2c and gpio address. This is the address we setup in the arduino program
address = 0x04
cmd = 0x00



#method for writing to the i2c bus
def writeByte(value):
        bus.write_byte(address, 13)
        bus.write_byte(address, value)
        return -1

#method for reading to the i2c bus
def readByte():
        number = bus.read_byte(address)
        return number

def writeI2c(value, pin):
        bus.write_i2c_block_data(address, cmd, [pin, 1, value])

#method for writing the message to send to the Arduino
'''def writeMessage(inputOutput, digitalAnalog, targetPin):
        byteMessage = 0x00
        if inputOutput:
                byteMessage |= 0x80
        if digitalAnalog:
                byteMessage |= 0x40
        targetPin = targetPin << 1
        byteMessage |= targetPin
        templateData['chat'].append("enviado-> " + str(byteMessage))
        writeByte(1)'''

        
#code to execute when entered '/'
@app.route("/")
def hello():
	now = datetime.datetime.now()
	timeString = now.strftime("%Y-%m-%d %H:%M")
	templateData['time'] = timeString
	templateData['chat'] = []

	'''render the template'''
	return render_template('main.html', **templateData)


#code to execute when POST a form
@app.route('/', methods=['POST'])
def my_form_post():
        '''access the form elements in the dictionary request.form'''
        #txtText = request.form['txtText']
        numberBus = request.form['txtText']
        rdbI2c = True if request.form['rdbI2c']=='yes' else False
        #rdbIO = True if request.form['rdbIO']=='Input' else False
        #rdbDA = True if request.form['rdbDA']=='Digital' else False
        txtPin = int(request.form['txtPin'])

        '''if the chkI2c is checked, then send the data through the bus'''
        if rdbI2c:
                rdbOnOff = True if request.form['rdbOnOff']=='on' else False
                try:
                        if rdbOnOff:
                                writeByte(1)
                                templateData['chat'].append("enviado-> "+str(txtPin) + ": "+ "on")
                        else:
                                writeByte(0)
                                templateData['chat'].append("enviado-> "+str(txtPin) + ": "+ "Off")
                except Exception, e:
                        return str(e)
                        '''templateData['chat'].append("ERROR with i2c")'''
        
        else:
                templateData['chat'].append("tu mensaje no se ha enviado porque no has elegido esa opcion")
        '''render'''
        return render_template('main.html', **templateData)

#method for the devices tab
@app.route('/devices')
def devicesList():
        return render_template('devices.html')


#run the server
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=True)




