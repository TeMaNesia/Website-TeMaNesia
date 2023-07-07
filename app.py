import os
import pyrebase
import json
import locale

from requests.exceptions import HTTPError
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'secret'
locale.setlocale(locale.LC_TIME, 'id_ID.utf8')

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
            return render_template(f'dashboard/{role}/{page}.html', user=session['user_info'], data_user=all_data)

    elif session['user_info']['role'] == 'Penyelenggara Lomba' and role == 'lomba':
        if page == 'lomba':
            all_data = get_all_user_lomba(session['user_info']['localId'])
            return render_template(f'dashboard/{role}/{page}.html', user=session['user_info'], data_lomba=all_data)
        
    elif session['user_info']['role'] == 'Penyelenggara Sertifikasi' and role == 'sertifikasi':
        if page == 'sertifikasi':
            all_data = get_all_user_sertifikasi(session['user_info']['localId'])
            return render_template(f'dashboard/{role}/{page}.html', user=session['user_info'], data_sertifikasi=all_data)
        
    elif session['user_info']['role'] == 'Penyelenggara Beasiswa' and role == 'beasiswa':
        if page == 'beasiswa':
            all_data = get_all_user_beasiswa(session['user_info']['localId'])
            return render_template(f'dashboard/{role}/{page}.html', user=session['user_info'], data_beasiswa=all_data)
        
    return render_template('errors/error-403.html'), 403
        

@app.route('/logout')
def logout():
    session.pop('user_info')
    return redirect('/')


