import json

from requests.exceptions import HTTPError
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from firebase import db, storage_delete_file


verification = Blueprint('verification', __name__)

@verification.route('/edit-status', methods=['POST'])
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


@verification.route('/get-user/<id>', methods=['GET'])
def get_user(id):
    data = db.collection('users_website').document(id).get()
    data_dict = data.to_dict()
    data_dict['tanggal_daftar'] = data_dict['tanggal_daftar'].strftime("%Y-%m-%d")

    return jsonify(data_dict)


@verification.route('/delete-user/<id>', methods=['GET'])
def delete_user(id):
    try:
        data = db.collection('users_website').document(id).get()
        data_dict = data.to_dict()

        storage_delete_file(data_dict['logo'])
    
        db.collection('users_website').document(id).delete()
        flash('Berhasil hapus pengguna', 'success')
        return redirect(url_for('dashboard', role='admin', page='verification'))
    
    except HTTPError as e:
        flash(json.loads(e.strerror)['error']['message'], 'error')
        return redirect(url_for('dashboard', role='admin', page='verification'))