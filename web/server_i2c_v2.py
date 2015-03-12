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

tablesNames = ['Digital Output', 'Digital Input',
                       'Analog Input', 'Analog Ouptut']
tablesNamesDict ={'Digital Output':'DO', 'Digital Input':'DI',
                       'Analog Input':'A)', 'Analog Ouptut':'AO'}

error = ""


#code to execute when entered '/'
@app.route("/")
def hello():
	return render_template('main.html', templateData=templateData) #Render the template


#method for the devices tab
@app.route('/devices')
def devicesList():    
        #creates a dict with all the devices in the i2c_devices table
        dbConnection = dbInit()[2]
        devicesTable = dbSelectTable(dbDevicesTable, dbConnection)
        DITable = dbSelectTable(dbDITable, dbConnection)
        DOTable = dbSelectTable(dbDOTable, dbConnection)
        AITable = dbSelectTable(dbAITable, dbConnection)
        AOTable = dbSelectTable(dbAOTable, dbConnection)
        tablesList = [DOTable, DITable, AITable, AOTable]
        
        # it passes it to the template before rendering
        return render_template('devices.html', DevicesTable=devicesTable,
                               TablesList=tablesList, TablesNames = tablesNames,
                               counter = 0)

#method for the new devices form. What happens to create a new device
@app.route('/devices/new_device', methods=['POST'])
def new_device():
        # gets the information from the form
        name = request.form['inputName']
        address = request.form['inputAddress']
        new_device_args = [{'Name': name, 'Address': address}]

        # gets all the entries from the Devices table in the database
        dbConnection = dbInit()[2]
        values = dbSelectTable(dbDevicesTable, dbConnection)

        # Checks that the name is not already used
        for device in values:
                if device.Name == name:
                        break
        else:
                # in case it really doesn't exist yet, create new item in i2c_devices table in database
                dbInsert(dbDevicesTable, dbConnection, new_device_args)
        return redirect('/devices') # go back to the web page

# method for creating a new node inside a device
@app.route('/devices/new_node', methods=['POST'])
def new_node():
        # gets the information from the form
        input_name = request.form['inputName']
        input_pin = request.form['inputPin']
        signal = request.form['signal']
        device_address = request.form['deviceAddress']

        # Arrange the data in the way that it want to be passed to the database (to the dbInsert method)
        print "name: "+input_name+", address:"+device_address+"."
        args=[{'Name': input_name, 'Address': int(device_address), 'Pin': int(input_pin)}]

        # Depending on the kind of signal chosen, select the appropriate db table
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
        
        return redirect(url_for('devicesList'))


####
#### methods for the socket
####        

#connection of the socket
@socketio.on('connect', namespace='/test')
def test_connect():
        pass

# Start reading: an option from a node is selected (delete, on, off, read, cancel, remove)
@socketio.on('start reading', namespace='/test')
def socket_start_reading(msg):
        # gets the relevant information from the form
        sub_inputs = msg['data'].split()
        table = tablesNamesDict[tablesNames[int(sub_inputs[0])]]
        device_name = sub_inputs[1]
        address = sub_inputs[2]
        pin = sub_inputs[3]
        instr = sub_inputs[4]

        # depending on the action that the user want to take place 
        # DELETE
        if instr == 'delete':
                dbConnection = dbInit()[2]
                if dbDeleteDevice(dbTablesDict, address, dbConnection):
                        emit('message', {'data': 'success deleting'})
                        emit('redirect',{'url': url_for('devicesList')})
                else:
                        emit('message', {'data': 'fail deleting'})

        # READ
        elif instr == 'read':
                for key in comThreads:  # checks that the thread is not running already
                        if key == (address + pin):
                                emit('reading',
                                     {'data': 'thread already started',
                                      'pin': pin}, namespace='/test')
                                break
                else:   # if it is not created, then creates it 
                        myCom = create_CommunicationThread('thread', int(address), int(pin),
                                                    0, 0, 0, bus, 2, socketio)
                        
                        comThreads[address + pin] = myCom
                        comThreads[address + pin].start()

        # CANCEL
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

                emit('reading',{'data': '',
                                'pin': pin}, namespace='/test')

        # REMOVE
        elif instr == 'remove':
                try:
                        dbConnection = dbInit()[2]
                        dbDelete(dbTablesDict[table], int(address), int(pin), dbConnection)
                        emit('redirect',{'url': url_for('devicesList')})
                except Exception, e:
                        global error
                        error = e
                
        # ON
        elif instr == 'On':
                myCom = create_CommunicationThread('thread', int(address), int(pin),
                                                   1, 1, 1, bus, 0, socketio)
                        
                comThreads[address + pin] = myCom
                comThreads[address + pin].start()

        # OFF
        elif instr == 'Off':
                myCom = create_CommunicationThread('thread', int(address), int(pin),
                                                   1, 1, 0, bus, 0, socketio)
                        
                comThreads[address + pin] = myCom
                comThreads[address + pin].start()

        # OTHER
        else:
                emit('message', {'data': instr})


#run the server
if __name__ == "__main__":
        socketio.run(app, host='0.0.0.0', port=80)


