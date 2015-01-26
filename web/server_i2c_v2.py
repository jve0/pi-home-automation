from flask import Flask, render_template, request, redirect, url_for
from server_db import *
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
bus = smbus.SMBus(1)

#database init
s = dbInit()
dbEngine = s[0]
dbMetadata = s[1]
dbConnection = s[2]

#init necessary tables in database and take them from it
dbDevicesTable = dbCreateTables(dbMetadata, dbEngine, 0)
dbDOTable = dbCreateTables(dbMetadata, dbEngine, 1)
dbDITable = dbCreateTables(dbMetadata, dbEngine, 2)
dbAOTable = dbCreateTables(dbMetadata, dbEngine, 3)
dbAITable = dbCreateTables(dbMetadata, dbEngine, 4)
dbTablesDict = {'Devices': dbDevicesTable,
                'DO': dbDOTable,
                'DI': dbDITable,
                'AI': dbAITable,
                'AO': dbAOTable}

#i2c and gpio address. This is the address we setup in the arduino program
i2c_address = 0x04
i2c_cmd = 0x01



#method for writing to the i2c bus
def writeI2c(address, pin, value):
        bus.write_i2c_block_data(address, i2c_cmd, ConvertListToSend(pin,value))

def ConvertListToSend(pin, value):
        converted = []
        converted.append(pin)
        converted.append(value)
        return converted


#method for reading to the i2c bus
def readByte():
        number = bus.read_byte(address)
        return number


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
        #create a dict with all the devices in the i2c_devices table
        dbConnection = dbInit()[2]
        values = dbSelectTable(dbDevicesTable, dbConnection)
        return render_template('devices.html', devicesData=values)

#method for the new devices form
@app.route('/devices/new_device', methods=['POST'])
def new_device():
        name = request.form['inputName']
        address = request.form['inputAddress']
        new_device_args = [{'Name': name, 'Address': address}]

        dbConnection = dbInit()[2]
        values = dbSelectTable(dbDevicesTable, dbConnection)

        for device in values:
                if device.Name == name:
                        break
        else:
                #create new item in i2c_devices table in database
                dbInsert(dbDevicesTable, dbConnection, new_device_args)
        return redirect('/devices')

#method for a new node inside a device
@app.route('/devices/new_node', methods=['POST'])
def new_node():
        input_name = request.form['inputName']
        input_pin = request.form['inputPin']
        signal = request.form['signal']
        device_address = request.form['deviceAddress']
        device_name = request.form['deviceName']

        args=[{'Name': input_name, 'Address': int(device_address), 'Pin': int(input_pin)}]

        if signal == 'Digital Output':
                dbInsert(dbDOTable, dbConnection, args)
        elif signal == 'Digital Input':
                dbInsert(dbDITable, dbConnection, args)
        elif signal == 'Analog Input':
                dbInsert(dbAITable, dbConnection, args)
        elif signal == 'Analog Output':
                dbInsert(dbAOTable, dbConnection, args)
        else:
                return str(0)
        
        return redirect(url_for('particular_device_details', device_name=device_name))


#method for the details of the devices
@app.route('/devices/details', methods=['POST'])
def device_details():
        device_name = request.form['submit']
        return redirect(url_for('particular_device_details', device_name=device_name))

#method for the page of each device
@app.route('/<device_name>')
def particular_device_details(device_name):
        dbConnection = dbInit()[2]
        device_address = dbSelectAddressByName(dbDevicesTable, device_name, dbConnection)

        tables={}
        for tb in dbTablesDict:
                if tb!= 'Devices':
                        tables[tb]= dbSelectRowByAddress(dbTablesDict[tb], device_address, dbConnection)

        return render_template('details.html',
                               device_name=device_name,
                               device_address=device_address,
                               tables=tables)



#method for handle the user commands related to inputs and outputs
@app.route('/devices/details/command', methods=['POST'])
def user_command():
        device_name = request.form['deviceName']
        command = request.form['but'] #returns a string: "selected_table device_address node.Pin On/Off"
        coms = command.split()
        selected_table = coms[0]
        device_address = coms[1]
        pin = coms[2]
        instruction = coms[3]

        try:
                if instruction == 'On':
                        writeI2c(int(device_address), int(pin), 1)
                elif instruction == 'Off':
                        writeI2c(int(device_address), int(pin), 0)
                elif instruction == 'remove':
                        dbConnection = dbInit()[2]
                        dbDelete(dbTablesDict[selected_table], int(device_address), int(pin), dbConnection)
                else:
                        return instruction

        except Exception, e:
                return str(e)
        
        return redirect(url_for('particular_device_details', device_name=device_name))



#run the server
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80, debug=True)




