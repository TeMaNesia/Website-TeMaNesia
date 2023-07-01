import os
import pyrebase
import locale
import json

from requests.exceptions import HTTPError
from flask import Flask, session, render_template, request, redirect, url_for, flash
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime


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

locale.setlocale(locale.LC_TIME, 'id_ID.utf8')

users_collection = db.collection('users')


@app.route('/', methods=['POST', 'GET'])
def index():
    if('user_info' not in session):
        return redirect('/login')
    
    else:
        flash('Selamat datang di TeMaNesia', 'success')
        if session['user_info']['role'] == 'Admin':
            return redirect(url_for('dashboard', role='admin', page='verification'))


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
            
            data = users_collection.document(session['user_info']['localId']).get().to_dict()
            session['user_info']['role'] = data.get('role')
            session['user_info']['nama_lembaga'] = data.get('nama_lembaga')

            if session['user_info']['role'] != 'Admin':
                if data.get('status') == 'Nonaktif':
                    flash('Status akun anda masih nonaktif, segera hubungi admin', 'error')
                    return redirect(url_for('login'))
                
            flash('Selamat datang di TeMaNesia', 'success')
            if session['user_info']['role'] == 'Admin':
                session['user_info']['users_data'] = get_users_data()
                return redirect(url_for('dashboard', role='admin', page='verification'))
        
        except Exception as e:
            flash("Email atau password salah", 'error')
            return render_template('authentication/login.html')
        
    return render_template('authentication/login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    new_account = {}

    if request.method == 'POST':
        new_account['nama_lembaga'] = request.form.get('nama')
        new_account['sektor_lembaga'] = request.form.get('sektor')
        new_account['role'] = request.form.get('role')
        new_account['telepon_lembaga'] = request.form.get('telepon')
        new_account['alamat_lembaga'] = request.form.get('alamat')

        new_account['email'] = request.form.get('email')
        new_account['password'] = request.form.get('password')
        new_account['status'] = 'Nonaktif'
        new_account['tanggal_daftar'] = datetime.now().strftime("%d %B %Y")

        try:
            user = auth.create_user_with_email_and_password(new_account['email'], new_account['password'])
            users_collection.document(user['localId']).set(new_account)
            auth.send_email_verification(user['idToken'])

            flash('Akun berhasil dibuat, silahkan hubungi admin untuk verifikasi', 'success')
            return redirect(url_for('email_verification'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('register'))
        
    return render_template('authentication/register.html')


@app.route('/verify-email', methods=['GET'])
def email_verification():
    return render_template('authentication/email_verification.html')


@app.route('/logout')
def logout():
    session.pop('user_info')
    return redirect('/')


@app.route('/dashboard/<role>/<page>')
def dashboard(role, page):
    return render_template(f'dashboard/{role}/{page}.html', user=session['user_info'])


@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/error-403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/error-404.html'), 404

@app.errorhandler(500)
def system_error(e):
    return render_template('errors/error-500.html'), 500


def get_users_data():
    documents = users_collection.where('role', '!=', 'Admin').stream()

    data = []
    for doc in documents:
        doc_data = doc.to_dict()
        data.append(doc_data)

    return data

port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(threaded=True, port=port, debug=True)