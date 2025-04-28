"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""


import atexit
from flask import Flask, render_template, request, flash, redirect,session
import webbrowser
import threading 
from flask_bcrypt import Bcrypt, bcrypt
import sqlite3
from datetime import datetime,date
import atexit




app = Flask(__name__)
app.secret_key="vika26"
bcrypt=Bcrypt(app)


# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app
#define the device fot the energy usage calculator 
devices=[
        {'name':'Air conditioner', 'power':3000},
        {'name': 'Heater', 'power':7000},
        {'name': 'Dishwasher', 'power':1500},
        {'name': 'Toaster', 'power':1000},
        {'name': 'Fan', 'power':200},
        {'name': 'Television', 'power':500},
        {'name': 'Your device', 'power':0},
        ]
ELECTRICITY_COST=24.5

@app.route('/')
def home():
       
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def post_login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        errors=[]
        #add validation and checking from the database 
        try:
            with sqlite3.connect('RolsaTechnology.db') as con:
                curs=con.execute("SELECT email, password,custID,firstname FROM tblCustomer WHERE email=?",[email])
                row=curs.fetchone()
                if row is None:
                    errors.append("This email is not register or you have a type mistake, please enter again or go to register page.")
                else:
                    hashedPassword=row[1]
                    if not bcrypt.check_password_hash(hashedPassword,password):
                        errors.append('Invalid password,please try again')
                    else:
                        #save the user date for the session period 
                        session['cust_id']=row[2]
                        session['email']=row[0]
                        session['name']=row[3]

        except sqlite3.Error as e:
            errors.append(f"Database error: {e}")
        finally:
            con.close()
        if errors:
            for error in errors:
                flash(error)
            return redirect('/login')
        else:
            return render_template('home.html')




@app.route('/energy')
def energy_usage_calculator():


        return render_template('energyUsage.html', devices=devices)


@app.route('/energy', methods=['POST'])
def calculated_energy():
    if request.method=='POST':
        device_name=request.form['device']
        power=float(request.form['power'])
        hours=float(request.form['hours'])

        #calculation for energy usage over day, week , month and year 
        daily_usage=(power*hours)/1000
        daily_cost=daily_usage*(ELECTRICITY_COST/100)

        weekly_usage= daily_usage * 7
        weekly_cost=weekly_usage*(ELECTRICITY_COST/100)

        monthly_usage=daily_usage*30
        monthly_cost=monthly_usage*(ELECTRICITY_COST/100)

        yearly_usage=daily_usage*365
        yearly_cost=yearly_usage*(ELECTRICITY_COST/100)
        calculation={
            'device_name':device_name,
            'daily_usage':round(daily_usage,2),
            'daily_cost':round(daily_cost,2),
            'weekly_usage':round(weekly_usage,2),
            'weekly_cost':round(weekly_cost,2),
            'monthly_usage':round(monthly_usage,2),
            'monthly_cost':round(monthly_cost,2),
            'yearly_usage':round(yearly_usage,2),
            'yearly_cost':round(yearly_cost,2)
            }
        return render_template('energyUsage.html',calculation=calculation, devices=devices )



@app.route('/tariffs')
def tariffs():
    #connect the database and diplay all tariffs to the user 
    with sqlite3.connect('RolsaTechnology.db') as con:
        cur=con.execute("SELECT * FROM tblTariffs")
        rows = cur.fetchall()
        tariffs = [{'id':row[0],'name': row[1], 'description': row[2], 'price': row[3]} for row in rows]  
        return render_template('tariffs.html', tariffs=tariffs)

@app.route('/tariffs', methods=['POST'])
def post_tariffs():
    if request.method=='POST':
        tariff_id=request.form['tariff_id']
        #connect with the database to take and output some important information to the users. 
        with sqlite3.connect('RolsaTechnology.db') as con:
            cur= con.execute("SELECT tariffID,name,price FROM tblTariffs WHERE tariffID =?", [tariff_id])
            tariff=cur.fetchone()
        #check for session if user is logged in to allow to make booking or not. 
        if 'cust_id' not in session or 'email' not in session:
            flash('Session invalid. Please log in again.')
            return redirect('/login')
        else:   
            return render_template('booking.html', tariff_id=tariff[0], tariff_name=tariff[1], tariff_price=tariff[2])

