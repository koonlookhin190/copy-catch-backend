from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import io
import zipfile

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

client = MongoClient('localhost', 27017)

db = client.flask_db
todos = db.todos

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if file and file.content_type == 'application/x-zip-compressed':
        file_stream = io.BytesIO(file.stream.read())

        with zipfile.ZipFile(file_stream, 'r') as zip_file:
            folder_names = []
            for file_name in zip_file.namelist():
                if '/' in file_name:
                    folder_name = file_name.split('/', 1)[0]
                    if folder_name.startswith('Q'):
                        folder_names.append(folder_name)
                    else:
                        folder_names.clear()
                        return 'This file is not in the right format'
        folder_names = list(set(folder_names))
        print(folder_names)
        return jsonify(folder_names)
    else:
        return 'Invalid file type. Only x-zip-compressed files are allowed.'


if __name__ == '__main__':
    app.run(debug=True)
