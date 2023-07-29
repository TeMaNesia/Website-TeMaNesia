import json

from requests.exceptions import HTTPError
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from firebase_admin import firestore

from firebase import db, storage_upload, storage_multiple_upload, storage_delete_file


lowongan = Blueprint('lowongan', __name__)

@lowongan.route('/add-lowongan', methods=['POST'])
def add_lowongan():
    new_lowongan = {}

    if request.method == 'POST':
        new_lowongan['ringkasan'] = request.form.get('ringkasan')
        new_lowongan['nama'] = request.form.get('nama')
        new_lowongan['lokasi'] = request.form.get('lokasi')
        new_lowongan['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d') 
        new_lowongan['url'] = request.form.get('url')
        new_lowongan['deskripsi'] = request.form.get('deskripsi')
        new_lowongan['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        new_lowongan['email_penyelenggara'] = request.form.get('email_penyelenggara')
        new_lowongan['created_at'] = datetime.now()
        new_lowongan['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        new_lowongan['status'] = 'Aktif'
        new_lowongan['jenis_kegiatan'] = 'lowongan'
        new_lowongan['foto_penyelenggara'] = request.form.get('foto_penyelenggara')
        new_lowongan['jurusan'] = request.form.getlist('jurusan')

        new_lowongan['poster_filename'] = request.files['poster'].filename
        new_lowongan['poster'] = storage_upload(request.files['poster'], 'poster')

        important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            uploaded_lowongan = db.collection('lowongan').add(new_lowongan)

            for i_file in important_files:
                db.collection('lowongan').document(uploaded_lowongan[1].id).collection('file-penting').add(i_file)

            flash('Lowongan baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))

    return render_template('errors/error-404.html'), 404


@lowongan.route('/edit-lowongan', methods=['POST'])
def edit_lowongan():
    edited_lowongan = {}

    if request.method == 'POST':
        edited_lowongan['ringkasan'] = request.form.get('ringkasan')
        edited_lowongan['nama'] = request.form.get('nama')
        edited_lowongan['lokasi'] = request.form.get('lokasi')
        edited_lowongan['date'] = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        edited_lowongan['penyelenggara_uid'] = request.form.get('penyelenggara_uid')
        edited_lowongan['url'] = request.form.get('url')
        edited_lowongan['deskripsi'] = request.form.get('deskripsi')
        edited_lowongan['created_at'] = datetime.strptime(request.form.get('created_at'), '%Y-%m-%d')
        edited_lowongan['status'] = request.form.get('status')
        edited_lowongan['jenis_kegiatan'] = request.form.get('jenis')
        edited_lowongan['foto_penyelenggara'] = request.form.get('foto_penyelenggara')
        edited_lowongan['email_penyelenggara'] = request.form.get('email')
        edited_lowongan['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        edited_lowongan['jurusan'] = request.form.getlist('jurusan')

        if request.files['poster'].filename != '':
            storage_delete_file(request.form.get('old_poster'))

            edited_lowongan['poster_filename'] = request.files['poster'].filename
            edited_lowongan['poster'] = storage_upload(request.files['poster'], 'poster')
            
        else:
            edited_lowongan['poster'] = request.form.get('old_poster')
        
        old_important_files = db.collection('lowongan').document(request.form.get('id')).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        important_files = []

        if request.files.getlist('file-penting')[0]:
            important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            db.collection('lowongan').document(request.form.get('id')).set(edited_lowongan)

            for i_file in important_files:
                db.collection('lowongan').document(request.form.get('id')).collection('file-penting').add(i_file)

            flash('Data lowongan berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))

    return render_template('errors/error-404.html'), 404


@lowongan.route('/get-lowongan/<id>', methods=['GET'])
def get_lowongan(id):
    data_dict = db.collection('lowongan').document(id).get().to_dict()
    important_files_data = db.collection('lowongan').document(id).collection('file-penting').get()

    data_dict['file_penting'] = [item.to_dict() for item in important_files_data]
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@lowongan.route('/delete-lowongan/<id>', methods=['GET'])
def delete_lowongan(id):
    try:
        data = db.collection('lowongan').document(id).get()
        data_dict = data.to_dict()

        storage_delete_file(data_dict['poster'])

        old_important_files = db.collection('lowongan').document(data.id).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        db.collection('lowongan').document(id).delete()
        flash('Berhasil hapus lowongan', 'success')
        return redirect(url_for('dashboard', role='lowongan', page='lowongan'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='lowongan', page='lowongan'))
    
@lowongan.route('/dashboard/lowongan/lamaran', methods=['POST', 'GET'])
def lamaran():
    if request.method == 'POST':
        lowongan = {}
        lowongan['id'] = request.form.get('id')
        lowongan['nama'] = request.form.get('nama')

        lamaran = db.collection('lamaran').where("id_lowongan", "==", request.form.get('id')).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        data = []
        for doc in lamaran:
            doc_dict = doc.to_dict()
            doc_dict['created_at'] = doc_dict['created_at'].strftime("%d %B %Y")
            doc_dict['id'] = doc.id

            doc_dict['nama'] = db.collection('users_mobile').document(doc_dict['id_users']).get().get('nama')
            
            data.append(doc_dict)

        return render_template(f'dashboard/lowongan/lamaran.html', user=session['user_info'], data_lamaran=data, data_lowongan=lowongan)
    
    return render_template('errors/error-403.html'), 403

@lowongan.route('/status-lamaran', methods=['POST'])
def status_lamaran():
    if request.method == 'POST':
        try:
            lamaran = db.collection('lamaran').document(request.form.get('id'))
            lamaran.update({'status': request.form.get('status')})
            flash('Status lamaran berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='lowongan', page='lowongan'))

    return render_template('errors/error-404.html'), 404


@lowongan.route('/get-lamaran/<id>', methods=['GET'])
def get_lamaran(id):
    data = db.collection('lamaran').document(id).get()
    data_dict = data.to_dict()

    return jsonify(data_dict)