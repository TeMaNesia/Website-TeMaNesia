import os
# import pyrebase
import hashlib

from flask import Flask, session, render_template, request, redirect
from firebase_admin import credentials, firestore, initialize_app, auth


app = Flask(__name__)

# config = {
#     'apiKey': "AIzaSyBAFpFJ2I_tx6fEa2ZfLco4smdwofm_S8o",
#     'authDomain': "temanesia-6feb4.firebaseapp.com",
#     'projectId': "temanesia-6feb4",
#     'storageBucket': "temanesia-6feb4.appspot.com",
#     'messagingSenderId': "348340047680",
#     'appId': "1:348340047680:web:834e74dc41adba5c5374a5",
#     'measurementId': "G-G0C48QK7RF",
#     'databaseURL': ''
# }

# firebase = pyrebase.initialize_app(config)
# auth = firebase.auth()


cred = credentials.Certificate('key.json')
initialize_app(cred)
db = firestore.client()

users_collection = db.collection('users')

new_account = {}

@app.route('/', methods=['POST', 'GET'])
def index():
    if('user' in session):
        return render_template('dashboard.html', umessage=session['user'])
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = auth.sign_in_with_email_and_password(email, hashlib.md5(password.encode()).hexdigest())
            session['user'] = user['localId']
            return render_template('dashboard.html', umessage=session['user'])
        
        except:
            return render_template('login.html', umessage="Login gagal, kesalahan email atau password")
        
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    new_account = {}

    if request.method == 'POST':
        new_account['nama_lembaga'] = request.form.get('nama')
        new_account['sektor_lembaga'] = request.form.get('sektor')
        new_account['telepon_lembaga'] = request.form.get('telepon')
        new_account['alamat_lembaga'] = request.form.get('alamat')

        return redirect('/create_account')
    
    return render_template('register.html')

@app.route('/create_account', methods=['POST', 'GET'])
def create_account():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password == confirm:
            new_account['email'] = request.form.get('email')
            new_account['password'] = hashlib.md5(password.encode()).hexdigest()

            return redirect('/email_verification')
    
    return render_template('create_account.html')

@app.route('/email_verification', methods=['POST', 'GET'])
def email_verification():
    if request.method == 'POST':
        # not done
        # auth.send_email_verification(account['idToken'])
        code = request.form.get('code_confirmation')
        true_code = ""
        if code == true_code: 
            user = auth.create_user_with_email_and_password(new_account['email'], new_account['password'])
            users_collection.document(user['localId']).set(new_account)

            return redirect('/')
        
    return render_template('email_verification.html')

@app.route('/logout')
def logout():
    session.pop('user')

    return redirect('/')

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, port=port)