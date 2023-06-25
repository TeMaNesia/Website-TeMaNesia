import os
import pyrebase

from flask import Flask, session, render_template, request, redirect, url_for, flash
from firebase_admin import credentials, firestore, initialize_app


app = Flask(__name__)
app.secret_key = 'secret'

config = {
    'apiKey': "AIzaSyBAFpFJ2I_tx6fEa2ZfLco4smdwofm_S8o",
    'authDomain': "temanesia-6feb4.firebaseapp.com",
    'projectId': "temanesia-6feb4",
    'storageBucket': "temanesia-6feb4.appspot.com",
    'messagingSenderId': "348340047680",
    'appId': "1:348340047680:web:834e74dc41adba5c5374a5",
    'measurementId': "G-G0C48QK7RF",
    'databaseURL': ''
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

cred = credentials.Certificate('key.json')
initialize_app(cred)
db = firestore.client()

users_collection = db.collection('users')


@app.route('/', methods=['POST', 'GET'])
def index():
    if('user' not in session):
        return redirect('/login')
    
    return render_template('dashboard.html')


@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_info = auth.get_account_info(user['idToken'])['users'][0]
            session['user_info'] = user_info

            if session['user_info']['emailVerified'] == False:
                flash('Email akun anda belum terverifikasi', 'error')
                return redirect(url_for('login'))
            
            status = users_collection.document(user['localId']).get().to_dict().get('status')

            if status == 'Nonaktif':
                flash('Status akun anda masih nonaktif, segera hubungi admin', 'error')
                return redirect(url_for('login'))

            return render_template('dashboard.html') 
        
        except Exception as e:
            flash("Email atau password salah", 'error')
            return render_template('authentication/login.html')
        
    return render_template('authentication/login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    new_account = {}

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        new_account['nama_lembaga'] = request.form.get('nama')
        new_account['sektor_lembaga'] = request.form.get('sektor')
        new_account['role'] = request.form.get('role')
        new_account['telepon_lembaga'] = request.form.get('telepon')
        new_account['alamat_lembaga'] = request.form.get('alamat')

        if password == confirm:
            new_account['email'] = request.form.get('email')
            new_account['password'] = password
            new_account['status'] = 'Nonaktif'

        try:
            user = auth.create_user_with_email_and_password(new_account['email'], new_account['password'])
            users_collection.document(user['localId']).set(new_account)
            auth.send_email_verification(user['idToken'])

            flash('Akun berhasil dibuat, silahkan hubungi admin untuk verifikasi', 'success')
            return redirect(url_for('email_verification'))

        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('register'))
        
    return render_template('authentication/register.html')


@app.route('/verify-email', methods=['GET'])
def email_verification():
    return render_template('authentication/email_verification.html')


@app.route('/logout')
def logout():
    session.pop('user_info')
    return redirect('/')


@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/error-403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/error-404.html'), 404

@app.errorhandler(500)
def system_error(e):
    return render_template('errors/error-500.html'), 500



port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(threaded=True, port=port, debug=True)