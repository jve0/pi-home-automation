from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, redirect, url_for, jsonify
from server_db import *
import datetime

import smbus
import time

from i2c_threads import create_CommunicationThread

from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug = True

#turn the flask app into a socketio app
socketio = SocketIO(app)

#dict to store the different threads created
comThreads = {}

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


error = ""


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
##        if rdbI2c:
##                rdbOnOff = True if request.form['rdbOnOff']=='on' else False
##                try:
##                        if rdbOnOff:
##                                writeI2c(txtPin, txtText)
##                                templateData['chat'].append("enviado")
##                        else:
##                                writeI2c(txtPin, 0)
##                                templateData['chat'].append("enviado")
##                except Exception, e:
##                        return str(e)        
##        else:
##                templateData['chat'].append("tu mensaje no se ha enviado porque no has elegido esa opcion")
        '''render'''
        return render_template('main.html', **templateData)

#method for the devices tab
@app.route('/devices')
def devicesList():    
        #gets a dict with all the devices in the i2c_devices table
        dbConnection = dbInit()[2]
        devicesData = dbSelectTable(dbDevicesTable, dbConnection)
        return render_template('devices.html', devicesData=devicesData)

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
                '''create new item in i2c_devices table in database'''
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
        '''get the address of the device, looking for the name received in the devices table'''
        device_address = dbSelectAddressByName(dbDevicesTable, device_name, dbInit()[2])
        tables={}
        '''with the address found, look in every table and get the data'''
        for tb in dbTablesDict:
                if tb!= 'Devices':
                        tables[tb]= dbSelectRowByAddress(dbTablesDict[tb], device_address, dbConnection)

        '''in case there's an error'''
        global error
        current_error = error
        error = ""
             
        '''render'''
        #return tables
        return render_template('details.html',
                               device_name=device_name,
                               device_address=device_address,
                               tables=tables,
                               error=current_error)



#method for handle the user commands related to inputs and outputs
##@app.route('/devices/details/command', methods=['POST'])
##def user_command():
##        device_name = request.form['deviceName']
##        command = request.form['but'] #returns a string: "selected_table device_address node.Pin On/Off"
##        coms = command.split()
##        selected_table = coms[0]
##        device_address = coms[1]
##        pin = coms[2]
##        instruction = coms[3]
##
##        value = 0
##
##        '''Determine whether is an analog or digital signal'''
##        if 'D' in selected_table:
##                A_D = 1
##        elif 'A' in selected_table:
##                A_D = 0
##                 
##        '''Determine wheter is a Write or a Read command'''
##        if 'I' in selected_table:
##                R_W = 0
##        elif 'O' in selected_table:
##                R_W = 1
##
##        '''clasified regarding the instruction'''
##        if instruction == 'On' and R_W == 1:
##                value = 1
##        elif instruction == 'Off' or R_W == 0:
##                value = 0
##        else:
##                return instruction
##
##
##        try:
##                if instruction == 'remove':
##                        dbConnection = dbInit()[2]
##                        dbDelete(dbTablesDict[selected_table], int(device_address), int(pin), dbConnection)
##                else:                   
##                        myCom = create_CommunicationThread('first_thread', int(device_address), int(pin),
##                                                    A_D, R_W, value, bus, 2, socketio)
##                        myCom.start()
##                                                                    
##        except Exception, e:
##                global error
##                error = str(e)
##        
##        return redirect(url_for('particular_device_details', device_name=device_name))
##


####
#### methods for the socket
####        

#connection of the socket
@socketio.on('connect', namespace='/test')
def test_connect():
        pass

@socketio.on('start reading', namespace='/test')
def socket_start_reading(msg):
        sub_inputs = msg['data'].split()
        table = sub_inputs[0]
        device_name = sub_inputs[1]
        address = sub_inputs[2]
        pin = sub_inputs[3]
        instr = sub_inputs[4]
        
        if instr == 'read':
                for key in comThreads:
                        if key == (address + pin):
                                emit('reading',
                                     {'data': 'thread already started',
                                      'pin': pin}, namespace='/test')
                                break
                else:
                        myCom = create_CommunicationThread('thread', int(address), int(pin),
                                                    0, 0, 0, bus, 2, socketio)
                        
                        comThreads[address + pin] = myCom
                        comThreads[address + pin].start()
                
        elif instr == 'cancel':
                if (address + pin) in comThreads:
                        if comThreads[address + pin].getExitFlag():
                                emit('message', {'data': 'thread cancelling'})
                                comThreads[address + pin].setExitFlag()
                                comThreads.pop(address + pin, None)
                        elif not comThreads[address + pin].getExitFlag():
                                comThreads.pop(address + pin, None)
                                emit('message', {'data':str(comThreads[address + pin].getExitFlag())})
                        
                        else:
                               emit('message', {'data': 'thread not cancelled'})
                else:
                        emit('message', {'data': 'thread does not exist'})

                emit('reading',{'data': '-',
                                'pin': pin}, namespace='/test')

        elif instr == 'remove':
                try:
                        dbConnection = dbInit()[2]
                        dbDelete(dbTablesDict[table], int(address), int(pin), dbConnection)
                        socketio.emit('redirect', {'device_name': device_name})
                except Exception, e:
                        global error
                        error = e
                
        
        elif instr == 'On':
                myCom = create_CommunicationThread('thread', int(address), int(pin),
                                                   1, 1, 1, bus, 0, socketio)
                        
                comThreads[address + pin] = myCom
                comThreads[address + pin].start()
        elif instr == 'Off':
                myCom = create_CommunicationThread('thread', int(address), int(pin),
                                                   1, 1, 0, bus, 0, socketio)
                        
                comThreads[address + pin] = myCom
                comThreads[address + pin].start()
        else:
                emit('message', {'data': instr})

#run the server
if __name__ == "__main__":
        socketio.run(app, host='0.0.0.0', port=80)


