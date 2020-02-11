from flask import *

from flask_pymongo import PyMongo

from flask_bootstrap import Bootstrap

from datetime import *

from flask_moment import Moment

#from pytz import timezone

import pandas_datareader as pdr
import pandas as pd
from passlib.hash import sha256_crypt

import holidays
import requests

app = Flask('my-stock')

app.config['SECRET_KEY'] = 'sOtCk!'

app.config['REMEMBER_COOKIE_DURATION']= timedelta

app.config['MONGO_URI'] = 'mongodb://localhost:27017/my-stock-db'

#app.config['MONGO_URI'] = 'mongodb://richardqlin:linqiwei1@ds211259.mlab.com:11259/mystock?retryWrites=false'

monent = Moment(app)

Bootstrap(app)

mongo = PyMongo(app)

weather_api = 'c115e005de28c13c6e9ff0ad6d7b14ca'

#col = mongo.db.users

#collection = mongo.db.AccountInformation

def offday():
    current = datetime.now()
    us = holidays.UnitedStates(state='CA')
    delete = []
    for k, v in us.items():
        if v == 'Susan B. Anthony Day' or v == 'César Chávez Day' \
                or v == 'César Chávez Day (Observed)' or v == 'Columbus Day' or v == 'Veterans Day':
            delete.append(k)

    for k in delete:
        us.pop(k)
    return current in us

def stock_market():
    print(datetime.now())
    current = datetime.now()
    week = datetime.now().strftime('%w')


    s = timedelta(days = 0)
    if offday() and week =='1':
        s = timedelta(days=3)
    elif offday():
        s = timedelta(days=1)
    elif week =='6':
        s = timedelta(days=1)
    elif week =='0':
        s = timedelta(days=2)

    current = current - s
    current = current.strftime("%Y-%m-%d")
    #current='2019-10-26'
    dowjone = pdr.get_data_yahoo('^DJI', start=current, end=current)['Adj Close']
    dowjone = pd.Series(dowjone[current])
    dow = [x for x in dowjone][0]
    nasd = pdr.get_data_yahoo('^IXIC', start=current, end=current)['Adj Close']
    nasd = pd.Series(nasd[current])
    nas = [x for x in nasd][0]
    stk = [round(dow,5), round(nas,5)]

    return stk

def weather():
    response = requests.get("http://ip-api.com/json/")
    js = response.json()
    city = js['city']

    api = 'c115e005de28c13c6e9ff0ad6d7b14ca'
    api_address = 'http://api.openweathermap.org/data/2.5/weather?appid=' + api + '&q='

    url = api_address + city + '&units=imperial'

    data = requests.get(url).json()
    temp = data['main']['temp']

    humidity = data['main']['humidity']

    wea = data['weather'][0]['main']

    des = data['weather'][0]['description']

    weather_list = [temp,humidity, wea,des,city]
    return weather_list



@app.route('/', methods = ['GET','POST'])
def register():

    session.pop('user-info', None)
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        doc = {}
        doc['email'] = request.form['email']

        found = mongo.db.users.find_one(doc)
        '''if found is not None:
            passcode = found['password']
            if len(passcode) < 77:
                mongo.db.users.remove(found)
        '''
        if found is None:
            doc['firstname'] = request.form['firstname']
            doc['lastname'] = request.form['lastname']
            doc['password'] = sha256_crypt.encrypt(request.form['password'])
            doc['amount'] = 0
            mongo.db.users.insert_one(doc)

            flash('Account created successfully!')
            return redirect('/login')
        else:
            flash('That user name is taken, please try again.')
            return redirect('/')
        '''
        for item in request.form:
            doc[item] = request.form[item]
        user_list= []
        for u in user:
            print(u)
            user_list.append(u['email'])
        print(user_list)
        if doc['email'] in user_list:
            flash( doc['email']+' already registered')
            return redirect('/')
        '''


