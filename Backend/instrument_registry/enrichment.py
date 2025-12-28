"""
Instrument Enrichment Service

Generates English translations and semantic descriptions using a Google Gemini LLM for search enhancement.
Enriched descriptions are internal-only, used for embeddings but never shown to users.
"""

from google import genai
from google.genai import types
from django.conf import settings
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

INVALID_ENRICHMENT_VALUES = {"", "Enrichment Failed", "Translation Failed"}

# Pydantic models for the response
class InstrumentDescription(BaseModel):
    index: int = Field(description="The index number matching the input list (1-based)")
    translation: str = Field(description="Precise English translation of the instrument name")
    description: str = Field(description="2-3 sentence English semantic description in lowercase")

class BatchResponse(BaseModel):
    results: list[InstrumentDescription]

class EnrichmentService:
    """Handles AI enrichment using a Google Gemini LLM"""
    
    def __init__(self):
        api_key = getattr(settings, 'GOOGLE_GENAI_API_KEY', '')
        if not api_key:
            raise ValueError("GOOGLE_GENAI_API_KEY not configured in settings")
        
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=45000) 
        )
        self.model_id = getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-2.5-flash-lite')
    
    def enrich_single(self, finnish_name, brand_model="", additional_info=""):
        """Generate English semantic description from Finnish instrument name."""
        if not finnish_name:
            return {'translation': "Translation Failed", 'description': "Enrichment Failed"}
        
        try:
            # Reuse the batch prompt logic for single items
            return self.enrich_batch([{
                'finnish_name': finnish_name, 
                'brand_model': brand_model, 
                'info': additional_info
            }])[0]
            
        except Exception as e:
            logger.error(f"Enrichment error for '{finnish_name}': {e}")
            return {'translation': "Translation Failed", 'description': "Enrichment Failed"}
    
    def enrich_batch(self, items, sub_batch_size=50):
        """
        Enrich multiple instruments using true batch processing.
        Sends multiple instruments in single API call for efficiency.
        """
        all_results = []

        for i in range(0, len(items), sub_batch_size):
            sub_batch = items[i:i + sub_batch_size]
            
            try:
                prompt = self._build_batch_prompt(sub_batch)
                
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                        response_schema=BatchResponse,
                    ),
                )
                
                batch_data = BatchResponse.model_validate_json(response.text)
                enrichments = self._process_structured_results(batch_data, len(sub_batch))
                all_results.extend(enrichments)
                
            except Exception as e:
                # If we are already processing a single item (fallback mode), stop the loop.
                if len(sub_batch) == 1:
                    logger.error(f"Single item processing failed: {e}")
                    # Manually append a failed result
                    all_results.append({
                        'translation': "Translation Failed",
                        'description': "Enrichment Failed"
                    })
                else:
                    # Only fallback if it was a group that failed
                    logger.warning(f"Batch failed (Size {len(sub_batch)}). Retrying individually. Error: {e}")
                    enrichments = self._fallback_individual_enrichment(sub_batch)
                    all_results.extend(enrichments)
        
        return all_results
    
    def _fallback_individual_enrichment(self, items):
        """Fallback to individual enrichment when batch fails."""
        logger.info(f"Processing {len(items)} items individually as fallback")
        results = []
        for item in items:
            try:
                enriched = self.enrich_single(
                    item.get('finnish_name', ''),
                    item.get('brand_model', ''),
                    item.get('info', '')
                )
                results.append(enriched)
            except Exception as e:
                logger.error(f"Individual enrichment failed for {item.get('finnish_name')}: {e}")
                results.append({
                    'translation': "Translation Failed",
                    'description': "Enrichment Failed"
                })
        return results

    def _process_structured_results(self, batch_data: BatchResponse, expected_count: int):
        """Map the structured results back to a simple list of strings."""
        # Create a placeholder list to ensure alignment
        final_list = [{
            'translation': "Translation Failed", 
            'description': "Enrichment Failed"
        } for _ in range(expected_count)]
        
        for item in batch_data.results:
            idx = item.index - 1
            if 0 <= idx < expected_count:
                final_list[idx] = {
                    'translation': item.translation.strip(),
                    'description': item.description.strip().lower()
                }
        
        return final_list
    
    def _build_batch_prompt(self, items):
        """Prompt asking for Translation AND Description"""
        instrument_list = []
        for i, item in enumerate(items, 1):
            finnish_name = item.get('finnish_name', 'Unknown')
            # Add brand/info to the prompt text if available
            extra = ""
            if item.get('brand_model'): extra += f" (Model: {item.get('brand_model')})"
            
            instrument_list.append(f"{i}. {finnish_name}{extra}")
        
        instruments_text = "\n".join(instrument_list)
        
        return f"""You are a laboratory equipment expert. 
Process these {len(items)} Finnish laboratory instruments.

INSTRUMENTS:
{instruments_text}

TASKS:
1. TRANSLATE: Provide the most accurate professional English name (e.g., "vetokaappi" -> "Fume Hood").
2. DESCRIBE: Generate a 2-3 sentence semantic description in lowercase.

- TRANSLATION RULES:
-- Use the provided Model/Brand info to identify the specific device type (e.g., differentiate a "Chemical Analyzer" from a "Hematology Analyzer").
-- Output the STANDARD GENERIC NAME, not the brand name (e.g., "Real-Time PCR System", NOT "LightCycler").

- DESCRIPTION REQUIREMENTS:
-- What the equipment is and its primary purpose
-- Common applications in laboratory/research settings
-- Key characteristics or capabilities
-- **Include common industry synonyms or alternative names naturally (e.g., "also known as...")**
-- OUTPUT MUST BE IN ENGLISH
-- Be factual and concise
-- **Optimize for search relevance: prioritize technical keywords over flowery language**
-- Do not repeat brand names unnecessarily

Generate a response following the given schema."""

def enrich_instruments_batch(unique_names_to_enrich, translation_cache, enrichment_cache, on_error=lambda msg: None):
    """
    Updates translation_cache and enrichment_cache with the results of the enrichment.
    unique_names_to_enrich is dict: {name_key: finnish_name}
    """
    items_to_enrich = []

    # Identify items that need processing (if EITHER cache is missing/failed)
    for name_key, item in unique_names_to_enrich.items():
        # Check if we still need to process this key
        needs_trans = name_key not in translation_cache or translation_cache[name_key] in INVALID_ENRICHMENT_VALUES
        needs_enrich = name_key not in enrichment_cache or enrichment_cache[name_key] in INVALID_ENRICHMENT_VALUES
        
        if needs_trans or needs_enrich:
            items_to_enrich.append({
                'finnish_name': item['finnish_name'],  # Extract name
                'brand_model': item['brand_model'],    # Extract model info
                'cache_key': name_key
            })

    if not items_to_enrich:
        return

    logger.info(f"Enriching & Translating {len(items_to_enrich)} instruments via Gemini") 
    
    try:
        service = EnrichmentService()
        results = service.enrich_batch(items_to_enrich)
        
        for item, result in zip(items_to_enrich, results):
            key = item['cache_key']
            
            # Update caches
            if result['translation'] != "Translation Failed":
                translation_cache[key] = result['translation']
            
            if result['description'] != "Enrichment Failed":
                enrichment_cache[key] = result['description']
            
    except Exception as e:
        error_msg = f"Batch processing error: {e}"
        logger.error(error_msg)
        on_error(error_msg)