@app.route('/add-lomba', methods=['POST'])
def add_lomba():
    new_lomba = {}

    if request.method == 'POST':
        new_lomba['ringkasan'] = request.form.get('ringkasan')
        new_lomba['nama'] = request.form.get('nama')
        new_lomba['lokasi'] = request.form.get('lokasi')
        new_lomba['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d') 
        new_lomba['url'] = request.form.get('url')
        new_lomba['deskripsi'] = request.form.get('deskripsi')
        new_lomba['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        new_lomba['email_penyelenggara'] = request.form.get('email_penyelenggara')
        new_lomba['created_at'] = datetime.now()
        new_lomba['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        new_lomba['status'] = 'Aktif'
        new_lomba['jenis_kegiatan'] = 'Lomba'

        try:
            db.collection('lomba').document().set(new_lomba)
            flash('Lomba baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

    return render_template('errors/error-404.html'), 404


@app.route('/edit-lomba', methods=['POST'])
def edit_lomba():
    edited_lomba = {}

    if request.method == 'POST':
        edited_lomba['ringkasan'] = request.form.get('ringkasan')
        edited_lomba['nama'] = request.form.get('nama')
        edited_lomba['lokasi'] = request.form.get('lokasi')
        edited_lomba['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        edited_lomba['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        edited_lomba['url'] = request.form.get('url')
        edited_lomba['deskripsi'] = request.form.get('deskripsi')
        edited_lomba['created_at'] = datetime.strptime(request.form.get('created_at'), '%Y-%m-%d')
        edited_lomba['status'] = request.form.get('status')
        edited_lomba['jenis_kegiatan'] = request.form.get('jenis')
        edited_lomba['email_penyelenggara'] = request.form.get('email')
        edited_lomba['nama_penyelenggara'] = request.form.get('nama_penyelenggara')

        try:
            db.collection('lomba').document(request.form.get('id')).set(edited_lomba)
            flash('Data lomba berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

    return render_template('errors/error-404.html'), 404


@app.route('/get-lomba/<id>', methods=['GET'])
def get_lomba(id):
    data = db.collection('lomba').document(id).get()

    data_dict = data.to_dict()
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@app.route('/delete-lomba/<id>', methods=['GET'])
def delete_lomba(id):
    try:
        db.collection('lomba').document(id).delete()
        flash('Berhasil hapus lomba', 'success')
        return redirect(url_for('dashboard', role='lomba', page='lomba'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='lomba', page='lomba'))


@app.route('/edit-status', methods=['POST'])
def edit_status():
    if request.method == 'POST':
        try:
            user = db.collection('users_website').document(request.form.get('id'))
            user.update({'status': request.form.get('status')})
            flash('Status pengguna berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='admin', page='verification'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='admin', page='verification'))

    return render_template('errors/error-404.html'), 404


@app.route('/get-user/<id>', methods=['GET'])
def get_user(id):
    data = db.collection('users_website').document(id).get()
    data_dict = data.to_dict()
    data_dict['tanggal_daftar'] = data_dict['tanggal_daftar'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@app.route('/delete-user/<id>', methods=['GET'])
def delete_user(id):
    try:
        db.collection('users_website').document(id).delete()
        flash('Berhasil hapus pengguna', 'success')
        return redirect(url_for('dashboard', role='admin', page='verification'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='admin', page='verification'))


@app.route('/add-sertifikasi', methods=['POST'])
def add_sertifikasi():
    new_sertifikasi = {}

    if request.method == 'POST':
        new_sertifikasi['ringkasan'] = request.form.get('ringkasan')
        new_sertifikasi['nama'] = request.form.get('nama')
        new_sertifikasi['lokasi'] = request.form.get('lokasi')
        new_sertifikasi['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d') 
        new_sertifikasi['url'] = request.form.get('url')
        new_sertifikasi['deskripsi'] = request.form.get('deskripsi')
        new_sertifikasi['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        new_sertifikasi['email_penyelenggara'] = request.form.get('email_penyelenggara')
        new_sertifikasi['created_at'] = datetime.now()
        new_sertifikasi['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        new_sertifikasi['status'] = 'Aktif'
        new_sertifikasi['jenis_kegiatan'] = 'Sertifikasi'

        try:
            db.collection('sertifikasi').document().set(new_sertifikasi)
            flash('sertifikasi baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

    return render_template('errors/error-404.html'), 404


@app.route('/edit-sertifikasi', methods=['POST'])
def edit_sertifikasi():
    edited_sertifikasi = {}

    if request.method == 'POST':
        edited_sertifikasi['ringkasan'] = request.form.get('ringkasan')
        edited_sertifikasi['nama'] = request.form.get('nama')
        edited_sertifikasi['lokasi'] = request.form.get('lokasi')
        edited_sertifikasi['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        edited_sertifikasi['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        edited_sertifikasi['url'] = request.form.get('url')
        edited_sertifikasi['deskripsi'] = request.form.get('deskripsi')
        edited_sertifikasi['created_at'] = datetime.strptime(request.form.get('created_at'), '%Y-%m-%d')
        edited_sertifikasi['status'] = request.form.get('status')
        edited_sertifikasi['jenis_kegiatan'] = request.form.get('jenis')
        edited_sertifikasi['email_penyelenggara'] = request.form.get('email')
        edited_sertifikasi['nama_penyelenggara'] = request.form.get('nama_penyelenggara')

        try:
            db.collection('sertifikasi').document(request.form.get('id')).set(edited_sertifikasi)
            flash('Data sertifikasi berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

    return render_template('errors/error-404.html'), 404


@app.route('/get-sertifikasi/<id>', methods=['GET'])
def get_sertifikasi(id):
    data = db.collection('sertifikasi').document(id).get()

    data_dict = data.to_dict()
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@app.route('/delete-sertifikasi/<id>', methods=['GET'])
def delete_sertifikasi(id):
    try:
        db.collection('sertifikasi').document(id).delete()
        flash('Berhasil hapus sertifikasi', 'success')
        return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))
    

@app.route('/add-beasiswa', methods=['POST'])
def add_beasiswa():
    new_beasiswa = {}

    if request.method == 'POST':
        new_beasiswa['ringkasan'] = request.form.get('ringkasan')
        new_beasiswa['nama'] = request.form.get('nama')
        new_beasiswa['lokasi'] = request.form.get('lokasi')
        new_beasiswa['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d') 
        new_beasiswa['url'] = request.form.get('url')
        new_beasiswa['deskripsi'] = request.form.get('deskripsi')
        new_beasiswa['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        new_beasiswa['email_penyelenggara'] = request.form.get('email_penyelenggara')
        new_beasiswa['created_at'] = datetime.now()
        new_beasiswa['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        new_beasiswa['status'] = 'Aktif'
        new_beasiswa['jenis_kegiatan'] = 'Beasiswa'

        try:
            db.collection('beasiswa').document().set(new_beasiswa)
            flash('beasiswa baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

    return render_template('errors/error-404.html'), 404


@app.route('/edit-beasiswa', methods=['POST'])
def edit_beasiswa():
    edited_beasiswa = {}

    if request.method == 'POST':
        edited_beasiswa['ringkasan'] = request.form.get('ringkasan')
        edited_beasiswa['nama'] = request.form.get('nama')
        edited_beasiswa['lokasi'] = request.form.get('lokasi')
        edited_beasiswa['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        edited_beasiswa['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        edited_beasiswa['url'] = request.form.get('url')
        edited_beasiswa['deskripsi'] = request.form.get('deskripsi')
        edited_beasiswa['created_at'] = datetime.strptime(request.form.get('created_at'), '%Y-%m-%d')
        edited_beasiswa['status'] = request.form.get('status')
        edited_beasiswa['jenis_kegiatan'] = request.form.get('jenis')
        edited_beasiswa['email_penyelenggara'] = request.form.get('email')
        edited_beasiswa['nama_penyelenggara'] = request.form.get('nama_penyelenggara')

        try:
            db.collection('beasiswa').document(request.form.get('id')).set(edited_beasiswa)
            flash('Data beasiswa berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

    return render_template('errors/error-404.html'), 404


@app.route('/get-beasiswa/<id>', methods=['GET'])
def get_beasiswa(id):
    data = db.collection('beasiswa').document(id).get()

    data_dict = data.to_dict()
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@app.route('/delete-beasiswa/<id>', methods=['GET'])
def delete_beasiswa(id):
    try:
        db.collection('beasiswa').document(id).delete()
        flash('Berhasil hapus beasiswa', 'success')
        return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))


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


port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(threaded=True, port=port, debug=True)