from sqlalchemy import *

#basic lines to initialise the database
def dbInit():
    engine = create_engine('sqlite:///devices.db')
    metadata = MetaData(engine)
    conn = engine.connect()
    return [engine, metadata, conn]

#Create/reflects the tables in the database
def dbCreateTables(metadata, engine, count):
    if count == 0:
        table = Table('i2c_devices', metadata,
                           Column('Address', Integer),
                           Column('Name', String(20)))
    elif count==1: 
        table = Table('DO', metadata,
                      Column('Address', Integer),
                      Column('Name', String(20)),
                      Column('Pin', Integer))
    elif count==2:
        table = Table('DI', metadata,
                         Column('Address', Integer),
                         Column('Name', String(20)),
                         Column('Pin', Integer))
    elif count==3:
        table = Table('AO', metadata,
                         Column('Address', Integer),
                         Column('Name', String(20)),
                         Column('Pin', Integer))
    elif count==4:
        table = Table('AI', metadata,
                         Column('Address', Integer),
                         Column('Name', String(20)),
                         Column('Pin', Integer))
    else:
        table = 0

    metadata.create_all(engine) # create_all checks the existence of a table before creating, so it is safe to call it multiple times'''
    
    return table

## Insert: create new value in table
def dbInsert(table, connection, args):
    i = table.insert()
    i.execute(args)
    # args must be a dict with the names of the columns and their values
    # e.g. args = [{'Name': 'jose', 'Address':0},{'Name':'pepe', 'Address': 1}]

## Select Table: gets a certain table
def dbSelectTable(table, connection):
    return connection.execute(select([table])).fetchall()
    #this returns a dict, thus the best way to get the rows is by for loop

## Select Row By Address: when the address is known, it gets its characteristics in a particular table
def dbSelectRowByAddress(table, address, connection):
    selection = connection.execute(select([table]).where(table.c.Address == address))
    return selection.fetchall()     #return a nx2 array (Address, Pin)

## Select Address By Name: when the name of a device is known, it returns its address
def dbSelectAddressByName(table, name, connection):
    s = "SELECT Address FROM " + str(table) + " WHERE Name='" + name+ "'"
    selection = connection.execute(s).fetchone()
    return selection[0] # return an integer

## Update: updates a value in a table
def dbUpdate(table, connection, args):
    u = table.update()
    u.execute(args)

## Delete: deletes a value from a table
def dbDelete(table, address, pin, connection):
    connection.execute(table.delete().where(and_(table.c.Address == address,
                                                 table.c.Pin == pin)))

## Delete Device: from a particular address, it deletes every row related to it
def dbDeleteDevice(tablesDict, address, connection):
    for table in tablesDict:
        connection.execute(tablesDict[table].delete().where(tablesDict[table].c.Address == address))
    else:
        return True
    return False

## Drop: deletes a complete table
def dbDrop(table, engine, connection):
    connection.close()
    table.drop(engine)
    conn = engine.connect()
    
