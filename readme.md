# InsightGenie - Document Intelligence Platform

## Overview

InsightGenie is a Flask-based document intelligence platform that combines document processing, question answering, summarization, and translation capabilities. The application leverages modern AI technologies including Groq's Llama models and Google Gemini embeddings to provide intelligent responses to user queries about uploaded documents.

## System Architecture

The application follows a modular Flask architecture with clear separation of concerns:

- **Frontend**: Modern web interface using HTML, CSS, and JavaScript with Bootstrap 5
- **Backend**: Flask web application with modular service components
- **AI Services**: Integration with Groq LLM and Google Gemini embeddings
- **Document Processing**: Multi-format document parsing and text extraction
- **Vector Storage**: FAISS-based vector database for document embeddings
- **Session Management**: Flask session-based user state management

## Key Components

### Backend Services

1. **Flask Application (`app.py`)**
   - Main web server handling HTTP requests and routing
   - Session management with UUID-based session IDs
   - File upload handling with security validation
   - CORS configuration for cross-origin requests
   - ProxyFix middleware for deployment compatibility

2. **Document Processor (`document_processor.py`)**
   - Supports TXT, PDF, and DOCX file formats
   - Uses PyPDF2 for PDF text extraction
   - Uses python-docx for DOCX document processing
   - Implements robust error handling and encoding detection
   - File size validation (200MB max)

3. **RAG System (`rag_system.py`)**
   - Retrieval-Augmented Generation using LangChain
   - Groq Llama3-70b-8192 model for text generation
   - Google Gemini embedding-001 for document embeddings
   - FAISS vector database for similarity search
   - Session-based document storage
   - RecursiveCharacterTextSplitter for document chunking (1500 chars with 300 overlap)

4. **Translation Service (`translation_service.py`)**
   - Free Google Translator integration via deep-translator
   - Support for 80+ languages
   - Language code mapping for user-friendly interface
   - Error handling for translation failures

### Frontend Components

1. **Modern Web Interface**
   - Responsive Bootstrap 5 design
   - Professional gradient styling and animations
   - Drag-and-drop file upload with progress indicators
   - Real-time chat interface for Q&A
   - Multi-tab interface for different features

2. **JavaScript Application (`static/js/main.js`)**
   - Class-based architecture for maintainability
   - Event-driven interactions
   - File upload handling with validation
   - Real-time updates and progress tracking
   - Smooth scrolling and UI animations

## Data Flow

1. **Document Upload**: Users upload documents via drag-and-drop or file picker
2. **Text Extraction**: DocumentProcessor extracts text from various file formats
3. **Embedding Generation**: RAGSystem creates embeddings using Google Gemini
4. **Vector Storage**: Documents stored in session-specific FAISS indexes
5. **Query Processing**: User questions trigger similarity search and LLM generation
6. **Response Generation**: Groq Llama model generates contextual responses

## External Dependencies

### AI Services
- **Groq API**: LLM services using Llama3-70b-8192 model
- **Google Gemini API**: Embedding generation using embedding-001 model
- **Google Translator**: Free translation services via deep-translator

### Key Libraries
- **Flask**: Web framework with CORS support
- **LangChain**: RAG implementation and text processing
- **FAISS**: Vector similarity search
- **PyPDF2**: PDF document processing
- **python-docx**: DOCX document processing
- **Bootstrap 5**: Frontend styling framework

### Environment Variables Required
- `GROQ_API_KEY`: API key for Groq LLM services
- `GEMINI_API_KEY`: API key for Google Gemini embeddings
- `SESSION_SECRET`: Flask session encryption key (optional, defaults to placeholder)

## Deployment Strategy

- **Replit Platform**: Configured for autoscale deployment
- **Gunicorn WSGI Server**: Production-ready server with reload capability
- **Nix Package Management**: Stable channel with PostgreSQL support
- **Port Configuration**: Application runs on port 5000
- **Static Assets**: Served directly by Flask in development

The deployment uses Gunicorn with bind configuration for 0.0.0.0:5000, enabling external access. The .replit configuration supports both development and production workflows with automatic reloading during development.

## Changelog

```
Changelog:
- June 27, 2025. Initial setup
- June 27, 2025. Enhanced multi-file processing with improved error handling
- June 27, 2025. Implemented professional UI design with advanced navigation bar
- June 27, 2025. Added comprehensive upload feedback system
- June 27, 2025. Enhanced chat interface with smooth animations
- June 27, 2025. Improved document processing reliability for PDF, DOCX, and TXT files
- June 27, 2025. Fixed file persistence - uploaded documents now remain visible across multiple uploads
- June 27, 2025. Improved loading spinner to show only in working area, not full page
- June 27, 2025. Enhanced LLM response formatting with proper header handling and bullet point structure
- June 27, 2025. Added duplicate file prevention and better visual feedback for uploads
- June 27, 2025. Fixed UI scattering issues with robust scroll handling and layout stability
- June 27, 2025. Made application fully responsive for mobile, tablet, and desktop devices
- June 27, 2025. Enhanced visual design with advanced animations, gradients, and interactive elements
- June 27, 2025. Added sticky navigation, scroll indicators, and improved accessibility features
- June 27, 2025. Optimized performance with GPU acceleration and layout containment
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```