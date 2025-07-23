from flask import Flask, request, render_template
import os
import json
from docx import Document
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGES_FOLDER'] = 'static/images'
app.config['JSON_FOLDER'] = 'data'
app.config['ALLBLOGS_FILE'] = os.path.join(app.config['JSON_FOLDER'], 'allblogs.json')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)
os.makedirs(app.config['JSON_FOLDER'], exist_ok=True)

# Ensure allblogs.json exists
if not os.path.exists(app.config['ALLBLOGS_FILE']):
    with open(app.config['ALLBLOGS_FILE'], 'w') as f:
        json.dump([], f)

def get_next_id():
    try:
        with open(app.config['ALLBLOGS_FILE'], 'r') as f:
            allblogs = json.load(f)
        if not allblogs:
            return 1
        return max(blog['id'] for blog in allblogs) + 1
    except:
        return 1

def get_next_json_filename():
    existing = [f for f in os.listdir(app.config['JSON_FOLDER']) if f.startswith('blog') and f.endswith('.json')]
    numbers = [int(f[4:-5]) for f in existing if f[4:-5].isdigit()]
    next_number = max(numbers) + 1 if numbers else 1
    return f"blog{next_number}.json"

def process_docx(docx_path):
    document = Document(docx_path)
    output = []
    
    for block in document.paragraphs:
        if block.runs:
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

def update_allblogs(blog_data, blog_filename):
    with open(app.config['ALLBLOGS_FILE'], 'r', encoding='utf-8') as f:
        allblogs = json.load(f)
    
    # Get the first image or use a default
    first_image = next((item['image'] for item in blog_data if 'image' in item), "/static/images/default.png")
    
    # Find the title in the content (first subhead or first paragraph)
    title = next((item['subhead'] for item in blog_data if 'subhead' in item), "Untitled Blog")
    
    allblogs.append({
        'id': get_next_id(),
        'title': title,
        'category': request.form['category'],
        'excerpt': request.form['excerpt'],
        'date': request.form['date'],
        'readTime': request.form['read_time'],
        'image': first_image,
        'link': blog_filename
    })
    
    with open(app.config['ALLBLOGS_FILE'], 'w', encoding='utf-8') as f:
        json.dump(allblogs, f, indent=4, ensure_ascii=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Process the DOCX file
        file = request.files['docx_file']
        if file and file.filename.endswith('.docx'):
            filename = f"{uuid.uuid4().hex}.docx"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process the content (original structure)
            processed_content = process_docx(filepath)
            
            # Save the blog JSON (original structure)
            json_filename = get_next_json_filename()
            json_filepath = os.path.join(app.config['JSON_FOLDER'], json_filename)
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(processed_content, f, indent=4, ensure_ascii=False)

            # Update allblogs.json with the additional fields from the form
            update_allblogs(processed_content, json_filename)

            return f"✅ Uploaded and processed!<br> JSON saved as <code>{json_filename}</code> and added to allblogs.json."

    # For GET request, pass current date to template
    current_date = datetime.now().strftime("%B %d, %Y")
    return render_template('index.html', current_date=current_date)

if __name__ == '__main__':
    app.run(debug=True)