is_shutdown=False

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/booking', methods=['POST'] )
def post_booking():
    if request.method=='POST':
        custDate=request.form['date']
        time=request.form['time']
        tariff_id=request.form['tariff_id']
        tariff_price=request.form['tariff_price']
        cust_id=session.get('cust_id')
        #add validation for the date 
        selectedDate=datetime.strptime(custDate, '%Y-%m-%d').date()
        today=date.today()
        errors=[]
        if selectedDate<today:
            errors.append('The date of the appoitment can`t be in the past')
        with sqlite3.connect('RolsaTechnology.db') as con:
            cur= con.execute("SELECT date, time FROM tblBooking WHERE date =? AND time= ?",(custDate, time) )
            result=cur.fetchone()
            if result:
                errors.append('This date and time is allready booked, please choose different date or time')

            if errors:
                for error in errors:
                    flash(error)
                return redirect('/booking')
            else:
                with sqlite3.connect('RolsaTechnology.db') as con:# add the data to the booking table 
                    cur=con.execute('INSERT INTO tblBooking (custID,tariffID, date, status, time, amount ) VALUES (?,?,?,?,?,?)',
                                    (cust_id,tariff_id,custDate,'Pending',time,tariff_price))
                #output the confirmation page
                return render_template('booking_confirmation.html', date=custDate, time=time)

app.route('/confirmation')
def confirmation():
    return render_template('booking_confirmation.html')



@app.route('/register')
def register():
    return render_template('register.html ')

@app.route('/register', methods=['POST'])
def post_register():
    if request.method=='POST':
        name=request.form['name']
        lastname=request.form['lastname']
        address=request.form['address']
        postcode=request.form['postcode']
        phone=request.form['phone']
        email=request.form['email']
        password=request.form['password']
        confirmedPassword=request.form['confirmedPassword']
        errors=[]
        #validation of user inputs 
        if len(name)<3:
            errors.append("Your name must be more than 3 characters long")
        if not name.isalpha():
            errors.append("Your name must contain just letters")
        if len(lastname)<3:
            errors.append("Your last name must be more than 3 characters long")
        if not lastname.isalpha():
            errors.append("Your last name must contain just letters")
        if len(address)<3:
            errors.append("Your address must be more than 3 characters long")
        if len(postcode)<5 or len(postcode)>8:
            errors.append("Your post code must be more than 5 characters long and less than 8")
        if phone.startswith("+"):
            phone_validation=phone[1:]
        if not phone_validation.isdigit():
                errors.append('Your phone should containe just digits (except for the leading +)')
        elif len(phone)<11 or len(phone)>13:
                errors.append("Your phone must be more than 11 characters long and less than 13")
 
        if '.' not in email and  '@' not in email:
             errors.append("Your email must have both '@' and '.' ")
        else:
            local,domain=email.split('@',1)
            if " " in domain:
                errors.append('Domain must not contain spaces')
            elif not domain:
                errors.append('Domain must not be empty')
            elif "." not in domain:
                errors.append('Domain must contain at least one dot')
            elif len(domain)>255:
                errors.append('Domain must not be bigger that 255 characters')
            elif " " in local:
                errors.append('Local must not contain spaces')
            elif not local:
                errors.append('Local must not be empty')
            elif len(local)>64:
                errors.append('Local must not be bigger that 64 characters')
        if len(password)<8:
            errors.append("Your password must be more than 8 characters long")
        if not any(char.isdigit() for char in password):
             errors.append("Your password must have at least one number ")
        if  not any(char.isupper() for char in password):
             errors.append("Your password must have at least one uppercase ")
        if  not any(char.islower() for char in password):
             errors.append("Your password must have at least one lowercase ")
        SPECIAL_CHARACTER="!$%^&*()_-+=@'#~<>,.?/|"
        if not any(char in SPECIAL_CHARACTER for char in password):
            errors.append("Your password must have at least one special character ")
        if password !=confirmedPassword:
            errors.append("Your password does not match confirmed password, please enter again ")
        with sqlite3.connect('RolsaTechnology.db') as con:
            curs=con.execute("SELECT * FROM tblCustomer WHERE email=(?)",[email])
            rows=curs.fetchall()
            if rows:
                errors.append("This email is already registered, please use another email or log in to the system ")
        if errors:
            for error in errors:
                flash(error)
            return redirect('/register')
        else:
            #adding data to database 
            hashedPassword=bcrypt.generate_password_hash(password)
            with sqlite3.connect('RolsaTechnology.db') as con:
                cur=con.execute('INSERT INTO tblCustomer ( firstname,lastname,address,postcode, phoneNumber,email , password) VALUES (?,?,?,?,?,?,?)',
                                (name,lastname,address,postcode,phone,email,hashedPassword))
                con.commit()
                cust_id=cur.lastrowid
                #saving user details for session time
                session['cust_id']=cust_id
                session['email']= email
                session['name']= name
            return render_template('home.html')


