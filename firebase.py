import os
import tempfile
import pyrebase
import uuid

from firebase_admin import credentials, firestore, initialize_app, storage

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
initialize_app(cred, {
    'storageBucket': 'temanesia-6feb4.appspot.com'
})

db = firestore.client()
bucket = storage.bucket()


def storage_upload(the_file, destination_folder):
    
    temp = tempfile.NamedTemporaryFile(delete=False)
    the_file.save(temp.name)

    unique_filename = str(uuid.uuid4()) + '.' + the_file.filename.split('.')[-1]

    blob = bucket.blob(f'{destination_folder}/{unique_filename}')
    blob.upload_from_filename(temp.name)
    blob.make_public()

    os.remove(temp.name)

    return blob.public_url


def storage_multiple_upload(multiple_files, destination_folder):

    results = []

    for important_file in multiple_files:
        results.append(
            {
                'nama_file': important_file.filename,
                'url': storage_upload(important_file, destination_folder)
            }
        )

    return results


def storage_delete_file(public_url):
    bucket.blob(public_url.replace('https://storage.googleapis.com/temanesia-6feb4.appspot.com/', '')).delete()