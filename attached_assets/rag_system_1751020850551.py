import os
import logging
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) system for question answering
    Uses Groq for LLM and Google Gemini for embeddings
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Groq client for LLM
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Initialize Google Gemini embeddings
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Set environment variable for Google API key
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        self.llm = ChatGroq(model='llama3-70b-8192', api_key=groq_api_key)
        self.embedding_model = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
        
        self.document_store: Dict[str, FAISS] = {}  # session_id -> FAISS vectorstore
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300
        )
    
    def add_document(self, session_id: str, content: str, filename: str):
        """
        Add a document to the RAG system for a specific session
        
        Args:
            session_id: Session identifier
            content: Document text content
            filename: Original filename
        """
        try:
            # Split content into chunks for better retrieval
            chunks = self.text_splitter.split_text(content)
            
            if session_id not in self.document_store:
                # Create new FAISS vectorstore for this session
                vectorstore = FAISS.from_texts(chunks, self.embedding_model)
                self.document_store[session_id] = vectorstore
            else:
                # Add to existing vectorstore
                self.document_store[session_id].add_texts(chunks)
            
            self.logger.info(f"Added {len(chunks)} chunks from {filename} to session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding document to RAG system: {str(e)}")
            raise
    
    def ask_question(self, session_id: str, question: str) -> Optional[str]:
        """
        Ask a question and get an answer based on the documents
        
        Args:
            session_id: Session identifier
            question: User's question
            
        Returns:
            Answer string or None if no documents available
        """
        try:
            if session_id not in self.document_store:
                return None
            
            # Get relevant context from vector store
            vectorstore = self.document_store[session_id]
            relevant_docs = vectorstore.similarity_search(question, k=3)
            
            if not relevant_docs:
                return "I couldn't find relevant information in the uploaded documents to answer your question."
            
            # Create context from relevant documents
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Generate answer using Groq
            answer = self._generate_answer(question, context)
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error answering question: {str(e)}")
            return f"Error processing your question: {str(e)}"
    
    def get_documents(self, session_id: str) -> List[str]:
        """Get all document contents for a session"""
        if session_id not in self.document_store:
            return []
        
        try:
            # Get all documents from the vectorstore
            vectorstore = self.document_store[session_id]
            # Get all texts by doing a broad similarity search
            all_docs = vectorstore.similarity_search("", k=100)  # Get many docs
            
            # Extract unique content
            contents = list(set([doc.page_content for doc in all_docs]))
            return contents
            
        except Exception as e:
            self.logger.error(f"Error getting documents: {str(e)}")
            return []
    
    def summarize_text(self, text: str) -> str:
        """
        Generate a summary of the provided text
        
        Args:
            text: Text to summarize
            
        Returns:
            Summary text
        """
        try:
            # Limit text length to avoid token limits
            limited_text = text[:8000] if len(text) > 8000 else text
            
            prompt_template = PromptTemplate.from_template(
                """You are a summarizer. Please provide a comprehensive summary of the following text. 
                Focus on the main points, key findings, and important details:

                Text: {text}

                Summary:"""
            )
            
            chain = prompt_template | self.llm | StrOutputParser()
            summary = chain.invoke({"text": limited_text})
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def summarize_text_with_instruction(self, text: str, instruction: str) -> str:
        """
        Generate a summary with specific instructions
        
        Args:
            text: Text to summarize
            instruction: Specific instruction for summary style
            
        Returns:
            Summary text
        """
        try:
            # Limit text length to avoid token limits
            limited_text = text[:8000] if len(text) > 8000 else text
            
            prompt_template = PromptTemplate.from_template(
                """You are a summarizer. {instruction}

                Text: {text}

                Summary:"""
            )
            
            chain = prompt_template | self.llm | StrOutputParser()
            summary = chain.invoke({"text": limited_text, "instruction": instruction})
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary with instruction: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def clear_session(self, session_id: str):
        """Clear all documents for a session"""
        if session_id in self.document_store:
            del self.document_store[session_id]
            self.logger.info(f"Cleared session {session_id}")
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Groq with context"""
        try:
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""You are a helpful assistant. Use the context provided below to answer the question. 
                If the answer cannot be found in the context, say "I don't know."

                Context:
                {context}

                Question:
                {question}

                Answer:"""
            )
            
            chain = prompt_template | self.llm | StrOutputParser()
            answer = chain.invoke({"context": context, "question": question})
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {str(e)}")
            return '''Sorry for the inconvenience. Here at InsightGenie, we are using a free API. 
            And the rate limit is exceeded, please try again after a few minutes☺️'''