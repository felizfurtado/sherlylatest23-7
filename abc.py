import json
import re
from docx import Document

def process_docx_to_json(docx_path, output_json_path):
    # Load the Word document
    doc = Document(docx_path)
    
    # Initialize the blog data structure
    blog_data = {
        "id": "counter",
        "content": []
    }
    
    # Process each paragraph in the document
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        # Check for bold text (assuming first bold line is title)
        is_bold = any(run.bold for run in para.runs)
        
        # Check for italic text
        is_italic = any(run.italic for run in para.runs)
        
        # Check for underlined text (this is a simple approach)
        is_underlined = any(run.underline for run in para.runs)
        
        # Determine the content type based on formatting
        if is_bold and not blog_data["content"] and not any(item["type"] == "title" for item in blog_data["content"]):
            # First bold line is title
            blog_data["content"].append({"type": "title", "text": text})
        elif is_bold:
            # Subsequent bold lines are subheadings
            blog_data["content"].append({"type": "subhead", "text": text})
        elif is_italic:
            # Italic text goes to quotes
            blog_data["content"].append({"type": "quote", "text": text})
        elif is_underlined:
            # Underlined text goes to points
            blog_data["content"].append({"type": "point", "text": text})
        else:
            # Regular text goes to paragraphs
            blog_data["content"].append({"type": "p", "text": text})
    
    # Save to JSON file
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(blog_data, f, indent=2, ensure_ascii=False)

# Example usage
process_docx_to_json('Document1.docx', 'blog-details.json')