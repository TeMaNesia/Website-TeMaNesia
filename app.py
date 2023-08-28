import os
import json
import locale

from requests.exceptions import HTTPError
from flask import Flask, session, render_template, request, redirect, url_for, flash
from firebase_admin import firestore
from datetime import datetime

from firebase import db, auth, storage_upload
from models.beasiswa import beasiswa
from models.verification import verification
from models.lomba import lomba
from models.sertifikasi import sertifikasi
from models.lowongan import lowongan


app = Flask(__name__)

app.register_blueprint(verification)
app.register_blueprint(lomba)
app.register_blueprint(beasiswa)
app.register_blueprint(sertifikasi)
app.register_blueprint(lowongan)

app.secret_key = 'secret'
locale.setlocale(locale.LC_TIME, 'id_ID.utf8')


@app.route('/', methods=['POST', 'GET'])
def index():
    if('user_info' not in session):
        return redirect('/login')
    
    else:
        flash('Selamat datang di TeMaNesia', 'success')
        if session['user_info']['role'] == 'Admin':
            return redirect(url_for('dashboard', role='admin', page='verification'))
        
        elif session['user_info']['role'] == 'Penyelenggara Lomba':
            return redirect(url_for('dashboard', role='lomba', page='lomba'))
        
        elif session['user_info']['role'] == 'Penyelenggara Sertifikasi':
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))
        
        elif session['user_info']['role'] == 'Penyelenggara Beasiswa':
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))
        
        elif session['user_info']['role'] == 'Penyelenggara Lowongan':
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))


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
            
            data = db.collection('users_website').document(session['user_info']['localId']).get().to_dict()
            session['user_info']['role'] = data.get('role')
            session['user_info']['nama_lembaga'] = data.get('nama_lembaga')
            session['user_info']['foto'] = data.get('logo')

            if session['user_info']['role'] == 'Admin':
                flash('Selamat datang di TeMaNesia', 'success')
                return redirect(url_for('dashboard', role='admin', page='verification'))
            
            else:
                if data.get('status') == 'Nonaktif':
                    flash('Status akun anda masih nonaktif, segera hubungi admin', 'error')
                    return redirect(url_for('login'))
                
                flash('Selamat datang di TeMaNesia', 'success')
                if session['user_info']['role'] == 'Penyelenggara Lomba':
                    return redirect(url_for('dashboard', role='lomba', page='lomba'))
                
                elif session['user_info']['role'] == 'Penyelenggara Sertifikasi':
                    return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))
                
                elif session['user_info']['role'] == 'Penyelenggara Beasiswa':
                    return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))
                
                elif session['user_info']['role'] == 'Penyelenggara Lowongan':
                    return redirect(url_for('dashboard', role='lowongan', page='lowongan'))
        
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
        password = request.form.get('password')
        new_account['status'] = 'Nonaktif'
        new_account['tanggal_daftar'] = datetime.now()
        new_account['logo'] = storage_upload(request.files['logo'], 'profile_picture')

        try:
            user = auth.create_user_with_email_and_password(new_account['email'], password)
            db.collection('users_website').document(user['localId']).set(new_account)
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


@app.route('/dashboard/<role>/<page>')
def dashboard(role, page):
    if('user_info' not in session):
        return redirect('/')

    if session['user_info']['role'] == 'Admin' and role == 'admin':
        if page == 'verification':
            all_data = get_all_users_data()
            return render_template(f'dashboard/admin/verification.html', user=session['user_info'], data_user=all_data)

    elif session['user_info']['role'] == 'Penyelenggara Lomba' and role == 'lomba':
        if page == 'lomba':
            all_data = get_all_user_lomba(session['user_info']['localId'])
            return render_template(f'dashboard/lomba/lomba.html', user=session['user_info'], data_lomba=all_data)
        
    elif session['user_info']['role'] == 'Penyelenggara Sertifikasi' and role == 'sertifikasi':
        if page == 'sertifikasi':
            all_data = get_all_user_sertifikasi(session['user_info']['localId'])
            return render_template(f'dashboard/sertifikasi/sertifikasi.html', user=session['user_info'], data_sertifikasi=all_data)
        
    elif session['user_info']['role'] == 'Penyelenggara Beasiswa' and role == 'beasiswa':
        if page == 'beasiswa':
            all_data = get_all_user_beasiswa(session['user_info']['localId'])
            return render_template(f'dashboard/beasiswa/beasiswa.html', user=session['user_info'], data_beasiswa=all_data)
        
    elif session['user_info']['role'] == 'Penyelenggara Lowongan' and role == 'lowongan':
        if page == 'lowongan':
            all_data = get_all_user_lowongan(session['user_info']['localId'])
            return render_template(f'dashboard/lowongan/lowongan.html', user=session['user_info'], data_lowongan=all_data)
        
    return render_template('errors/error-403.html'), 403
        

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


def get_all_users_data():
    documents = db.collection('users_website').order_by("tanggal_daftar", direction=firestore.Query.DESCENDING).stream()

    data = []
    for doc in documents:
        doc_dict = doc.to_dict()

        if doc_dict['role'] == 'Admin':
            continue
        
        doc_dict['tanggal_daftar'] = doc_dict['tanggal_daftar'].strftime("%d %B %Y")
        doc_dict['id'] = doc.id
        data.append(doc_dict)

    return data


def get_all_user_lomba(user_id):
    documents = db.collection('lomba').where("penyelenggara_uid", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    data = []
    for doc in documents:
        doc_dict = doc.to_dict()
        doc_dict['date'] = doc_dict['date'].strftime("%d %B %Y")
        doc_dict['id'] = doc.id
        data.append(doc_dict)

    return data


def get_all_user_sertifikasi(user_id):
    documents = db.collection('sertifikasi').where("penyelenggara_uid", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    data = []
    for doc in documents:
        doc_dict = doc.to_dict()
        doc_dict['date'] = doc_dict['date'].strftime("%d %B %Y")
        doc_dict['id'] = doc.id
        data.append(doc_dict)

    return data


def get_all_user_beasiswa(user_id):
    documents = db.collection('beasiswa').where("penyelenggara_uid", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    data = []
    for doc in documents:
        doc_dict = doc.to_dict()
        doc_dict['date'] = doc_dict['date'].strftime("%d %B %Y")
        doc_dict['id'] = doc.id
        data.append(doc_dict)

    return data


def get_all_user_lowongan(user_id):
    documents = db.collection('lowongan').where("penyelenggara_uid", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    data = []
    for doc in documents:
        doc_dict = doc.to_dict()
        doc_dict['date'] = doc_dict['date'].strftime("%d %B %Y")
        doc_dict['id'] = doc.id
        data.append(doc_dict)

    return data


port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')