"""
LLM Client per Pulse.
Chiama Groq, Cerebras, Gemini direttamente con OpenAI SDK.
Fallback automatico se un provider fallisce o va in rate limit.
"""

import os
from typing import Optional
from openai import OpenAI, RateLimitError, APIError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

settings = get_settings()


class LLMClient:
    """
    Client unificato per 3 provider free:
    1. Groq — veloce, buono per scoring e task semplici
    2. Cerebras — alta qualità, buono per sintesi profonde
    3. Gemini — contesto lungo, fallback sicuro
    """

    def __init__(self):
        # Inizializza 3 client con base_url diverse
        self.clients = {
            "groq": OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            ),
            "cerebras": OpenAI(
                api_key=settings.cerebras_api_key,
                base_url="https://api.cerebras.ai/v1",
            ),
            "gemini": OpenAI(
                api_key=settings.gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
        }

        # Mappa modelli → provider
        self.models = {
            "fast": "groq/llama-3.1-8b-instant",           # scoring, spiegazioni brevi
            "quality": "cerebras/gpt-oss-120b",             # sintesi profonda
            "long": "gemini/gemini-3.5-flash",              # contesto lungo
        }

    def _get_client_and_model(self, model_key: str):
        """
        Estrae provider e nome modello dalla stringa "provider/modello".
        """
        full_name = self.models.get(model_key, self.models["fast"])
        provider, model_name = full_name.split("/", 1)
        return self.clients[provider], model_name, provider

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=lambda e: isinstance(e, (RateLimitError, APIError)),
    )
    def complete(
        self,
        prompt: str,
        model_key: str = "fast",
        temperature: float = 0.7,
        max_tokens: int = 500,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Chiama il LLM con retry automatico su rate limit.
        Se fallisce, prova il provider successivo.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Ordine di fallback: richiesto → quality → fast → long
        fallback_order = [model_key, "quality", "fast", "long"]
        tried = set()

        for key in fallback_order:
            if key in tried:
                continue
            tried.add(key)

            try:
                client, model_name, provider = self._get_client_and_model(key)
                print(f"  🔄 Chiamata {provider}/{model_name}...")

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                result = response.choices[0].message.content
                print(f"  ✅ OK ({provider})")
                return result

            except RateLimitError as e:
                print(f"  ⚠️ Rate limit su {key}: {e}")
                continue  # prova fallback

            except APIError as e:
                print(f"  ⚠️ API error su {key}: {e}")
                continue  # prova fallback

            except Exception as e:
                print(f"  ❌ Errore su {key}: {e}")
                continue

        # Se tutti falliscono
        raise RuntimeError("Tutti i provider LLM hanno fallito.")

    # --- Metodi convenienza per task specifici ---

    def score_relevance(self, title: str, summary: str, field: str) -> int:
        """
        Score 1-10 per rilevanza di una notizia nel suo campo.
        Usa modello fast (Groq) per velocità.
        """
        prompt = f"""Valuta la rilevanza di questa notizia per il campo {field.upper()}.

Titolo: {title}
Sommario: {summary}

Rispondi SOLO con un numero da 1 a 10, dove:
1 = irrilevante
10 = estremamente rilevante e importante

Score:"""

        try:
            result = self.complete(prompt, model_key="fast", temperature=0.1, max_tokens=5)
            # Estrai numero dalla risposta
            score = int("".join(filter(str.isdigit, result)))
            return max(1, min(10, score))  # clamp 1-10
        except:
            return 5  # default neutro

    def summarize(self, text: str, field: str) -> str:
        """
        Riassume un articolo in 2-3 frasi.
        Usa modello quality (Cerebras) per qualità.
        """
        prompt = f"""Riassumi questo articolo di {field.upper()} in 2-3 frasi concise e chiare.

Articolo:
{text}

Riassunto:"""

        return self.complete(prompt, model_key="quality", temperature=0.5, max_tokens=200)

    def explain_why_matters(self, title: str, summary: str, field: str) -> str:
        """
        Spiega "Perché questa notizia importa" in 1-2 frasi.
        """
        prompt = f"""Spiega perché questa notizia di {field.upper()} è importante.

Titolo: {title}
Riassunto: {summary}

Perché importa (1-2 frasi, impatto concreto):"""

        return self.complete(prompt, model_key="quality", temperature=0.6, max_tokens=150)

    def explain_briefing(self, title: str, summary: str) -> str:
        """
        Spiega il contenuto del briefing in modo breve, chiaro e diretto.
        Massimo 3 frasi. Linguaggio professionale ma accessibile.
        """
        # FIX: se il testo è vuoto o troppo corto, usa solo il titolo
        if not summary or len(summary.strip()) < 50:
            text = title
        else:
            text = summary

        prompt = f"""Spiega questo articolo in modo breve, chiaro e diretto.
Massimo 3 frasi. Linguaggio professionale ma accessibile.

Titolo: {title}
Testo: {text}

Spiegazione breve:"""

        return self.complete(prompt, model_key="fast", temperature=0.5, max_tokens=150)


# --- Singleton ---
_llm_client = None


def get_llm_client() -> LLMClient:
    """Restituisce istanza singleton del LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client