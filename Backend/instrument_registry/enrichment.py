"""
Instrument Enrichment Service

Generates semantic descriptions using Google AI Studio 2.0 Flash for search enhancement.
Enriched descriptions are internal-only, used for embeddings but never shown to users.
"""

from google import genai
from google.genai import types
from django.conf import settings
import time
import logging
import json
import re

logger = logging.getLogger(__name__)

INVALID_ENRICHMENT_VALUES = {"", "Enrichment Failed"}

class EnrichmentService:
    """Handles AI enrichment using Google Gemini 2.0 Flash"""
    
    def __init__(self):
        api_key = getattr(settings, 'GOOGLE_GENAI_API_KEY', '')
        if not api_key:
            raise ValueError("GOOGLE_GENAI_API_KEY not configured in settings")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-2.0-flash-exp')
        
        # Rate limiting (15 RPM for Google AI Studio free tier)
        self.requests_per_minute = 15
        self.last_request_times = []
    
    def _rate_limit(self):
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.last_request_times = [
            t for t in self.last_request_times 
            if current_time - t < 60
        ]
        
        # If at limit, wait until oldest request expires
        if len(self.last_request_times) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_times[0]) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.last_request_times = []
        
        self.last_request_times.append(current_time)
    
    def enrich_single(self, finnish_name, brand_model="", additional_info=""):
        """Generate English semantic description from Finnish instrument name."""
        if not finnish_name or finnish_name in INVALID_ENRICHMENT_VALUES:
            return "Enrichment Failed"
        
        try:
            self._rate_limit()
            
            prompt = self._build_enrichment_prompt(
                finnish_name, brand_model, additional_info
            )
            
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for more factual output
                    max_output_tokens=400,  # Keep descriptions concise
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
                self._rate_limit()
                
                prompt = self._build_batch_prompt(sub_batch)
                
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=100 * len(sub_batch),
                    )
                )
                
                enrichments = self._parse_batch_response(response.text, len(sub_batch))
                
                if len(enrichments) != len(sub_batch):
                    logger.warning(
                        f"Expected {len(sub_batch)} enrichments, got {len(enrichments)}. "
                        f"Falling back to individual processing."
                    )
                    enrichments = self._fallback_individual_enrichment(sub_batch)
                
                all_results.extend(enrichments)
                
            except Exception as e:
                logger.error(f"Batch enrichment failed for {len(sub_batch)} items: {e}")
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
                    item.get('name', ''),
                    item.get('brand_model', ''),
                    item.get('info', '')
                )
                results.append(enriched)
            except Exception as e:
                logger.error(f"Individual enrichment failed for {item.get('name')}: {e}")
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
        
        prompt = f"""You are a laboratory equipment expert. You will receive a Finnish instrument name and generate a concise English semantic description optimized for search.

Finnish Equipment Name: {finnish_name}
{additional_context}

Generate a 2-3 sentence English description that includes:
- What the equipment is and its primary purpose
- Common applications in laboratory/research settings
- Key characteristics or capabilities

Requirements:
- OUTPUT MUST BE IN ENGLISH
- Be factual and concise
- Use lowercase
- Focus on searchable semantic content
- Include the English equipment name/category naturally in the description
- Do not repeat unnecessarily
- Do not include brand names unless provided above

English Description:"""
        
        return prompt
    
    def _build_batch_prompt(self, items):
        """Build prompt for batch enrichment of multiple instruments."""
        instrument_list = []
        for i, item in enumerate(items, 1):
            finnish_name = item.get('name', 'Unknown')
            brand = item.get('brand_model', '')
            info = item.get('info', '')
            
            entry = f"{i}. Finnish name: {finnish_name}"
            if brand:
                entry += f", Brand/Model: {brand}"
            if info and len(info.strip()) > 5:
                truncated_info = info[:150] if len(info) > 150 else info
                entry += f", Notes: {truncated_info}"
            
            instrument_list.append(entry)
        
        instruments_text = "\n".join(instrument_list)
        
        prompt = f"""You are a laboratory equipment expert. Generate concise English semantic descriptions for {len(items)} laboratory instruments.

INSTRUMENTS:
{instruments_text}

OUTPUT FORMAT: JSON array with exactly {len(items)} objects. Each object MUST have:
- "index": the number (1 to {len(items)})
- "description": 2-3 sentence English description in lowercase

Requirements for each description:
- What the equipment is and its primary purpose
- Common applications in laboratory/research settings
- Key characteristics or capabilities
- OUTPUT MUST BE IN ENGLISH
- Use lowercase throughout
- Be factual and concise
- Focus on searchable semantic content
- Include the English equipment name/category naturally
- Do not repeat brand names unnecessarily

Output ONLY the JSON array, no other text:"""
        
        return prompt
    
    def _parse_batch_response(self, response_text, expected_count):
        """Parse JSON array from batch response."""
        try:
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in response")
            
            data = json.loads(json_match.group())
            
            if not isinstance(data, list):
                raise ValueError("Response is not a JSON array")
            
            if len(data) != expected_count:
                logger.warning(
                    f"JSON array length mismatch: expected {expected_count}, got {len(data)}"
                )
            
            sorted_data = sorted(data, key=lambda x: x.get('index', 0))
            
            descriptions = []
            for item in sorted_data:
                desc = item.get('description', '').strip().lower()
                if desc and len(desc) >= 10:
                    descriptions.append(desc)
                else:
                    descriptions.append("Enrichment Failed")
            
            return descriptions
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON in response: {e}")
        except Exception as e:
            logger.error(f"Error parsing batch response: {e}")
            raise


def enrich_instruments_batch(unique_names_to_enrich, enrichment_cache, on_error=lambda msg: None):
    """Enrich instruments using cached values when possible. Returns updated cache."""
    items_to_enrich = []
    
    for item in unique_names_to_enrich:
        if item not in enrichment_cache:
            items_to_enrich.append(item)
    
    if not items_to_enrich:
        return enrichment_cache
    
    logger.info(f"Enriching {len(items_to_enrich)} instruments via Google AI (Finnish→English)")
    
    try:
        service = EnrichmentService()
        enriched_results = service.enrich_batch(items_to_enrich)
        for item, enrichment in zip(items_to_enrich, enriched_results):
            enrichment_cache[item] = enrichment
            if enrichment not in INVALID_ENRICHMENT_VALUES:
                logger.debug(f"Enriched '{item}': {enrichment[:50]}...")
            
    except Exception as e:
        error_msg = f"Batch enrichment error: {e}"
        logger.error(error_msg)
        on_error(error_msg)
        for item in items_to_enrich:
            enrichment_cache[item] = "Enrichment Failed"
    
    return enrichment_cache