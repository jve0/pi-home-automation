from flask import Flask, render_template, request, redirect, url_for, jsonify
from server_db import *
import datetime

import smbus
import time

from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
    close_room, disconnect

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

#Threading and sockets
##thread = None
##socketio = SocketIO(app)

#method for writing to the i2c bus
def writeI2c(address, pin, R_W, A_D, value):
        bus.write_i2c_block_data(address, i2c_cmd, [pin, R_W, A_D, value])


#method for reading to the i2c bus
def readI2c(address, pin):
        writeI2c(address, pin, 0, 0, 0) #format: [address, pin, R/W, A/D, value]
        time.sleep(0.1) #delay 0.1 seconds. Otherwise you get IOError
        data = bus.read_byte(address)
        
        return data



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
##        global thread
##        if thread != None:
##                test_disconnect()
##                thread = None
                
        
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
        dbConnection = dbInit()[2]
        device_address = dbSelectAddressByName(dbDevicesTable, device_name, dbConnection)

        tables={}
        for tb in dbTablesDict:
                if tb!= 'Devices':
                        tables[tb]= dbSelectRowByAddress(dbTablesDict[tb], device_address, dbConnection)
        '''threading'''
##        global thread
##        if thread is None:
##                thread = Thread(target=background_thread)
##                thread.start()
        '''in case ther's an error'''
        global error
        current_error = error
        error = ""

        '''render'''
        return render_template('details.html',
                               device_name=device_name,
                               device_address=device_address,
                               tables=tables,
                               error=current_error)



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

        '''Determine wheter is an analog or digital signal'''
        if 'D' in selected_table:
                A_D = 1
        elif 'A' in selected_table:
                A_D = 0
                 
        '''Determine wheter is a Write or a Read command'''
        if 'I' in selected_table:
                R_W = 0
        elif 'O' in selected_table:
                R_W = 1

        '''clasified regarding the instruction'''
        if instruction == 'On' and R_W == 1:
                value = 1
        elif instruction == 'Off' or R_W == 0:
                value = 0
        else:
                return instruction


        try:
                if instruction == 'remove':
                        dbConnection = dbInit()[2]
                        dbDelete(dbTablesDict[selected_table], int(device_address), int(pin), dbConnection)
                else:
                        writeI2c(int(device_address), int(pin), R_W, A_D, value)
        except Exception, e:
                global error
                error = str(e)
        
        return redirect(url_for('particular_device_details', device_name=device_name))


@app.route('/_stuff', methods=['GET'])
def change_html_value():
        input = request.args.get('s')
        sub_inputs = input.split()
        table = sub_inputs[0]
        address = sub_inputs[1]
        pin = sub_inputs[2]
        instr = sub_inputs[3]

        try:
                data = readI2c(int(address), int(pin))
        except Exception, e:
                global error
                error = str(e)
                data = error
        
        return jsonify(value=str(data), pin=str(pin))

####
#### methods for the socket
####
##def background_thread():
##    """Example of how to send server generated events to clients."""
##    count = 0
##    while True:
##        time.sleep(10)
##        count += 1
##        socketio.emit('my response',
##                      {'data': 'Server generated event', 'count': count},
##                      namespace='/test')
##        #socketio.emit('my response',{'data': 
##
###simple emit
##@socketio.on('my event', namespace='/test')
##def test_message(message):
##    session['receive_count'] = session.get('receive_count', 0) + 1
##    emit('my response',
##         {'data': message['data'], 'count': session['receive_count']})
##
###broadcast emit
##@socketio.on('my broadcast event', namespace='/test')
##def test_broadcast_message(message):
##    session['receive_count'] = session.get('receive_count', 0) + 1
##    emit('my response',
##         {'data': message['data'], 'count': session['receive_count']},
##         broadcast=True)
##
###yes
##@socketio.on('disconnect request', namespace='/test')
##def disconnect_request():
##    session['receive_count'] = session.get('receive_count', 0) + 1
##    emit('my response',
##         {'data': 'Disconnected!', 'count': session['receive_count']})
##    disconnect()
##
###maybe
##@socketio.on('connect', namespace='/test')
##def test_connect():
##    emit('my response', {'data': 'Connected', 'count': 0})
##
###don't think so
##@socketio.on('disconnect', namespace='/test')
##def test_disconnect():
##    print('Client disconnected')
##



#run the server
if __name__ == "__main__":
        app.run(host='0.0.0.0', port=80,debug=True)




