from flask import Flask, request, jsonify
import io
import zipfile
import re

from app import mongo,spellchecker
from models.question import Question

db = mongo.db

def perform_spell_correction(text):
    corrected_text = []
    words = text.split()
    for word in words:
        corrected_word = spellchecker.correction(word)
        corrected_text.append(corrected_word)
    spell_corr = list(filter(None, corrected_text))
    return ' '.join(spell_corr)


class UploadController:

    @staticmethod
    def upload():
        file = request.files.get('file')
        file_stream = io.BytesIO(file.stream.read())
        with zipfile.ZipFile(file_stream, 'r') as zip_file:
            student_ids = set()
            for file_name in zip_file.namelist():
                if '/' in file_name:
                    folder_names = file_name.split('/', 1)[0]
                    folder_names = folder_names.replace('.', '').replace(' ', '')
                    if folder_names.startswith('Q'):
                        student_id = file_name.split('/')[1].split()[0]
                        name_parts = file_name.split("-")
                        if len(name_parts) >= 3:
                            student_name = name_parts[2].strip()
                        if student_id != 'Question' and 'Attempt1_textresponse' in file_name:
                            student_ids.add(student_id)
                            text_response = zip_file.read(file_name).decode('utf-8')
                            text_response = text_response.lower()
                            if 'any text entered here will be displayed in the response input box when a new attempt ' \
                               'at the question starts.' in text_response:
                                text_response = text_response.replace('any text entered here will be displayed in the '
                                                                      'response input box when a new attempt at the '
                                                                      'question starts.', '')
                                text_response = text_response.strip()
                                if text_response == '':
                                    text_response = 'null'
                            if "'s" in text_response:
                                text_response = text_response.replace("'s", '')
                            if "don't" in text_response:
                                text_response = text_response.replace("don't", 'do not')
                            text_response = re.sub(r'[^a-zA-Z0-9 ]', ' ', text_response)
                            text_response = perform_spell_correction(text_response)
                            question = Question(course_id=3, question=folder_names, student_name=student_name,
                                                student_id=student_id, answer=text_response)
                            question_dict = question.to_dict()
                            db.Question.insert_one(question_dict)
                    else:
                        return jsonify({'message': 'Invalid format'}), 400
            all_questions = db.Question.distinct('question')
            for question in all_questions:
                for student_id in student_ids:
                    query = {
                        'question': question,
                        'student_id': student_id
                    }
                    if db.Question.count_documents(query) == 0:
                        question_data = {
                            'course_id': 3,
                            'question': question,
                            'student_name': 'null',
                            'student_id': student_id,
                            'answer': 'null'
                        }
                        db.Question.insert_one(question_data)
        return jsonify({'message': 'Upload successful'}), 200