import json

from requests.exceptions import HTTPError
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

from firebase import db, storage_upload, storage_multiple_upload, storage_delete_file


beasiswa = Blueprint('beasiswa', __name__)

@beasiswa.route('/add-beasiswa', methods=['POST'])
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
        new_beasiswa['jenis_kegiatan'] = 'beasiswa'
        new_beasiswa['foto_penyelenggara'] = request.form.get('foto_penyelenggara')
        new_beasiswa['jurusan'] = request.form.getlist('jurusan')

        new_beasiswa['poster_filename'] = request.files['poster'].filename
        new_beasiswa['poster'] = storage_upload(request.files['poster'], 'poster')

        important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            uploaded_beasiswa = db.collection('beasiswa').add(new_beasiswa)

            for i_file in important_files:
                db.collection('beasiswa').document(uploaded_beasiswa[1].id).collection('file-penting').add(i_file)

            flash('Beasiswa baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

    return render_template('errors/error-404.html'), 404


@beasiswa.route('/edit-beasiswa', methods=['POST'])
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
        edited_beasiswa['foto_penyelenggara'] = request.form.get('foto_penyelenggara')
        edited_beasiswa['email_penyelenggara'] = request.form.get('email')
        edited_beasiswa['nama_penyelenggara'] = request.form.get('nama_penyelenggara')
        edited_beasiswa['jurusan'] = request.form.getlist('jurusan')

        if request.files['poster'].filename != '':
            storage_delete_file(request.form.get('old_poster'))

            edited_beasiswa['poster_filename'] = request.files['poster'].filename
            edited_beasiswa['poster'] = storage_upload(request.files['poster'], 'poster')
            
        else:
            edited_beasiswa['poster'] = request.form.get('old_poster')
        
        old_important_files = db.collection('beasiswa').document(request.form.get('id')).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        important_files = []

        if request.files.getlist('file-penting')[0]:
            important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            db.collection('beasiswa').document(request.form.get('id')).set(edited_beasiswa)

            for i_file in important_files:
                db.collection('beasiswa').document(request.form.get('id')).collection('file-penting').add(i_file)

            flash('Data beasiswa berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))

    return render_template('errors/error-404.html'), 404


@beasiswa.route('/get-beasiswa/<id>', methods=['GET'])
def get_beasiswa(id):
    data_dict = db.collection('beasiswa').document(id).get().to_dict()
    important_files_data = db.collection('beasiswa').document(id).collection('file-penting').get()

    data_dict['file_penting'] = [item.to_dict() for item in important_files_data]
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@beasiswa.route('/delete-beasiswa/<id>', methods=['GET'])
def delete_beasiswa(id):
    try:
        data = db.collection('beasiswa').document(id).get()
        data_dict = data.to_dict()

        storage_delete_file(data_dict['poster'])

        old_important_files = db.collection('beasiswa').document(data.id).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        db.collection('beasiswa').document(id).delete()
        flash('Berhasil hapus beasiswa', 'success')
        return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='beasiswa', page='beasiswa'))