@app.route('/login', methods =['GET','POST'])
def login():
    #collection = mongo.db.AccountInformation
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':

        term = request.form.get('accept')
        if term == None:
            flash('Please check the terms, thank you.')
            return redirect('/login')
        if term == 'yes':
            email = request.form['email']
            print(email)
            #doc = {'email': request.form['email'], 'password': request.form['password']}
            found = mongo.db.users.find_one({'email':email})
            if found is None:
                print('non')
                flash('Sign Up or Register')
                return redirect('/')
            else:
                try:
                    if sha256_crypt.verify(request.form['password'], found['password']):
                        lst = weather()
                        stk_list = stock_market()
                        session['user-info'] = {'firstname': found['firstname'], 'lastname': found['lastname'],
                                            'email': found['email'], 'loginTime': datetime.utcnow(),'amount':found['amount'],
                                            'temp': lst[0], 'hum': lst[1], 'city':lst[-1], 'weather': lst[2], 'dow': stk_list[0],
                                            'nas': stk_list[1]}
                        return redirect('/account')

                    else:
                        flash('user name and password you entered did not match our record. Please check it again')
                        return redirect('/login')
                except ValueError:
                    flash('password is not encrypted in database, please sign up again, Thank you.')
                    return redirect('/')
@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/account', methods=['GET','POST'])
def account():
    userinfo = mongo.db.users.find({'email': session['user-info']['email']})
    info = [x for x in userinfo]
    if 'user-info' in session:
        if request.method == 'GET':
            return render_template('account.html', saveinfo = info)
        elif request.method == 'POST':
            balance = info[0]['amount']
            amount = request.form['amount']
            if len(amount) > 0:
                amount = int(amount)
            choice = request.form['choice']
            print(choice)
            if choice == 'deposit':
                balance += amount
            elif choice == 'withdraw':
                if balance < amount:
                    flash('Sorry, your account is out of balance')
                else:
                    balance -= amount
            elif choice == 'clear':
                balance = 0
                print(choice, balance)
                mongo.db.users.update({'email': session['user-info']['email']}, {'$set': {'amount': balance}})
                return redirect('/logout')
            print(balance,amount)
            mongo.db.users.update({'email':session['user-info']['email']},{'$set':{'amount':balance}})
            return redirect('/account')


@app.route('/checkout', methods=['GET','POST'])
def checkout():
    if 'user-info' in session:
        if request.method == 'GET':
            savelogin = session['user-info']
            print('save=',savelogin)
            return render_template('checkout.html', entries=savelogin)

        elif request.method == 'POST':
            user = mongo.db.entries.find({'user': session['user-info']['email']})
            info = [x for x in user]
            print('info',info)
            entry = {}
            entry['email'] = session['user-info']['email']
            share = request.form['share']
            tick = request.form['tick']

            week = datetime.now().strftime('%w')
            if week == '6' or week == '0' or offday():
                price = 0
                flash('market closed')
                return redirect('/checkout')
            else:
                cur = datetime.now().strftime("%Y-%m-%d")
                ticker = pdr.get_data_yahoo(tick.upper(), start=cur, end=cur)['Adj Close']
                print(ticker)
                ticker = pd.Series(ticker[cur])
                price = [x for x in ticker][0]
            share = int(share)
            count = 0
            print(count, user.count())
            '''
            if count == user.count() and (not (week == '6' or week == '0')):
                edit = 'insert'
            '''
            entry['tick'] = tick
            entry['share'] = share
            entry['price'] = round(price, 3)
            total = round(int(share) * price, 3)
            entry['total'] = total
            #entry['time'] = datetime.now()
            entry['loginTime'] = session['user-info']['loginTime']

            #entry = {'user': session['user-info']['email'], 'content': request.form['content'], 'time': datetime.utcnow()}

            if len(info) == 0:
                entry['diff']=0
            else:
                for i in info:
                    if entry['tick'] == i['tick']:
                        entry['diff'] = i['price'] * entry['share'] - entry['total']

            session['user-info'] = entry

            return redirect('/checkout')
    else:
        flash('You need to login first')
        return redirect('/login')

