from flask import Flask, request, render_template
import os
import json
from docx import Document
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGES_FOLDER'] = 'static/images'
app.config['JSON_FOLDER'] = 'data'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)
os.makedirs(app.config['JSON_FOLDER'], exist_ok=True)

def get_next_json_filename():
    existing = [f for f in os.listdir(app.config['JSON_FOLDER']) if f.startswith('blog') and f.endswith('.json')]
    numbers = [int(f[4:-5]) for f in existing if f[4:-5].isdigit()]
    next_number = max(numbers) + 1 if numbers else 1
    return f"blog{next_number}.json"

def process_docx(docx_path):
    document = Document(docx_path)
    output = []
    title_extracted = False

    # Handle paragraphs first keeping their order
    for block in document.paragraphs:
        if block.runs:
            if not title_extracted:
                # First bold text will be title
                for run in block.runs:
                    if run.bold:
                        output.append({'title': run.text.strip()})
                        title_extracted = True
                        break
                continue  # Skip this paragraph after title is extracted

            # Check within paragraph
            added = False
            for run in block.runs:
                if run.bold:
                    output.append({'subhead': block.text.strip()})
                    added = True
                    break
                elif run.italic:
                    output.append({'quote': block.text.strip()})
                    added = True
                    break
            if not added and block.text.strip():
                output.append({'p': block.text.strip()})

    # Handle images in the order they appear (including inline)
    for rel in document.part._rels:
        rel = document.part._rels[rel]
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_name = f"{uuid.uuid4().hex}.png"
            image_path = os.path.join(app.config['IMAGES_FOLDER'], image_name)
            with open(image_path, 'wb') as img_file:
                img_file.write(image_data)
            # Image link relative to server root
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

            json_filename = get_next_json_filename()
            json_filepath = os.path.join(app.config['JSON_FOLDER'], json_filename)
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)

            return f"✅ Uploaded and processed!<br> JSON saved as <code>{json_filename}</code> in data folder."

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
