import httpx
from app.config import settings
from gtts import gTTS
import uuid
from pathlib import Path
import re

class AISummarizer:
    def __init__(self):
        self.hf_api_key = settings.huggingface_api_key
        self.gemini_api_key = settings.gemini_api_key
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
    
    def clean_content(self, text: str) -> str:
        """Remove truncation markers and clean text"""
        if not text:
            return ""
        text = re.sub(r'\[\+\d+ chars\]', '', text)
        text = re.sub(r'\.{3,}', '.', text)
        return text.strip()
    
    async def fetch_article_content(self, url: str) -> str:
        """Fetch full article from URL"""
        try:
            print(f"🌐 Fetching: {url[:60]}...")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0, follow_redirects=True, headers=headers)
                
                if response.status_code == 200:
                    html = response.text
                    # Remove noise
                    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
                    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL | re.IGNORECASE)
                    text = re.sub(r'<[^>]+>', ' ', html)
                    text = ' '.join(text.split())
                    print(f"✅ Extracted {len(text[:5000])} chars")
                    return text[:5000]
                    
        except Exception as e:
            print(f"❌ Fetch error: {e}")
        return ""
    
    def create_intelligent_summary(self, title: str, description: str, content: str, web_content: str, language: str) -> str:
        """Create smart summary without AI APIs"""
        print("🧠 Creating intelligent summary...")
        
        # Combine all text
        all_text = f"{title}. {description}. {content}. {web_content}"
        
        # Split into sentences
        sentences = []
        for sent in re.split(r'[।\.\!]', all_text):
            clean = sent.strip()
            # Keep sentences that are substantial (50+ chars) and meaningful
            if len(clean) > 50 and not any(skip in clean.lower() for skip in ['cookie', 'subscribe', 'advertisement', 'terms of service']):
                sentences.append(clean)
        
        # Remove duplicates while preserving order
        unique_sentences = []
        seen = set()
        
        for sent in sentences:
            # Normalize for comparison
            normalized = sent.lower().strip()
            if normalized not in seen and len(normalized) > 50:
                unique_sentences.append(sent)
                seen.add(normalized)
                if len(unique_sentences) >= 6:
                    break
        
        if unique_sentences:
            # Ensure proper ending
            summary = '. '.join(unique_sentences)
            if not summary.endswith('.'):
                summary += '.'
            print(f"✅ Created summary: {len(summary)} chars")
            return summary
        else:
            # Last resort
            return f"{title}. {description}"
    
    async def generate_summary(self, title: str, description: str, content: str, url: str, language: str = "en") -> str:
        """Generate comprehensive summary - WORKS WITHOUT API KEYS"""
        print(f"\n{'='*60}")
        print(f"🤖 Generating Summary")
        print(f"Language: {language}")
        print(f"{'='*60}\n")
        
        # Clean inputs
        title = self.clean_content(title)
        description = self.clean_content(description)
        content = self.clean_content(content)
        
        print(f"📝 Input - Title: {len(title)}, Desc: {len(description)}, Content: {len(content)}")
        
        # Fetch full article content
        web_content = ""
        if url:
            web_content = await self.fetch_article_content(url)
        
        # Try Gemini if key exists
        if self.gemini_api_key:
            try:
                summary = await self.try_gemini(title, description, content, web_content, language)
                if summary and len(summary) > 150:
                    print(f"✅ Using Gemini summary: {len(summary)} chars\n")
                    return summary
            except Exception as e:
                print(f"⚠️ Gemini failed: {e}")
        
        # Try HuggingFace if key exists (English only)
        if self.hf_api_key and language == "en":
            try:
                summary = await self.try_huggingface(title, description, content)
                if summary and len(summary) > 100:
                    print(f"✅ Using HuggingFace summary: {len(summary)} chars\n")
                    return summary
            except Exception as e:
                print(f"⚠️ HuggingFace failed: {e}")
        
        # Intelligent fallback (ALWAYS WORKS)
        print("💡 Using intelligent extraction (no AI needed)")
        summary = self.create_intelligent_summary(title, description, content, web_content, language)
        print()
        return summary
    
    async def try_gemini(self, title: str, description: str, content: str, web_content: str, language: str) -> str:
        """Try Gemini API"""
        try:
            # Try multiple model endpoints
            model_endpoints = [
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            ]
            
            combined = f"Title: {title}\n\nDescription: {description}\n\nContent: {web_content[:3000]}"
            
            if language == "hi":
                prompt = f"इस समाचार का 5-6 वाक्यों में पूर्ण सारांश दें:\n\n{combined}"
            else:
                prompt = f"Write a complete 5-6 sentence summary:\n\n{combined}"
            
            async with httpx.AsyncClient() as client:
                for endpoint in model_endpoints:
                    try:
                        response = await client.post(
                            f"{endpoint}?key={self.gemini_api_key}",
                            json={
                                "contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}
                            },
                            timeout=20.0
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            summary = result["candidates"][0]["content"]["parts"][0]["text"]
                            if len(summary) > 100:
                                return summary.strip()
                    except:
                        continue
        except:
            pass
        return None
    
    async def try_huggingface(self, title: str, description: str, content: str) -> str:
        """Try HuggingFace API"""
        try:
            API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            text = f"{title}. {description}. {content}"[:1000]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    API_URL,
                    headers=headers,
                    json={"inputs": text, "parameters": {"max_length": 200, "min_length": 100}},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and result:
                        return result[0].get("summary_text", "")
        except:
            pass
        return None
    
    def generate_audio_summary(self, summary: str, language: str = "en") -> str:
        """Generate audio from summary"""
        try:
            if not summary or len(summary) < 20:
                return None
            
            lang_code = "hi" if language == "hi" else "en"
            filename = f"{uuid.uuid4()}.mp3"
            filepath = self.audio_dir / filename
            
            tts = gTTS(text=summary, lang=lang_code, slow=False)
            tts.save(str(filepath))
            print(f"🔊 Audio saved: {filename}")
            return f"/static/audio/{filename}"
            
        except Exception as e:
            print(f"Audio error: {e}")
            return None

ai_summarizer = AISummarizer()