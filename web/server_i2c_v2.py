from flask import Flask, render_template, request, redirect, url_for
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

devicesData ={
        'my_first_node': {
                 'Address': 0x04,
                 'DO': 13,
                 'AO': 3
                 },
        'my_second_node': {
                 'Address': 0x05,
                 'DO': 13,
                 }
        }

#i2c bus init
bus = smbus.SMBus(1)

#i2c and gpio address. This is the address we setup in the arduino program
i2c_address = 0x04
i2c_cmd = 0x01



#method for writing to the i2c bus
def writeByte(value):
        bus.write_byte(address, 13)
        bus.write_byte(address, value)
        return -1

#method for reading to the i2c bus
def readByte():
        number = bus.read_byte(address)
        return number

def writeI2c(pin, value):
        bus.write_i2c_block_data(i2c_address, i2c_cmd, ConvertListToSend(pin,value))

def ConvertListToSend(pin, value):
        converted = []
        converted.append(pin)
        converted.append(value)
        return converted

#code to execute when entered '/'
@app.route("/")
def hello():
	now = datetime.datetime.now()
	timeString = now.strftime("%Y-%m-%d %H:%M")
	templateData['time'] = timeString
	templateData['chat'] = []

	'''render the template'''
	return render_template('main.html', templateData=templateData)


#code to execute when POST a form
@app.route('/', methods=['POST'])
def my_form_post():
        '''access the form elements in the dictionary request.form'''
        txtText = int(request.form['txtText'])
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
                                writeI2c(txtPin, txtText)
                                templateData['chat'].append("enviado")
                        else:
                                writeI2c(txtPin, 0)
                                templateData['chat'].append("enviado")
                except Exception, e:
                        return str(e)        
        else:
                templateData['chat'].append("tu mensaje no se ha enviado porque no has elegido esa opcion")
        '''render'''
        return render_template('main.html', **templateData)

#method for the devices tab
@app.route('/devices')
def devicesList():
        return render_template('devices.html', devicesData=devicesData)

#method for the new devices form
@app.route('/devices/new_device', methods=['POST'])
def new_device():
        name = request.form['inputName']
        address = request.form['inputAddress']

        for device in devicesData:
                if device == name:
                        break
        else:
                devicesData[name] = { 'Address': address }
        return redirect('/devices')

#method for the details of the devices
@app.route('/devices/details', methods=['POST'])
def device_details():
        specific_device = request.form['submit']
        return render_template('details.html', device_name=specific_device, specificDeviceData=devicesData[specific_device])


#method for handle the user commands related to inputs and outputs
@app.route('/devices/details/command', methods=['POST'])
def user_command():
        command = request.form['but'] #returns a string: "device_name device_name.key On/Off"
        coms = command.split()
        device_name = coms[0]
        device_key = coms[1]
        instruction = coms[2]

        try:
                if instruction == 'On':
                        writeI2c(devicesData[device_name][device_key], 1)
                elif instruction == 'Off':
                        writeI2c(devicesData[device_name][device_key], 0)
        except Exception, e:
                return str(e)
                
        return 'wee'



#run the server
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=True)




