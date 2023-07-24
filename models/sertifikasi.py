import json

from requests.exceptions import HTTPError
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

from firebase import db, storage_upload, storage_multiple_upload, storage_delete_file


sertifikasi = Blueprint('sertifikasi', __name__)

@sertifikasi.route('/add-sertifikasi', methods=['POST'])
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

        new_sertifikasi['poster_filename'] = request.files['poster'].filename
        new_sertifikasi['poster'] = storage_upload(request.files['poster'], 'poster')

        important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            uploaded_sertifikasi = db.collection('sertifikasi').add(new_sertifikasi)

            for i_file in important_files:
                db.collection('sertifikasi').document(uploaded_sertifikasi[1].id).collection('file-penting').add(i_file)

            flash('Sertifikasi baru berhasil ditambahkan', 'success')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

    return render_template('errors/error-404.html'), 404


@sertifikasi.route('/edit-sertifikasi', methods=['POST'])
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

        if request.files['poster'].filename != '':
            storage_delete_file(request.form.get('old_poster'))

            edited_sertifikasi['poster_filename'] = request.files['poster'].filename
            edited_sertifikasi['poster'] = storage_upload(request.files['poster'], 'poster')
            
        else:
            edited_sertifikasi['poster'] = request.form.get('old_poster')
        
        old_important_files = db.collection('sertifikasi').document(request.form.get('id')).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        important_files = []

        if request.files.getlist('file-penting')[0]:
            important_files = storage_multiple_upload(request.files.getlist('file-penting'), 'file-penting')

        try:
            db.collection('sertifikasi').document(request.form.get('id')).set(edited_sertifikasi)

            for i_file in important_files:
                db.collection('sertifikasi').document(request.form.get('id')).collection('file-penting').add(i_file)

            flash('Data sertifikasi berhasil diperbaharui', 'success')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

        except HTTPError as e:
            flash(json.loads(e.strerror)['error']['message'], 'error')
            return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))

    return render_template('errors/error-404.html'), 404


@sertifikasi.route('/get-sertifikasi/<id>', methods=['GET'])
def get_sertifikasi(id):
    data_dict = db.collection('sertifikasi').document(id).get().to_dict()
    important_files_data = db.collection('sertifikasi').document(id).collection('file-penting').get()

    data_dict['file_penting'] = [item.to_dict() for item in important_files_data]
    data_dict['date'] = data_dict['date'].strftime("%Y-%m-%d")
    data_dict['created_at'] = data_dict['created_at'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@sertifikasi.route('/delete-sertifikasi/<id>', methods=['GET'])
def delete_sertifikasi(id):
    try:
        data = db.collection('sertifikasi').document(id).get()
        data_dict = data.to_dict()

        storage_delete_file(data_dict['poster'])

        old_important_files = db.collection('sertifikasi').document(data.id).collection('file-penting').get()
        for doc in old_important_files:
            storage_delete_file(doc.to_dict()['url'])
            doc.reference.delete()

        db.collection('sertifikasi').document(id).delete()
        flash('Berhasil hapus sertifikasi', 'success')
        return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='sertifikasi', page='sertifikasi'))