@app.route('/profile')
def profile():
    cust_id=session.get('cust_id')
    name=session.get('name')
    
    with sqlite3.connect('RolsaTechnology.db') as con:
       
    # Query to join tblBooking and tblTariffs to get tariff_name
        cur = con.execute("""
            SELECT b.date, b.time, b.amount, t.name, b.bookingID
            FROM tblBooking b
            JOIN tblTariffs t ON b.tariffID = t.tariffID
            WHERE b.custID = ?
            AND status = 'Pending'
        """, [cust_id])
        rows = cur.fetchall()
        bookings = [{'date':row[0],'time': row[1], 'amount': row[2],'tariff_name':row[3], 'booking_id':row[4]} for row in rows]  
        return render_template('profile.html', bookings=bookings, name=name)

@app.route('/cancel', methods=['POST'])
def cancellation():
    if request.method=='POST':
        booking_id=request.form['booking_id']
        with sqlite3.connect('RolsaTechnology.db') as con:
            cur=con.execute('UPDATE tblBooking SET status = ? WHERE bookingID = ? ',('Cancelled',booking_id))
            flash('The booking was sucssefully cancelled')
            return redirect('/profile')


@app.route('/carbon')
def carbon():
    return render_template('carbon.html')

#emission factors 
TRANSPORT={
    'car':3000, #kg CO₂ per year
    'bus':1000,#kg CO₂ per year
    'train':500,#kg CO₂ per year
    'bike':0 #kg CO₂ per year
    }
DIET={
    'meat':2.5,# Diet emissions (kg CO₂ per day)
    'vegetarian':1.5,
    'vegan':1
    }

ELECTRICITY_EMISSION=0.233 # UK average kg CO₂ per kWh
GAS_EMISSION=2.01 # UK average kg CO₂ per cubic meter of gas
SHORTFLIGHTS_EMISSION=125.5 # kg CO₂ (set the flight to 500km)
LONGFLIGHTS_EMISSION=195# kg CO₂ (set the flight to 1000km)
@app.route('/carbon', methods=['POST'])
def post_carbon():
    if request.method=='POST':
        electricity=float(request.form['electricity'])
        gas=float(request.form['gas'])
        transport=request.form['transport']
        shortFlights=int(request.form['shortflights'])
        longFlights=int(request.form['longfliets'])
        diet=request.form['diet']

        #calculation of carbon footprints taking average emission 
        electricityUsage=(electricity*12)*ELECTRICITY_EMISSION
        gasUsage=(gas*12)*GAS_EMISSION
        transportUsage=TRANSPORT[transport]
        dietUsage=DIET[diet]*365
        shortFlightsUsage=shortFlights*SHORTFLIGHTS_EMISSION
        longFlightsUsage=longFlights*LONGFLIGHTS_EMISSION
        total_footprint= electricityUsage + gasUsage +transportUsage + dietUsage +shortFlightsUsage + longFlightsUsage
        total_footprint=round(total_footprint,2)
        return render_template('carbon_results.html', footprint=total_footprint)

@app.route('/carbon_results')
def carbon_results():
    return render_template('carbon_results.html')



@app.route('/greentechnology')
def greentechnology():
    
    return render_template('greentechnology.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def clear_session():
    global is_shutdown
    is_shutdown=True
    session.clear()

atexit.register(clear_session)

def web_running():
    webbrowser.open_new('http://127.0.0.1:5000')
    

if __name__ == '__main__':
    threading.Thread(target=web_running).start()
    app.run(debug=True)
    
