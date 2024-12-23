from flask import Flask, request, jsonify, send_file, render_template 
import boto3 
import xml.etree.ElementTree as ET 
from io import BytesIO
import os
import json
import csv

# AWS S3 Configuration
AWS_S3_BUCKET = 'xmlcsv'
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 
AWS_SECRET_KEY = 

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Frontend form for upload and download

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not file.filename.endswith('.xml'):
        return jsonify({'error': 'Only XML files are allowed'}), 400

    # Upload XML to S3
    try:
        s3_client.upload_fileobj(file, AWS_S3_BUCKET, file.filename)
        return jsonify({'message': 'File uploaded successfully!', 'filename': file.filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_file():
        filename = request.json.get('filename')
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

    # Download XML from S3
        try:
            xml_file = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=filename)['Body'].read()
            xml_file = xml_file.decode('utf-8')
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Convert XML to CSV
        try:
            root = ET.fromstring(xml_file)
            csv_data = BytesIO()
            csv_writer = csv.writer(csv_data)

        # Assuming XML has simple structure; modify according to your schema
            header = [elem.tag for elem in root[0]]
            csv_writer.writerow(header)
            for child in root:
                csv_writer.writerow([elem.text for elem in child])

            csv_data.seek(0)

        # Upload CSV to S3
            csv_filename = filename.replace('.xml', '.csv')
            s3_client.upload_fileobj(csv_data, AWS_S3_BUCKET, csv_filename)
            return jsonify({'message': 'File processed successfully!', 'csv_filename': csv_filename})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET']) 
def download_file(filename):
    try:
        csv_file = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=filename)['Body'].read()
        return send_file(BytesIO(csv_file), as_attachment=True, download_name=filename, mimetype='text/csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
