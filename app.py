import os
import logging
from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid
import json
from document_processor import DocumentProcessor
from rag_system import RAGSystem
from translation_service import TranslationService
from dotenv import load_dotenv
load_dotenv() 

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fgfsafasfas")
# only for the replit
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure CORS
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
VECTOR_STORE_FOLDER = 'vector_store'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTOR_STORE_FOLDER, exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Initialize services
document_processor = DocumentProcessor()
rag_system = RAGSystem()
translation_service = TranslationService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        session_id = get_session_id()
        logging.info(f"Upload files - Session ID: {session_id}")
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files selected'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        uploaded_files = []
        success_count = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            # Check file extension
            if not allowed_file(file.filename):
                uploaded_files.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': f'File type not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
                })
                continue
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                uploaded_files.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
                })
                continue
            
            if file_size == 0:
                uploaded_files.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': 'File is empty'
                })
                continue
            
            try:
                # Secure filename and add session ID
                filename = secure_filename(file.filename)
                # Ensure unique filename to prevent conflicts
                import time
                timestamp = str(int(time.time() * 1000))
                filename = f"{session_id}_{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save file
                file.save(filepath)
                logging.info(f"File saved: {filepath}")
                
                # Process the document
                content = document_processor.process_document(filepath)
                
                if content and content.strip():
                    # Add to RAG system with original filename for user reference
                    rag_system.add_document(session_id, content, file.filename)
                    uploaded_files.append({
                        'filename': file.filename,
                        'size': file_size,
                        'status': 'processed',
                        'message': f'Successfully processed - {len(content.split())} words extracted'
                    })
                    success_count += 1
                    logging.info(f"Successfully processed: {file.filename} - Content length: {len(content)}")
                else:
                    uploaded_files.append({
                        'filename': file.filename,
                        'status': 'error',
                        'message': 'Could not extract text content. File may be corrupted, password-protected, or unsupported format.'
                    })
                    # Clean up failed file
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        
            except Exception as e:
                error_msg = str(e)
                # Provide more specific error messages
                if "corrupted" in error_msg.lower() or "invalid" in error_msg.lower():
                    error_msg = "File appears to be corrupted or in an unsupported format"
                elif "permission" in error_msg.lower():
                    error_msg = "Permission denied accessing the file"
                elif "memory" in error_msg.lower():
                    error_msg = "File too large to process in memory"
                
                logging.error(f"Error processing file {file.filename}: {str(e)}")
                uploaded_files.append({
                    'filename': file.filename,
                    'status': 'error',
                    'message': f'Processing error: {error_msg}'
                })
                # Clean up failed file
                if 'filepath' in locals() and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass  # Ignore cleanup errors
        
        # Prepare response
        response_message = f'Successfully processed {success_count} out of {len(files)} files'
        if success_count == 0:
            response_message = 'No files were successfully processed'
        
        return jsonify({
            'message': response_message,
            'files': uploaded_files,
            'success_count': success_count,
            'total_count': len(files)
        })
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        session_id = get_session_id()
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Debug session information
        logging.info(f"Ask question - Session ID: {session_id}")
        logging.info(f"Available sessions in RAG system: {list(rag_system.document_store.keys())}")
        
        # Get answer from RAG system
        answer = rag_system.ask_question(session_id, question)
        
        if not answer:
            return jsonify({'error': 'No documents found. Please upload documents first.'}), 400
        
        # Store in session history
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({
            'question': question,
            'answer': answer,
            'timestamp': str(uuid.uuid4())  # Simple timestamp replacement
        })
        
        return jsonify({
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        logging.error(f"Question answering error: {str(e)}")
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/summarize', methods=['POST'])
def summarize_documents():
    try:
        session_id = get_session_id()
        
        # Get all documents for this session
        documents = rag_system.get_documents(session_id)
        
        if not documents:
            return jsonify({'error': 'No documents found. Please upload documents first.'}), 400
        
        # Combine all document content
        combined_content = "\n\n".join(documents)
        
        # Generate summary
        summary = rag_system.summarize_text(combined_content)
        
        return jsonify({
            'summary': summary,
            'document_count': len(documents)
        })
        
    except Exception as e:
        logging.error(f"Summarization error: {str(e)}")
        return jsonify({'error': f'Error generating summary: {str(e)}'}), 500

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_language = data.get('source_language', 'English')
        target_language = data.get('target_language', 'Spanish')
        
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        # Translate text
        translated_text = translation_service.translate(text, source_language, target_language)
        
        return jsonify({
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })
        
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        return jsonify({'error': f'Error translating text: {str(e)}'}), 500

@app.route('/summarize_text', methods=['POST'])
def summarize_text_input():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        summary_size = data.get('summary_size', 'Medium (1 paragraph)')
        
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        word_count = len(text.split())
        max_words = 8000
        
        if word_count > max_words:
            return jsonify({'error': f'Text exceeds {max_words} word limit. Currently: {word_count} words.'}), 400
        
        # Create prompt based on summary size
        size_prompts = {
            "Short (1-2 lines)": "Write a very short 1-2 line summary.",
            "Medium (1 paragraph)": "Write a concise summary in one paragraph.",
            "Detailed (multi-paragraph)": "Write a detailed multi-paragraph summary covering all important points."
        }
        
        prompt_instruction = size_prompts.get(summary_size, size_prompts["Medium (1 paragraph)"])
        
        # Generate summary using RAG system
        summary = rag_system.summarize_text_with_instruction(text, prompt_instruction)
        
        return jsonify({
            'summary': summary,
            'word_count': word_count,
            'summary_size': summary_size
        })
        
    except Exception as e:
        logging.error(f"Text summarization error: {str(e)}")
        return jsonify({'error': f'Error summarizing text: {str(e)}'}), 500

@app.route('/get_languages', methods=['GET'])
def get_languages():
    try:
        languages = translation_service.get_supported_languages()
        return jsonify({'languages': list(languages.keys())})
    except Exception as e:
        logging.error(f"Get languages error: {str(e)}")
        return jsonify({'error': f'Error getting languages: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        session_id = get_session_id()
        
        # Clear chat history
        session['chat_history'] = []
        
        # Clear RAG system data for this session
        rag_system.clear_session(session_id)
        
        # Clean up uploaded files
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.startswith(session_id):
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    logging.warning(f"Could not remove file {filename}: {e}")
        
        return jsonify({'message': 'History cleared successfully'})
        
    except Exception as e:
        logging.error(f"Clear history error: {str(e)}")
        return jsonify({'error': f'Error clearing history: {str(e)}'}), 500

@app.route('/get_chat_history')
def get_chat_history():
    return jsonify({
        'history': session.get('chat_history', [])
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
