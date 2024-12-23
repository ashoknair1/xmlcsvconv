import os
import boto3
from flask import Flask, request, jsonify, render_template
import pandas as pd
from xml.etree import ElementTree as ET
from werkzeug.utils import secure_filename

# AWS S3 Configuration
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')

app = Flask(__name__)

# Configure S3
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)
S3_BUCKET = 'xmlcsv'  # Replace with your bucket name

# Configure file upload
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'xml'}

# Ensure uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def xml_to_csv(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Parse XML and convert to a list of dicts
    data = []
    for elem in root.findall('.//record'):  # Modify this path based on XML structure
        record = {}
        for sub_elem in elem:
            record[sub_elem.tag] = sub_elem.text
        data.append(record)

    # Convert list of dicts to DataFrame and save as CSV
    df = pd.DataFrame(data)
    csv_file_path = xml_file_path.replace('.xml', '.csv')
    df.to_csv(csv_file_path, index=False)

    return csv_file_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Convert XML to CSV
        csv_file_path = xml_to_csv(file_path)

        # Upload CSV to S3
        csv_filename = filename.replace('.xml', '.csv')
        s3_client.upload_file(csv_file_path, S3_BUCKET, csv_filename)

        # Generate the S3 URL for download
        download_url = f'https://{S3_BUCKET}.s3.amazonaws.com/{csv_filename}'

        return jsonify({'success': True, 'downloadUrl': download_url})

    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)