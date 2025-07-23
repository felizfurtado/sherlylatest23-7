from flask import Flask, request, render_template, redirect, url_for
import os
import json
import uuid
from docx import Document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGES_FOLDER'] = 'static/images'
app.config['JSON_FOLDER'] = 'data'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)
os.makedirs(app.config['JSON_FOLDER'], exist_ok=True)

def process_docx(docx_path):
    document = Document(docx_path)
    output = []
    title_extracted = False

    for i, block in enumerate(document.paragraphs):
        if block.runs:
            # Check for title
            if not title_extracted:
                for run in block.runs:
                    if run.bold:
                        output.append({'title': run.text.strip()})
                        title_extracted = True
                        break
                continue  # Skip to next block after title

            # After title
            added = False
            for run in block.runs:
                if run.bold:
                    output.append({'subhead': block.text.strip()})
                    added = True
                    break
                elif run.italic:
                    output.append({'points': block.text.strip()})
                    added = True
                    break
            if not added and block.text.strip():
                output.append({'p': block.text.strip()})

    # Handling Images
    for rel in document.part._rels:
        rel = document.part._rels[rel]
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_name = f"{uuid.uuid4().hex}.png"
            image_path = os.path.join(app.config['IMAGES_FOLDER'], image_name)
            with open(image_path, 'wb') as img_file:
                img_file.write(image_data)
            output.append({'image': f"/{image_path.replace(os.sep, '/')}"})

    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['docx_file']
        if file and file.filename.endswith('.docx'):
            filename = f"{uuid.uuid4().hex}.docx"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            processed_data = process_docx(filepath)

            json_filename = f"{uuid.uuid4().hex}.json"
            json_filepath = os.path.join(app.config['JSON_FOLDER'], json_filename)
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)

            return f"Uploaded and processed! JSON saved at <code>{json_filepath}</code>"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
