import logging
from deep_translator import GoogleTranslator
from typing import Optional

class TranslationService:
    """
    Translation service using Google Translator (free)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Language mappings (Google Translate language codes) - Extended support
        self.languages = {
            'Afrikaans': 'af', 'Albanian': 'sq', 'Amharic': 'am', 'Arabic': 'ar', 
            'Armenian': 'hy', 'Azerbaijani': 'az', 'Basque': 'eu', 'Belarusian': 'be', 
            'Bengali': 'bn', 'Bosnian': 'bs', 'Bulgarian': 'bg', 'Catalan': 'ca', 
            'Cebuano': 'ceb', 'Chichewa': 'ny', 'Chinese (simplified)': 'zh-CN', 
            'Chinese (traditional)': 'zh-TW', 'Corsican': 'co', 'Croatian': 'hr', 
            'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 
            'Esperanto': 'eo', 'Estonian': 'et', 'Filipino': 'tl', 'Finnish': 'fi', 
            'French': 'fr', 'Frisian': 'fy', 'Galician': 'gl', 'Georgian': 'ka', 
            'German': 'de', 'Greek': 'el', 'Gujarati': 'gu', 'Haitian creole': 'ht', 
            'Hausa': 'ha', 'Hawaiian': 'haw', 'Hebrew': 'iw', 'Hindi': 'hi', 
            'Hmong': 'hmn', 'Hungarian': 'hu', 'Icelandic': 'is', 'Igbo': 'ig', 
            'Indonesian': 'id', 'Irish': 'ga', 'Italian': 'it', 'Japanese': 'ja', 
            'Javanese': 'jw', 'Kannada': 'kn', 'Kazakh': 'kk', 'Khmer': 'km', 
            'Korean': 'ko', 'Kurdish (kurmanji)': 'ku', 'Kyrgyz': 'ky', 'Lao': 'lo', 
            'Latin': 'la', 'Latvian': 'lv', 'Lithuanian': 'lt', 'Luxembourgish': 'lb', 
            'Macedonian': 'mk', 'Malagasy': 'mg', 'Malay': 'ms', 'Malayalam': 'ml', 
            'Maltese': 'mt', 'Maori': 'mi', 'Marathi': 'mr', 'Mongolian': 'mn', 
            'Myanmar (burmese)': 'my', 'Nepali': 'ne', 'Norwegian': 'no', 'Pashto': 'ps', 
            'Persian': 'fa', 'Polish': 'pl', 'Portuguese': 'pt', 'Punjabi': 'pa', 
            'Romanian': 'ro', 'Russian': 'ru', 'Samoan': 'sm', 'Scots gaelic': 'gd', 
            'Serbian': 'sr', 'Sesotho': 'st', 'Shona': 'sn', 'Sindhi': 'sd', 
            'Sinhala': 'si', 'Slovak': 'sk', 'Slovenian': 'sl', 'Somali': 'so', 
            'Spanish': 'es', 'Sundanese': 'su', 'Swahili': 'sw', 'Swedish': 'sv', 
            'Tajik': 'tg', 'Tamil': 'ta', 'Telugu': 'te', 'Thai': 'th', 'Turkish': 'tr', 
            'Ukrainian': 'uk', 'Urdu': 'ur', 'Uzbek': 'uz', 'Vietnamese': 'vi', 
            'Welsh': 'cy', 'Xhosa': 'xh', 'Yiddish': 'yi', 'Yoruba': 'yo', 'Zulu': 'zu'
        }
    
    def translate(self, text: str, source_language: str, target_language: str) -> str:
        """
        Translate text from source to target language
        
        Args:
            text: Text to translate
            source_language: Source language name (e.g., 'English', 'Spanish')
            target_language: Target language name (e.g., 'French', 'German')
            
        Returns:
            Translated text
        """
        try:
            if not text or not text.strip():
                return "No text provided for translation"
            
            if source_language not in self.languages:
                return f"Unsupported source language: {source_language}"
            
            if target_language not in self.languages:
                return f"Unsupported target language: {target_language}"
            
            source_code = self.languages[source_language]
            target_code = self.languages[target_language]
            
            # Check if source and target are the same
            if source_code == target_code:
                return text
            
            # Use Google Translator (free)
            translator = GoogleTranslator(source=source_code, target=target_code)
            
            # Split long text into chunks if necessary
            max_length = 4000  # Google Translate API limit
            if len(text) <= max_length:
                translated_text = translator.translate(text)
            else:
                # Split text into sentences and translate in chunks
                sentences = text.split('. ')
                translated_chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) <= max_length:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            translated_chunks.append(translator.translate(current_chunk.strip()))
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    translated_chunks.append(translator.translate(current_chunk.strip()))
                
                translated_text = " ".join(translated_chunks)
            
            self.logger.info(f"Successfully translated text from {source_language} to {target_language}")
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            return f"Translation error: {str(e)}"
    
    def get_supported_languages(self) -> dict:
        """Get dictionary of supported language codes and names"""
        return self.languages.copy()
