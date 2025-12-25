"""
Instrument Enrichment Service

Generates semantic descriptions using a Google Gemini LLM for search enhancement.
Enriched descriptions are internal-only, used for embeddings but never shown to users.
"""

from google import genai
from google.genai import types
from django.conf import settings
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

INVALID_ENRICHMENT_VALUES = {"", "Enrichment Failed"}

# Pydantic models for the response
class InstrumentDescription(BaseModel):
    index: int = Field(description="The index number matching the input list (1-based)")
    description: str = Field(description="2-3 sentence English semantic description in lowercase")

class BatchResponse(BaseModel):
    results: list[InstrumentDescription]

class EnrichmentService:
    """Handles AI enrichment using a Google Gemini LLM"""
    
    def __init__(self):
        api_key = getattr(settings, 'GOOGLE_GENAI_API_KEY', '')
        if not api_key:
            raise ValueError("GOOGLE_GENAI_API_KEY not configured in settings")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-2.5-flash-lite')
    
    def enrich_single(self, finnish_name, brand_model="", additional_info=""):
        """Generate English semantic description from Finnish instrument name."""
        if not finnish_name or finnish_name in INVALID_ENRICHMENT_VALUES:
            return "Enrichment Failed"
        
        try:
            prompt = self._build_enrichment_prompt(
                finnish_name, brand_model, additional_info
            )
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for more factual output
                    max_output_tokens=8192,
                )
            )
            
            enriched = response.text.strip()
            
            # Validate response
            if not enriched or len(enriched) < 10:
                logger.warning(f"Invalid enrichment for '{finnish_name}': too short")
                return "Enrichment Failed"
            
            return enriched.lower()
            
        except Exception as e:
            logger.error(f"Enrichment error for '{finnish_name}': {e}")
            return "Enrichment Failed"
    
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
                    )
                )
                
                # Single validation step
                batch_data = BatchResponse.model_validate_json(response.text)
                enrichments = self._process_structured_results(batch_data, len(sub_batch))
                all_results.extend(enrichments)
                
            except Exception as e:
                # Catches both Network errors AND Pydantic/Validation errors
                logger.error(f"Batch failed (Batch {i}-{i+len(sub_batch)}): {e}")
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
                results.append("Enrichment Failed")
        return results
    
    def _build_enrichment_prompt(self, finnish_name, brand, info):
        """Build prompt for single instrument enrichment."""
        context_parts = []
        if brand:
            context_parts.append(f"Brand/Model: {brand}")
        if info and len(info.strip()) > 5:
            truncated_info = info[:200] if len(info) > 200 else info
            context_parts.append(f"Notes: {truncated_info}")
        
        additional_context = ". ".join(context_parts) if context_parts else ""
        
        return f"""You are a laboratory equipment expert. You will receive a Finnish instrument name and generate a concise English semantic description optimized for search.
Finnish Equipment Name: {finnish_name}
{additional_context}

Generate a 2-3 sentence English description that includes:
- What the equipment is and its primary purpose
- Common applications in laboratory/research settings
- Key characteristics or capabilities

Requirements:
- OUTPUT MUST BE IN ENGLISH
- Be factual and concise
- Focus on searchable semantic content
- Include the English equipment name/category naturally in the description
- Do not repeat unnecessarily
- Do not include brand names unless provided above

English Description:"""

    def _process_structured_results(self, batch_data: BatchResponse, expected_count: int):
        """Map the structured results back to a simple list of strings."""
        # Create a placeholder list to ensure alignment
        final_list = ["Enrichment Failed"] * expected_count
        
        for item in batch_data.results:
            # Adjust 1-based index to 0-based
            idx = item.index - 1
            if 0 <= idx < expected_count:
                if len(item.description) > 10:
                    final_list[idx] = item.description.lower()
        
        return final_list
    
    def _build_batch_prompt(self, items):
        """Build prompt for batch enrichment of multiple instruments."""
        instrument_list = []
        for i, item in enumerate(items, 1):
            finnish_name = item.get('finnish_name', 'Unknown')
            instrument_list.append(f"{i}. Finnish name: {finnish_name}")
        
        instruments_text = "\n".join(instrument_list)
        
        return f"""You are a laboratory equipment expert. 
Generate concise English semantic descriptions for these {len(items)} laboratory instruments.

INSTRUMENTS:
{instruments_text}

DESCRIPTION REQUIREMENTS:
- What the equipment is and its primary purpose
- Common applications in laboratory/research settings
- Key characteristics or capabilities
- OUTPUT MUST BE IN ENGLISH
- Be factual and concise
- Focus on searchable semantic content
- Include the English equipment name naturally
- Do not repeat brand names unnecessarily

Generate a response following the given schema."""

def enrich_instruments_batch(unique_names_to_enrich, enrichment_cache, on_error=lambda msg: None):
    """Enrich instruments using cached values when possible. Returns updated cache."""
    items_to_enrich = []

    # unique_names_to_enrich is a dict {name_key: finnish_name}
    for name_key, finnish_name in unique_names_to_enrich.items():
        if name_key not in enrichment_cache:
            items_to_enrich.append({
                'finnish_name': finnish_name,  # Use actual Finnish name, not lowercase key
                'brand_model': '',
                'info': '',
                'cache_key': name_key
            })

    if not items_to_enrich:
        return enrichment_cache

    logger.info(f"Enriching {len(items_to_enrich)} instruments via Google AI (Finnish→English)")
    
    try:
        service = EnrichmentService()
        enriched_results = service.enrich_batch(items_to_enrich)
        for item, enrichment in zip(items_to_enrich, enriched_results):
            enrichment_cache[item['cache_key']] = enrichment
            if enrichment not in INVALID_ENRICHMENT_VALUES:
                logger.debug(f"Enriched '{item}': {enrichment[:50]}...")
            
    except Exception as e:
        error_msg = f"Batch enrichment error: {e}"
        logger.error(error_msg)
        on_error(error_msg)
        for item in items_to_enrich:
            enrichment_cache[item['cache_key']] = "Enrichment Failed"
    
    return enrichment_cache