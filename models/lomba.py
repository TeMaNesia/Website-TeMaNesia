import json

from requests.exceptions import HTTPError
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from firebase_admin import firestore

from firebase import db, storage_upload, storage_multiple_upload, storage_delete_file


lomba = Blueprint('lomba', __name__)

@lomba.route('/add-lomba', methods=['POST'])
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
        new_lomba['foto_penyelenggara'] = request.form.get('foto_penyelenggara')
        new_lomba['jurusan'] = request.form.getlist('jurusan')

        new_lomba['poster_filename'] = request.files['poster'].filename
        new_lomba['poster'] = storage_upload(request.files['poster'], 'poster')

        important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            uploaded_lomba = db.collection('lomba').add(new_lomba)

            for i_file in important_files:
                db.collection('lomba').document(uploaded_lomba[1].id).collection('file-penting').add(i_file)

            flash('Lomba baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

    return render_template('errors/error-404.html'), 404


@lomba.route('/edit-lomba', methods=['POST'])
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
        edited_lomba['foto_penyelenggara'] = request.form.get('foto_penyelenggara')
        edited_lomba['email_penyelenggara'] = request.form.get('email')
        edited_lomba['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        edited_lomba['jurusan'] = request.form.getlist('jurusan')

        if request.files['poster'].filename != '':
            storage_delete_file(request.form.get('old_poster'))

            edited_lomba['poster_filename'] = request.files['poster'].filename
            edited_lomba['poster'] = storage_upload(request.files['poster'], 'poster')
            
        else:
            edited_lomba['poster'] = request.form.get('old_poster')
        
        old_important_files = db.collection('lomba').document(request.form.get('id')).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        important_files = []

        if request.files.getlist('file-penting')[0]:
            important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            db.collection('lomba').document(request.form.get('id')).set(edited_lomba)

            for i_file in important_files:
                db.collection('lomba').document(request.form.get('id')).collection('file-penting').add(i_file)

            flash('Data lomba berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

    return render_template('errors/error-404.html'), 404


@lomba.route('/get-lomba/<id>', methods=['GET'])
def get_lomba(id):
    data_dict = db.collection('lomba').document(id).get().to_dict()
    important_files_data = db.collection('lomba').document(id).collection('file-penting').get()

    data_dict['file_penting'] = [item.to_dict() for item in important_files_data]
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@lomba.route('/delete-lomba/<id>', methods=['GET'])
def delete_lomba(id):
    try:
        data = db.collection('lomba').document(id).get()
        data_dict = data.to_dict()

        storage_delete_file(data_dict['poster'])

        old_important_files = db.collection('lomba').document(data.id).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        db.collection('lomba').document(id).delete()
        flash('Berhasil hapus lomba', 'success')
        return redirect(url_for('dashboard', role='lomba', page='lomba'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='lomba', page='lomba'))
    

@lomba.route("/search_peserta", methods=["GET"])
def search_peserta():
    search_text = request.args.get("search_text")
    docs = db.collection("users_mobile").where("nim_nisn", "==", int(search_text)).get()

    for doc in docs:
        data = doc.to_dict()
        data['id_peserta'] = doc.id
        
    return jsonify(data)
    

@lomba.route('/dashboard/lomba/send-sertificate', methods=['POST', 'GET'])
def send_sertificate():

    if request.method == 'GET':
        id = request.args.get('id')
        name = request.args.get('name') 

        lomba = {}
        lomba['id'] = id
        lomba['nama'] = name

        sertificate = db.collection('sertificate').where("id_lomba", "==", id).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        data = []
        for doc in sertificate:
            doc_dict = doc.to_dict()
            doc_dict['tanggal_pembuatan'] = doc_dict['tanggal_pembuatan'].strftime("%d %B %Y")
            doc_dict['id'] = doc.id
            data.append(doc_dict)

        return render_template(f'dashboard/lomba/send_sertificate.html', user=session['user_info'], data_sertifikat=data, data_lomba=lomba)
    
    # if request.method == 'POST':
    #     lomba = {}
    #     lomba['id'] = request.form.get('id')
    #     lomba['nama'] = request.form.get('nama')

    #     sertificate = db.collection('sertificate').where("id_lomba", "==", request.form.get('id')).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    #     data = []
    #     for doc in sertificate:
    #         doc_dict = doc.to_dict()
    #         doc_dict['tanggal_pembuatan'] = doc_dict['tanggal_pembuatan'].strftime("%d %B %Y")
    #         doc_dict['id'] = doc.id
    #         data.append(doc_dict)

    #     return render_template(f'dashboard/lomba/send_sertificate.html', user=session['user_info'], data_sertifikat=data, data_lomba=lomba)
    
    return render_template('errors/error-403.html'), 403


@lomba.route('/add-sertificate', methods=['POST'])
def add_sertificate():
    new_sertificate = {}

    if request.method == 'POST':
        new_sertificate['nama'] = request.form.get('nama')
        new_sertificate['nama_peserta'] = request.form.get('nama_peserta')
        new_sertificate['nim_nisn_peserta'] = request.form.get('no_peserta')
        new_sertificate['nomor'] = request.form.get('nomor')
        new_sertificate['tanggal_pembuatan'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d') 

        new_sertificate['sertifikat_filename'] = request.files['file-sertifikat'].filename
        new_sertificate['file_sertifikat'] = storage_upload(request.files['file-sertifikat'], 'file-sertifikat')
        new_sertificate['created_at'] = datetime.now()

        new_sertificate['id_lomba'] = request.form.get('id')
        new_sertificate['id_peserta'] =  request.form.get('id_peserta')

        try:
            db.collection('sertificate').add(new_sertificate)
            flash('Sertifikat lomba berhasil dikirimkan', 'success')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

    return render_template('errors/error-404.html'), 404


@lomba.route('/delete-sertifikat/<doc>/<id>', methods=['GET'])
def delete_sertifikat(doc, id):
    try:
        data = db.collection('sertificate').document(id).get()
        data_dict = data.to_dict()

        storage_delete_file(data_dict['file_sertifikat'])

        db.collection('sertificate').document(id).delete()
        flash('Berhasil hapus sertifikat lomba', 'success')
        return redirect(url_for('dashboard', role='lomba', page='lomba'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='lomba', page='lomba'))


@lomba.route('/get-sertifikat/<doc>/<id>', methods=['GET'])
def get_sertifikat(doc, id):
    data_dict = db.collection('sertificate').document(id).get().to_dict()

    data_dict['tanggal_pembuatan'] = data_dict['tanggal_pembuatan'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@lomba.route('/edit-sertificate', methods=['POST'])
def edit_sertificate():
    edited_sertificate = {}

    if request.method == 'POST':
        edited_sertificate['nama'] = request.form.get('nama')
        edited_sertificate['nama_peserta'] = request.form.get('nama_peserta')
        edited_sertificate['nim_nisn_peserta'] = request.form.get('no_peserta')
        edited_sertificate['nomor'] = request.form.get('nomor')
        edited_sertificate['tanggal_pembuatan'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d') 
        edited_sertificate['created_at'] = datetime.strptime(request.form.get('created_at'), '%Y-%m-%d')

        edited_sertificate['id_lomba'] = request.form.get('id_lomba')
        edited_sertificate['id_peserta'] = request.form.get('id_peserta')

        if request.files['file-sertifikat'].filename != '':
            storage_delete_file(request.form.get('old_sertificate'))
            edited_sertificate['sertifikat_filename'] = request.files['file-sertifikat'].filename
            edited_sertificate['file_sertifikat'] = storage_upload(request.files['file-sertifikat'], 'file-sertifikat')
            
        else:
            edited_sertificate['file_sertifikat'] = request.form.get('old_sertificate')
            edited_sertificate['sertifikat_filename'] = request.form.get('old_sertificate_name')
    
        try:
            # db.collection('lomba').document(request.form.get('id_lomba')).collection('sertificate').document(request.form.get('id')).set(edited_sertificate)
            db.collection('sertificate').document(request.form.get('id')).set(edited_sertificate)
            flash('Data sertifikat lomba berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lomba', page='lomba'))

    return render_template('errors/error-404.html'), 404