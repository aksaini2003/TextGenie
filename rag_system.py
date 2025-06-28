import os
import logging
from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv 
load_dotenv()
class RAGSystem:
    """
    RAG (Retrieval-Augmented Generation) system for question answering
    Uses Groq for LLM and Google Gemini for embeddings
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Groq client for LLM
        groq_api_key = os.environ['GROQ_API_KEY']
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Initialize Google Gemini embeddings
        gemini_api_key = os.environ['GOOGLE_API_KEY']
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Set environment variable for Google API key
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        try:
            self.llm = ChatGroq(model='llama3-70b-8192', api_key=groq_api_key)
            self.embedding_model = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
            self.logger.info("Successfully initialized RAG system with Groq and Google Gemini")
        except Exception as e:
            self.logger.error(f"Error initializing RAG system: {str(e)}")
            raise
        
        self.document_store: Dict[str, FAISS] = {}  # session_id -> FAISS vectorstore
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
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
            if not content or not content.strip():
                self.logger.warning(f"Empty content for document: {filename}")
                return
            
            # Split content into chunks for better retrieval
            chunks = self.text_splitter.split_text(content)
            
            if not chunks:
                self.logger.warning(f"No chunks created from document: {filename}")
                return
            
            # Add metadata to chunks
            metadatas = [{"source": filename, "chunk_id": i} for i in range(len(chunks))]
            
            if session_id not in self.document_store:
                # Create new FAISS vectorstore for this session
                vectorstore = FAISS.from_texts(chunks, self.embedding_model, metadatas=metadatas)
                self.document_store[session_id] = vectorstore
                self.logger.info(f"Created new vectorstore for session {session_id}")
            else:
                # Add to existing vectorstore
                self.document_store[session_id].add_texts(chunks, metadatas=metadatas)
                self.logger.info(f"Added to existing vectorstore for session {session_id}")
            
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
                self.logger.warning(f"No documents found for session {session_id}")
                return None
            
            # Get relevant context from vector store
            vectorstore = self.document_store[session_id]
            
            try:
                relevant_docs = vectorstore.similarity_search(question, k=4)
            except Exception as e:
                self.logger.error(f"Error in similarity search: {str(e)}")
                return "Error searching through documents. Please try again."
            
            if not relevant_docs:
                return "I couldn't find relevant information in the uploaded documents to answer your question."
            
            # Create context from relevant documents
            context_parts = []
            for doc in relevant_docs:
                source = doc.metadata.get('source', 'Unknown')
                content = doc.page_content
                context_parts.append(f"From {source}: {content}")
            
            context = "\n\n".join(context_parts)
            
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
            all_docs = vectorstore.similarity_search("", k=200)  # Get many docs
            
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
            limited_text = text[:12000] if len(text) > 12000 else text
            
            prompt_template = PromptTemplate.from_template(
                """You are a professional summarizer. Please provide a comprehensive summary of the following text. 

                **Formatting guidelines:**
                - Structure your summary with clear paragraphs
                - Use bullet points (•) for key highlights  
                - Use **bold text** for important concepts
                - Use proper line breaks between topics
                - Keep the summary well-organized and easy to read

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
            limited_text = text[:12000] if len(text) > 12000 else text
            
            prompt_template = PromptTemplate.from_template(
                """You are a professional summarizer. {instruction}

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
                template="""You are a helpful assistant. Use the context provided below to answer the question accurately and comprehensively. 

                **Important formatting guidelines:**
                - Structure your response with clear paragraphs
                - Use bullet points (•) for lists when appropriate
                - Use numbered lists (1., 2., 3.) for sequential information
                - Use **bold text** for important terms or concepts
                - Use proper line breaks between different topics
                - Keep paragraphs concise and well-organized
                
                If the answer cannot be found in the context, say "I don't have enough information in the provided documents to answer this question."

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
            return '''Sorry for the inconvenience. We are currently experiencing high demand on our AI services. 
            Please try again in a few moments. If the issue persists, our rate limits may have been exceeded.'''
