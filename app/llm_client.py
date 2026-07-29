"""
Client LLM per Pulse.
Supporta Gemini, Cerebras e Groq con fallback automatico.
"""

from app.config import get_settings
import json
import re
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Import condizionale per i provider
OPENAI_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    pass


class LLMClient:
    """Client LLM con fallback multi-provider."""

    def __init__(self):
        settings = get_settings()
        self.gemini_key = settings.gemini_api_key
        self.cerebras_key = settings.cerebras_api_key
        self.groq_key = settings.groq_api_key
        self._client = None
        self._provider = None
        self._init_client()

    def _init_client(self):
        """Inizializza il client con il primo provider disponibile."""
        # Priorita: Groq > Gemini > Cerebras
        if self.groq_key and OPENAI_AVAILABLE:
            self._client = openai.OpenAI(
                api_key=self.groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self._provider = "groq"
            print("  [LLM] Groq attivo")
        elif self.gemini_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_key)
            self._provider = "gemini"
            print("  [LLM] Gemini attivo")
        elif self.cerebras_key and OPENAI_AVAILABLE:
            self._client = openai.OpenAI(
                api_key=self.cerebras_key,
                base_url="https://api.cerebras.ai/v1"
            )
            self._provider = "cerebras"
            print("  [LLM] Cerebras attivo")
        else:
            print("  [!] Nessun LLM provider disponibile - usando mock")
            self._provider = "mock"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Chiama il LLM con retry automatico."""
        if self._provider == "mock":
            return self._mock_response(prompt)

        if self._provider == "gemini":
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.3,
                )
            )
            return response.text

        # Cerebras / Groq (OpenAI-compatible)
        if self._provider == "cerebras":
            model_name = "llama-3.3-70b"
        else:
            model_name = "llama-3.1-8b-instant"

        response = self._client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _mock_response(self, prompt: str) -> str:
        """Risposta mock quando nessun provider e disponibile."""
        if "score" in prompt.lower():
            return "7"
        if "why" in prompt.lower() or "matters" in prompt.lower():
            return "Questa notizia e rilevante per il settore in quanto rappresenta un aggiornamento significativo."
        if "summary" in prompt.lower():
            return "Riassunto non disponibile - articolo troppo breve o senza contenuto estratto."
        return "Risposta mock"

    def score_relevance(self, title: str, summary: str, field: str) -> int:
        """Score da 1-10 della rilevanza di un articolo per il campo."""
        prompt = f"""Valuta la rilevanza di questo articolo per il campo '{field}'.

Titolo: {title}
Riassunto: {summary or "Nessun riassunto disponibile"}

Restituisci SOLO un numero da 1 a 10, dove:
- 1-3: poco rilevante
- 4-6: moderatamente rilevante  
- 7-8: molto rilevante
- 9-10: estremamente rilevante / breaking news

Score:"""
        try:
            response = self._call_llm(prompt, max_tokens=10)
            match = re.search(r'(\d+)', response)
            if match:
                score = int(match.group(1))
                return max(1, min(10, score))
            return 5
        except Exception as e:
            print(f"    [!] Errore scoring: {e}")
            return 5

    def summarize_and_explain(self, title: str, text: str, field: str) -> dict:
        """Genera summary e why_matters in un'unica chiamata."""
        prompt = f"""Analizza questo articolo di {field} e restituisci un JSON con due campi.

Titolo: {title}
Testo: {text[:4000]}

Restituisci SOLO un oggetto JSON valido con questa struttura esatta:
{{
  "summary": "riassunto conciso in 2-3 frasi (max 200 parole)",
  "why_matters": "spiegazione di perche e rilevante in 2-3 frasi (max 200 parole)"
}}

Il JSON deve essere valido e non contenere altro testo."""

        try:
            response = self._call_llm(prompt, max_tokens=800)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "summary": data.get("summary", "").strip() or "Riassunto non generato.",
                    "why_matters": data.get("why_matters", "").strip() or "Rilevanza non analizzata."
                }
        except Exception as e:
            print(f"    [!] Errore summarization: {e}")

        fallback_summary = (text[:300] + "...") if text and len(text) > 50 else "Riassunto non disponibile."
        return {
            "summary": fallback_summary,
            "why_matters": f"Articolo rilevante per il settore {field}."
        }

    def explain_briefing(self, title: str, summary: str) -> str:
        """Genera una spiegazione semplificata del briefing."""
        prompt = f"""Spiega in modo semplice e accessibile questo articolo.

Titolo: {title}
Contenuto: {summary or title}

Scrivi 3-4 frasi in italiano che spieghino:
1. Di cosa parla l'articolo
2. Perche e importante
3. Chi e interessato

Spiegazione:"""
        try:
            return self._call_llm(prompt, max_tokens=400)
        except Exception as e:
            print(f"    [!] Errore explain: {e}")
            return f"Spiegazione non disponibile. Titolo: {title}"


# Singleton
_llm_client = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client