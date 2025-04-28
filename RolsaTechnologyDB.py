import sqlite3 

con= sqlite3.connect('RolsaTechnology.db')
cur=con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS tblCustomer(
    custID INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL, 
    address TEXT NOT NULL,
    postcode TEXT NOT NULL,
    phoneNumber TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tblTariffs(
tariffID INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL,
description TEXT NOT NULL,
price REAL NOT NULL)""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tblBooking(
bookingID INTEGER PRIMARY KEY AUTOINCREMENT,
custID INTEGER,
tariffID INTEGER,
date TEXT NOT NULL,
status TEXT NOT NULL,
time TEXT NOT NULL,
amount REAL NOT NULL,
FOREIGN KEY (custID) REFERENCES tblCustomer(custID),
FOREIGN KEY (tariffID) REFERENCES tblTariffs(tariffID))""")

tariffs=[
    ('Standard consulatation', 'One hour consultation, where you can find out all important information, and understand if solar panel is suitable for you', 100.00),
    ('Premium consulatation','A two-hour in-depth consultation, including a detailed energy assessment and personalized solar panel recommendation', 200.00),
    ('Installation Package - Basic', 'Installation of a small PVsystem (up to 2 kW) with basic monitoring features', 4500.00),
    ('Installation Package - Advanced', 'Installation of a medium solar PV system (up to 4 kW) with advanced monitoring and battary storage', 7500.00),
    ('Maintenance Plan','Annual maintenance service for solar panels, including cleaning and performance checks.',150.00),
    ('Energy Optimization Consultation', 'A one-hour session to optimize energy usage and maximize solar panel efficiency.', 120.00)
    ]
cur.executemany("INSERT INTO tblTariffs(name,description,price) VALUES (?, ?, ?)", tariffs)

con.commit()
con.close()