@app.route('/stock', methods=['GET','POST'])
def stock():
    #total = 0
    user = mongo.db.users.find({'email': session['user-info']['email']})
    info = [x for x in user]

    total = info[0]['amount']
    global price
    if 'user-info' in session:
        if request.method == 'GET':
            savelogin = mongo.db.entries.find({'user':session['user-info']['email']})
            #for entry in savelogin:
            #    total = total + entry['total']
            savelogin = mongo.db.entries.find({'user': session['user-info']['email']})
            return render_template('stock.html', entries=savelogin, total = total, info = info)
        elif request.method == 'POST':
            edit = 'none'
            user = mongo.db.entries.find({'user': session['user-info']['email']})
            entry = {}
            entry['user'] = session['user-info']['email']
            share = request.form['share']
            tick = request.form['tick']
            act = request.form['action']
            week = datetime.now().strftime('%w')
            print(type(week),week, tick, act)

            if act == 'none':
                flash('you should select buy or sell')
                return redirect('/stock')
            if week == '6' or week == '0' or offday():
                edit ='none'
                act = 'none'
                price = 0
            else:
                cur = datetime.now().strftime("%Y-%m-%d")
                try:
                    ticker = pdr.get_data_yahoo(tick.upper(), start=cur, end=cur)['Adj Close']
                except ValueError:
                    flash('stock market is closed')
                    return redirect('/stock')

                ticker = pd.Series(ticker[cur])
                price = [x for x in ticker][0]
            try:
                share = int(share)
            except ValueError:
                flash('Please fill share numbers.')
                return redirect('/stock')
            count = 0
            for u in user:
                count += 1
                u_share = int(u['share'])
                if act == 'none':
                    break
                print(u['tick'], tick)
                if u['tick'] == tick:
                    count -= 1
                    print(u['tick'],tick)
                    if act == 'buy':
                        share = u_share + share
                        edit = 'edit'
                    elif act == 'sell':
                        print(u_share, share)
                        if u_share > share:
                            share = u_share - share
                            edit = 'edit'
                        elif u_share < share:
                            flash('out of your balance ')
                        elif u_share == share:
                            edit = 'delete'
                    break


            if count == user.count() and act =='sell':
                flash('You have to buy it first')

            print(count, user.count())
            if count == user.count() and (not (week == '6' or week == '0' or offday())):
                edit = 'insert'
            entry['tick'] = tick
            entry['share'] = share
            entry['price'] = round(price,3)
            share_price = round(int(share) * price, 3)
            entry['total'] = share_price
            entry['time'] = datetime.utcnow()
            user = {}
            user['_id'] = info[0]['_id']

            print(edit,act)
            #entry ={'user':session['user-info']['email'],'content':request.form['content'],'time':datetime.utcnow()}
            if edit == 'none' and act == 'none':
                flash ('market closed')
            elif edit == 'edit':
                print(edit,act)
                if act == 'sell':
                    total += share_price
                    mongo.db.users.update_one({'_id':user['_id']}, {'$set' : {'amount': total}})
                if act == 'buy':
                    if total < share_price:
                        flash('There is no enough moeny in Your account ')
                        return redirect('/stock')
                    else:
                        total -= share_price
                        print('total=',total)
                        mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'amount': total}})
                mongo.db.entries.update_one({'tick': entry['tick']},{ '$set':{'share': entry['share'],'total' : entry['total'], 'time': entry['time']}})
            elif edit == 'insert' and act=='buy':
                total -= share_price
                mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'amount': total}})
                mongo.db.entries.insert_one(entry)
            elif edit == 'delete':
                total += share_price
                mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'amount': total}})
                mongo.db.entries.remove({'tick': entry['tick']})
            return redirect('/stock')
    else:
        flash('You need to login first')
        return redirect('/login')

@app.route('/logout')
def logout():
    # removing user information from the session
    session.pop('user-info', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug='True')