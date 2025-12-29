import json
import os
import re
import requests
import signal
import sys
import time
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# Default constants
DEFAULT_MAX_RECORDS = 1000
DEFAULT_MAX_CONSECUTIVE_FAILURES = 3
DEFAULT_MODEL_X_URL = "http://192.168.1.29:8081"
DEFAULT_MODEL_Y_URL = "http://192.168.1.29:8080"
OUTPUT_DIR = "rag_data"

@dataclass
class GeneratorConfig:
    max_records: int = DEFAULT_MAX_RECORDS
    max_consecutive_failures: int = DEFAULT_MAX_CONSECUTIVE_FAILURES
    model_x_url: str = DEFAULT_MODEL_X_URL
    model_y_url: str = DEFAULT_MODEL_Y_URL
    delay_between_records: float = 1.0
    rag_domain: str = "PHP 8 and HTML5"  # Domain for RAG generation
    rag_focus: str = "security and performance"  # Focus area
    rag_constraint: str = "proprietary library constraint (e.g., 'use the `Sanitizer::filter()` class')"  # Required constraint type
    rag_skill_level: str = "senior architect"  # Persona skill level
    rag_languages: str = "PHP and/or HTML"  # Target languages
    web_format: bool = False  # Generate HTML pages instead of JSON

class RagGenerator:
    def __init__(self, config: GeneratorConfig, status_callback=None):
        self.config = config
        self.consecutive_failures = 0
        self.total_records = 0
        self.running = False
        self.status_callback = status_callback
        
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C and termination signals gracefully"""
        if self.status_callback:
            self.status_callback(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def _update_status(self, message: str):
        """Update status via callback if available"""
        if self.status_callback:
            self.status_callback(message)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to handle common parsing issues"""
        # Remove leading/trailing whitespace
        json_str = json_str.strip()
        
        # Try to extract JSON object/array if wrapped in extra text
        # Look for first { or [ and last } or ]
        first_brace = json_str.find('{')
        first_bracket = json_str.find('[')
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = json_str.rfind('}')
            if last_brace > first_brace:
                json_str = json_str[first_brace:last_brace+1]
        elif first_bracket != -1:
            last_bracket = json_str.rfind(']')
            if last_bracket > first_bracket:
                json_str = json_str[first_bracket:last_bracket+1]
        
        # Try to fix invalid escape sequences
        # JSON only allows: ", \, /, \b, \f, \n, \r, \t, \uXXXX
        # We'll try to escape unescaped backslashes that aren't part of valid sequences
        import re
        # This regex finds backslashes that aren't part of valid escape sequences
        # But we need to be careful - this is complex, so we'll use a simpler approach
        
        # Try parsing first
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            # If it's an escape error, try to fix it
            if "Invalid \\escape" in str(e) or "Invalid escape" in str(e):
                # Try to fix by escaping problematic backslashes
                # This is a heuristic - replace \ followed by non-escape chars with \\
                # But we need to avoid breaking valid escapes
                # Simple approach: double all backslashes, then fix valid ones
                # Actually, better: use a more careful replacement
                try:
                    # Try using codecs to decode/encode which might fix some issues
                    import codecs
                    # This won't work for JSON, let's try a different approach
                    # Replace invalid escape sequences manually
                    # Find positions of invalid escapes from error message if possible
                    pass
                except:
                    pass
            
            # If we can't fix it, return as-is and let the error propagate
            # The error message will help debug
            return json_str
    
    def call_model(self, endpoint_url: str, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Make HTTP call to model endpoint"""
        try:
            response = requests.post(
                f"{endpoint_url}/v1/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            self._update_status(f"Error calling model at {endpoint_url}: {e}")
            return None
    
    def call_model_x(self) -> Optional[Dict]:
        """Call Model X to generate intent and tags"""
        # Determine if this is a coding domain or content domain
        is_coding_domain = any(keyword in self.config.rag_domain.lower() for keyword in 
                              ['programming', 'coding', 'software', 'development', 'php', 'python', 
                               'javascript', 'java', 'html', 'css', 'code', 'developer'])
        
        if is_coding_domain:
            system_prompt = f"""Sei un {self.config.rag_skill_level} specializzato in {self.config.rag_domain}, focalizzato su {self.config.rag_focus}.
Genera un requisito di coding specifico (l'Intent) in formato JSON strict.
L'Intent deve riguardare l'interazione tra {self.config.rag_languages} e deve includere almeno un {self.config.rag_constraint}.

Rispondi SOLO con un JSON in questo formato:
{{
  "raw_intent": "Requisito di coding specifico e dettagliato che includa vincoli tecnici chiari.",
  "tags": ["tag1", "tag2", "tag3"]
}}"""
            user_prompt = f"Genera un nuovo requisito di coding per {self.config.rag_languages} con focus su {self.config.rag_focus}."
        else:
            # Generic content domain (cucina, ricette, etc.)
            system_prompt = f"""Sei un {self.config.rag_skill_level} specializzato in {self.config.rag_domain}, focalizzato su {self.config.rag_focus}.
Genera un requisito specifico (l'Intent) in formato JSON strict.
L'Intent deve riguardare {self.config.rag_domain} e deve includere almeno un {self.config.rag_constraint}.

Rispondi SOLO con un JSON in questo formato:
{{
  "raw_intent": "Requisito specifico e dettagliato relativo a {self.config.rag_domain}.",
  "tags": ["tag1", "tag2", "tag3"]
}}"""
            user_prompt = f"Genera un nuovo requisito per {self.config.rag_domain} con focus su {self.config.rag_focus}."
        
        response = self.call_model(self.config.model_x_url, system_prompt, user_prompt)
        if response:
            try:
                # Try to extract JSON from response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].strip()
                else:
                    json_str = response.strip()
                
                # Clean up common JSON issues
                json_str = self._clean_json_string(json_str)
                
                data = json.loads(json_str)
                if self.validate_json(data, ["raw_intent", "tags"]):
                    return data
            except json.JSONDecodeError as e:
                self._update_status(f"Failed to parse JSON from Model X: {e}")
                self._update_status(f"Response preview: {response[:200]}...")
        
        return None
    
    def call_model_y(self, intent_data: Dict) -> Optional[Dict]:
        """Call Model Y to generate solution"""
        # Determine if this is a coding domain or content domain
        is_coding_domain = any(keyword in self.config.rag_domain.lower() for keyword in 
                              ['programming', 'coding', 'software', 'development', 'php', 'python', 
                               'javascript', 'java', 'html', 'css', 'code', 'developer'])
        
        if is_coding_domain:
            system_prompt = f"""Sei un {self.config.rag_skill_level} specializzato in {self.config.rag_domain}, con focus su {self.config.rag_focus}.
Sei esperto in {self.config.rag_languages} e abile a scrivere codice pulito, commentato e aderente ai vincoli specificati.
Riceverai un raw_intent generato da un altro modello che descrive un requisito di coding specifico.

Il tuo compito è:
1. Analizzare l'Intent ricevuto
2. Produrre una soluzione completa usando {self.config.rag_languages}
3. Assicurarti che la soluzione rispetti i vincoli e le best practices del dominio {self.config.rag_domain}
4. Includere commenti dettagliati per spiegare l'approccio

Rispondi SOLO con un JSON in questo formato:
{{
  "code_snippet": "Codice completo con commenti dettagliati per risolvere il problema specifico.",
  "description": "Spiegazione chiara dell'approccio utilizzato per risolvere l'Intent."
}}"""
            user_prompt = f"""Risolvi questo requisito di coding:
{intent_data['raw_intent']}

Tags: {", ".join(intent_data['tags'])}"""
        else:
            # Generic content domain (cucina, ricette, etc.)
            system_prompt = f"""Sei un {self.config.rag_skill_level} specializzato in {self.config.rag_domain}, con focus su {self.config.rag_focus}.
Riceverai un raw_intent generato da un altro modello che descrive un requisito specifico relativo a {self.config.rag_domain}.

Il tuo compito è:
1. Analizzare l'Intent ricevuto
2. Produrre una soluzione completa e dettagliata relativa a {self.config.rag_domain}
3. Assicurarti che la soluzione rispetti i vincoli e le best practices del dominio {self.config.rag_domain}
4. Fornire informazioni chiare e dettagliate

Rispondi SOLO con un JSON in questo formato:
{{
  "code_snippet": "Contenuto completo e dettagliato per risolvere il requisito specifico.",
  "description": "Spiegazione chiara dell'approccio utilizzato per risolvere l'Intent."
}}"""
            user_prompt = f"""Risolvi questo requisito:
{intent_data['raw_intent']}

Tags: {", ".join(intent_data['tags'])}"""
        
        response = self.call_model(self.config.model_y_url, system_prompt, user_prompt)
        if response:
            try:
                # Try to extract JSON from response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].strip()
                else:
                    json_str = response.strip()
                
                # Clean up common JSON issues
                json_str = self._clean_json_string(json_str)
                
                data = json.loads(json_str)
                if self.validate_json(data, ["code_snippet", "description"]):
                    return data
            except json.JSONDecodeError as e:
                self._update_status(f"Failed to parse JSON from Model Y: {e}")
                self._update_status(f"Response preview: {response[:200]}...")
        
        return None
    
    def validate_json(self, data: Dict, required_keys: List[str]) -> bool:
        """Validate that required keys exist and are not empty"""
        for key in required_keys:
            if key not in data or not data[key] or str(data[key]).strip() == "":
                self._update_status(f"Validation failed: missing or empty key '{key}'")
                return False
        return True
    
    def save_record(self, record: Dict) -> str:
        """Save record to JSON file with timestamp and UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"record_{timestamp}_{unique_id}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e:
            self._update_status(f"Error saving record to {filepath}: {e}")
            return ""
    
    def save_html_record(self, record: Dict) -> str:
        """Save record as HTML page with timestamp and UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Generate title from raw_intent or description
        title = self._generate_title(record)
        
        # Create URL-friendly filename
        safe_title = self._create_safe_filename(title)
        filename = f"{safe_title}_{timestamp}_{unique_id}.html"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Generate HTML content
        html_content = self._generate_html_page(record, title)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return filepath
        except Exception as e:
            self._update_status(f"Error saving HTML record to {filepath}: {e}")
            return ""
    
    def _generate_title(self, record: Dict) -> str:
        """Generate a title from the record"""
        # Try to extract title from raw_intent (first sentence or key phrase)
        raw_intent = record.get('raw_intent', '')
        if raw_intent:
            # Take first sentence or first 60 chars
            title = raw_intent.split('.')[0].strip()
            if len(title) > 60:
                title = title[:57] + '...'
            if title:
                return title
        
        # Fallback to description
        description = record.get('description', '')
        if description:
            title = description.split('.')[0].strip()
            if len(title) > 60:
                title = title[:57] + '...'
            if title:
                return title
        
        # Final fallback
        return f"Solution {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _create_safe_filename(self, title: str) -> str:
        """Create a URL-safe filename from title"""
        import re
        # Remove special characters, keep only alphanumeric, spaces, and hyphens
        safe = re.sub(r'[^\w\s-]', '', title)
        # Replace spaces with hyphens
        safe = re.sub(r'[-\s]+', '-', safe)
        # Limit length
        if len(safe) > 50:
            safe = safe[:50]
        return safe.lower().strip('-')
    
    def _generate_html_page(self, record: Dict, title: str) -> str:
        """Generate a complete HTML page from the record"""
        # Extract content
        raw_intent = record.get('raw_intent', '')
        code_snippet = record.get('code_snippet', '')
        description = record.get('description', '')
        tags = record.get('tags', [])
        
        # Combine content - prefer code_snippet, fallback to description
        main_content = code_snippet if code_snippet else description
        if not main_content:
            main_content = raw_intent
        
        # Format tags
        tags_html = ''
        if tags:
            tags_html = '<div class="tags">' + ''.join([f'<span class="tag">{tag}</span>' for tag in tags]) + '</div>'
        
        # Generate meta description
        meta_description = description[:160] if description else raw_intent[:160] if raw_intent else title
        
        html_template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{self._escape_html(meta_description)}">
    <meta name="keywords" content="{", ".join(tags) if tags else ''}">
    <meta name="author" content="RAG Generator">
    <meta property="og:title" content="{self._escape_html(title)}">
    <meta property="og:description" content="{self._escape_html(meta_description)}">
    <meta property="og:type" content="article">
    <title>{self._escape_html(title)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.95;
            font-weight: 300;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .intent-section {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
        }}
        
        .intent-section h2 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}
        
        .intent-section p {{
            color: #555;
            line-height: 1.8;
        }}
        
        .solution-section {{
            margin-bottom: 30px;
        }}
        
        .solution-section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .solution-content {{
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            margin-top: 15px;
        }}
        
        .solution-content pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            line-height: 1.5;
            margin: 15px 0;
        }}
        
        .solution-content code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #e83e8c;
        }}
        
        .solution-content p {{
            margin-bottom: 15px;
            line-height: 1.8;
        }}
        
        .description-section {{
            background: #e8f4f8;
            border-left: 4px solid #17a2b8;
            padding: 20px;
            margin-top: 25px;
            border-radius: 4px;
        }}
        
        .description-section h3 {{
            color: #17a2b8;
            margin-bottom: 10px;
        }}
        
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .tag {{
            background: #667eea;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            body {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self._escape_html(title)}</h1>
            <div class="subtitle">Soluzione Completa</div>
        </div>
        
        <div class="content">
            {f'<div class="intent-section"><h2>Requisito</h2><p>{self._escape_html(raw_intent)}</p></div>' if raw_intent else ''}
            
            <div class="solution-section">
                <h2>Soluzione</h2>
                <div class="solution-content">
                    {self._format_content(main_content)}
                </div>
            </div>
            
            {f'<div class="description-section"><h3>Approccio</h3><p>{self._escape_html(description)}</p></div>' if description and description != main_content else ''}
            
            {tags_html}
        </div>
        
        <div class="footer">
            <p>Generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')} | RAG Generator</p>
        </div>
    </div>
</body>
</html>"""
        return html_template
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ''
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _format_content(self, content: str) -> str:
        """Format content, preserving code blocks and formatting"""
        if not content:
            return '<p>Nessun contenuto disponibile.</p>'
        
        # Check if content contains code blocks
        if '```' in content:
            # Split by code blocks
            parts = content.split('```')
            formatted = ''
            in_code = False
            
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Regular text
                    if part.strip():
                        # Convert newlines to paragraphs
                        paragraphs = [p.strip() for p in part.split('\n\n') if p.strip()]
                        for para in paragraphs:
                            formatted += f'<p>{self._escape_html(para)}</p>\n'
                else:
                    # Code block
                    if part.strip():
                        # Extract language if present
                        lines = part.split('\n', 1)
                        lang = lines[0].strip() if lines[0].strip() else ''
                        code = lines[1] if len(lines) > 1 else part
                        formatted += f'<pre><code>{self._escape_html(code)}</code></pre>\n'
            
            return formatted
        else:
            # Regular text, convert to paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if not paragraphs:
                paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
            
            formatted = ''
            for para in paragraphs:
                # Check if it's a code-like line (starts with common code patterns)
                if para.startswith(('<?', '<!', 'import ', 'def ', 'function ', 'class ', 'const ', 'let ', 'var ')):
                    formatted += f'<pre><code>{self._escape_html(para)}</code></pre>\n'
                else:
                    formatted += f'<p>{self._escape_html(para)}</p>\n'
            
            return formatted
    
    def get_existing_records_count(self) -> int:
        """Count existing JSON files in output directory"""
        if not os.path.exists(OUTPUT_DIR):
            return 0
        return len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')])
    
    def run(self) -> None:
        """Main generation loop"""
        self.running = True
        self._update_status(f"Starting RAG data generation...")
        self._update_status(f"Target records: {self.config.max_records}")
        self._update_status(f"Output format: {'HTML Pages' if self.config.web_format else 'JSON Records'}")
        self._update_status(f"Output directory: {OUTPUT_DIR}")
        self._update_status(f"Model X URL: {self.config.model_x_url}")
        self._update_status(f"Model Y URL: {self.config.model_y_url}")
        self._update_status(f"Delay between records: {self.config.delay_between_records}s")
        self._update_status("-" * 50)
        self._update_status(f"RAG Configuration:")
        self._update_status(f"  Domain: {self.config.rag_domain}")
        self._update_status(f"  Skill Level: {self.config.rag_skill_level}")
        self._update_status(f"  Focus: {self.config.rag_focus}")
        self._update_status(f"  Languages: {self.config.rag_languages}")
        self._update_status(f"  Constraint: {self.config.rag_constraint[:80]}..." if len(self.config.rag_constraint) > 80 else f"  Constraint: {self.config.rag_constraint}")
        self._update_status("-" * 50)
        
        while self.running and self.total_records < self.config.max_records:
            try:
                self._update_status(f"\nGenerating record {self.total_records + 1}/{self.config.max_records}...")
                
                # Check if stopped before each operation
                if not self.running:
                    self._update_status("Generation stopped by user")
                    break
                
                # Call Model X to generate intent
                self._update_status("Calling Model X to generate intent...")
                intent_data = self.call_model_x()
                
                if not self.running:
                    self._update_status("Generation stopped by user")
                    break
                
                if not intent_data:
                    self._update_status("Failed to get valid response from Model X")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.config.max_consecutive_failures:
                        self._update_status(f"Stopping: {self.config.max_consecutive_failures} consecutive failures")
                        break
                    # Wait before retry (interruptible)
                    for _ in range(20):  # 2 seconds in 0.1s increments
                        if not self.running:
                            break
                        time.sleep(0.1)
                    if not self.running:
                        break
                    continue
                
                # Check if stopped before Model Y call
                if not self.running:
                    self._update_status("Generation stopped by user")
                    break
                
                # Call Model Y to generate solution
                self._update_status("Calling Model Y to generate solution...")
                solution_data = self.call_model_y(intent_data)
                
                if not self.running:
                    self._update_status("Generation stopped by user")
                    break
                
                if not solution_data:
                    self._update_status("Failed to get valid response from Model Y")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.config.max_consecutive_failures:
                        self._update_status(f"Stopping: {self.config.max_consecutive_failures} consecutive failures")
                        break
                    # Wait before retry (interruptible)
                    for _ in range(20):  # 2 seconds in 0.1s increments
                        if not self.running:
                            break
                        time.sleep(0.1)
                    if not self.running:
                        break
                    continue
                
                # Combine data
                record = {
                    **intent_data,
                    **solution_data,
                    "generated_at": datetime.now().isoformat(),
                    "model_x_url": self.config.model_x_url,
                    "model_y_url": self.config.model_y_url
                }
                
                # Save record (JSON or HTML based on config)
                if self.config.web_format:
                    filepath = self.save_html_record(record)
                    file_type = "HTML page"
                else:
                    filepath = self.save_record(record)
                    file_type = "JSON record"
                
                if filepath:
                    self._update_status(f"✓ {file_type} saved: {os.path.basename(filepath)}")
                    self.total_records += 1
                    self.consecutive_failures = 0  # Reset failure counter on success
                else:
                    self._update_status(f"Failed to save {file_type.lower()}")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.config.max_consecutive_failures:
                        self._update_status(f"Stopping: {self.config.max_consecutive_failures} consecutive failures")
                        break
                
                # Delay between records for hardware cooldown (interruptible)
                if self.running and self.total_records < self.config.max_records:
                    self._update_status(f"Waiting {self.config.delay_between_records}s before next record...")
                    # Make delay interruptible by checking running status
                    delay_remaining = self.config.delay_between_records
                    while delay_remaining > 0 and self.running:
                        sleep_time = min(0.5, delay_remaining)  # Check every 0.5 seconds
                        time.sleep(sleep_time)
                        delay_remaining -= sleep_time
                
            except KeyboardInterrupt:
                self._update_status("\nInterrupted by user")
                break
            except Exception as e:
                self._update_status(f"Unexpected error: {e}")
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.config.max_consecutive_failures:
                    self._update_status(f"Stopping: {self.config.max_consecutive_failures} consecutive failures")
                    break
                # Wait longer on unexpected errors (interruptible)
                for _ in range(50):  # 5 seconds in 0.1s increments
                    if not self.running:
                        break
                    time.sleep(0.1)
                if not self.running:
                    break
        
        self._update_status(f"\nGeneration completed!")
        self._update_status(f"Total records generated: {self.total_records}")
        self._update_status(f"Records saved in: {OUTPUT_DIR}/")

class RagGeneratorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Data Generator")
        self.root.geometry("800x700")
        
        self.generator = None
        self.generation_thread = None
        
        # Create config
        self.config = GeneratorConfig()
        
        # Create UI elements
        self.create_widgets()
        
        # Initialize RAG configuration panel (but don't show it yet)
        self.rag_window = None
        
        # Update initial status
        self.update_folder_content()
        self.update_status("Ready to start generation")
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Max records
        ttk.Label(config_frame, text="Max Records:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.max_records_var = tk.IntVar(value=self.config.max_records)
        ttk.Entry(config_frame, textvariable=self.max_records_var, width=10).grid(row=0, column=1, sticky=tk.W)
        
        # Max consecutive failures
        ttk.Label(config_frame, text="Max Failures:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.max_failures_var = tk.IntVar(value=self.config.max_consecutive_failures)
        ttk.Entry(config_frame, textvariable=self.max_failures_var, width=10).grid(row=0, column=3, sticky=tk.W)
        
        # Delay between records
        ttk.Label(config_frame, text="Delay (s):").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.delay_var = tk.DoubleVar(value=self.config.delay_between_records)
        ttk.Entry(config_frame, textvariable=self.delay_var, width=10).grid(row=0, column=5, sticky=tk.W)
        
        # Model X URL
        ttk.Label(config_frame, text="Model X URL:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.model_x_var = tk.StringVar(value=self.config.model_x_url)
        ttk.Entry(config_frame, textvariable=self.model_x_var, width=30).grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Model Y URL
        ttk.Label(config_frame, text="Model Y URL:").grid(row=1, column=3, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.model_y_var = tk.StringVar(value=self.config.model_y_url)
        ttk.Entry(config_frame, textvariable=self.model_y_var, width=30).grid(row=1, column=4, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.records_label = ttk.Label(status_frame, text="Records: 0")
        self.records_label.grid(row=0, column=0, sticky=tk.W)
        
        self.failures_label = ttk.Label(status_frame, text="Failures: 0")
        self.failures_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # RAG Config display
        rag_info_frame = ttk.LabelFrame(main_frame, text="Current RAG Configuration", padding="5")
        rag_info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        rag_display_frame = ttk.Frame(rag_info_frame)
        rag_display_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        rag_info_frame.columnconfigure(0, weight=1)
        
        self.rag_status_label = ttk.Label(rag_display_frame, text="✓", font=('Arial', 10, 'bold'), foreground='green')
        self.rag_status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.rag_info_label = ttk.Label(rag_display_frame, text="", font=('Arial', 9), foreground='darkblue')
        self.rag_info_label.grid(row=0, column=1, sticky=tk.W)
        self.update_rag_info_display()
        
        # Web Format option
        format_frame = ttk.LabelFrame(main_frame, text="Output Format", padding="5")
        format_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.web_format_var = tk.BooleanVar(value=self.config.web_format)
        web_format_check = ttk.Checkbutton(format_frame, text="Web Format (Generate HTML pages instead of JSON)", 
                                          variable=self.web_format_var)
        web_format_check.grid(row=0, column=0, sticky=tk.W)
        ttk.Label(format_frame, text="When enabled, generates complete HTML pages ready for web publishing", 
                 font=('Arial', 8), foreground='gray').grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Generation", command=self.start_generation)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_generation, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="Refresh Folder", command=self.update_folder_content).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Open Folder", command=self.open_folder).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="RAG Config", command=self.show_rag_config, style='Accent.TButton').grid(row=0, column=4, padx=(10, 0))
        
        # Paned window for status and folder content
        paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status log
        log_frame = ttk.LabelFrame(paned, text="Status Log", padding="5")
        paned.add(log_frame, weight=1)
        
        self.status_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Folder content
        folder_frame = ttk.LabelFrame(paned, text="Folder Content", padding="5")
        paned.add(folder_frame, weight=1)
        
        # Treeview for folder content
        columns = ("Size", "Modified")
        self.folder_tree = ttk.Treeview(folder_frame, columns=columns, height=10)
        self.folder_tree.heading("#0", text="Filename")
        self.folder_tree.heading("Size", text="Size")
        self.folder_tree.heading("Modified", text="Modified")
        
        self.folder_tree.column("#0", width=300)
        self.folder_tree.column("Size", width=100)
        self.folder_tree.column("Modified", width=150)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(folder_frame, orient=tk.VERTICAL, command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_rag_config_panel(self):
        """Create the RAG configuration panel as a separate window"""
        self.rag_window = tk.Toplevel(self.root)
        self.rag_window.title("RAG Configuration - Prompt Customization")
        self.rag_window.geometry("600x500")
        self.rag_window.transient(self.root)  # Keep on top of main window
        self.rag_window.grab_set()  # Modal window
        
        # Update variables with current config values (important for reopening)
        self.rag_domain_var = tk.StringVar(value=self.config.rag_domain)
        self.rag_focus_var = tk.StringVar(value=self.config.rag_focus)
        self.rag_constraint_var = tk.StringVar(value=self.config.rag_constraint)
        self.rag_skill_level_var = tk.StringVar(value=self.config.rag_skill_level)
        self.rag_languages_var = tk.StringVar(value=self.config.rag_languages)
        
        # Create main frame
        main_frame = ttk.Frame(self.rag_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🦾 RAG Prompt Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        # Domain configuration
        ttk.Label(main_frame, text="Domain / Technology:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(5, 2))
        domain_entry = ttk.Entry(main_frame, textvariable=self.rag_domain_var, width=60)
        domain_entry.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        ttk.Label(main_frame, text="Examples: 'Python and ML', 'JavaScript and React', 'Java and Spring Boot'", 
                 font=('Arial', 8), foreground='gray').grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Skill level
        ttk.Label(main_frame, text="Expert Level:", font=('Arial', 10, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=(5, 2))
        skill_entry = ttk.Entry(main_frame, textvariable=self.rag_skill_level_var, width=60)
        skill_entry.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        ttk.Label(main_frame, text="Examples: 'senior architect', 'principal engineer', 'tech lead'", 
                 font=('Arial', 8), foreground='gray').grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Focus area
        ttk.Label(main_frame, text="Focus / Specialization:", font=('Arial', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(5, 2))
        focus_entry = ttk.Entry(main_frame, textvariable=self.rag_focus_var, width=60)
        focus_entry.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        ttk.Label(main_frame, text="Examples: 'security and performance', 'scalability and maintainability', 'AI/ML integration'", 
                 font=('Arial', 8), foreground='gray').grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Required constraint
        ttk.Label(main_frame, text="Constraint Type (Required):", font=('Arial', 10, 'bold')).grid(row=10, column=0, sticky=tk.W, pady=(5, 2))
        constraint_entry = tk.Text(main_frame, height=4, width=60, wrap=tk.WORD, state=tk.NORMAL)
        constraint_entry.delete('1.0', tk.END)  # Clear first
        constraint_entry.insert('1.0', self.config.rag_constraint)  # Insert current value
        constraint_entry.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        ttk.Label(main_frame, text="Examples: 'proprietary library constraint', 'design pattern requirement', 'architecture pattern'", 
                 font=('Arial', 8), foreground='gray').grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Languages
        ttk.Label(main_frame, text="Target Languages/Tech:", font=('Arial', 10, 'bold')).grid(row=13, column=0, sticky=tk.W, pady=(5, 2))
        languages_entry = ttk.Entry(main_frame, textvariable=self.rag_languages_var, width=60)
        languages_entry.grid(row=14, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        ttk.Label(main_frame, text="Examples: 'Python and JavaScript', 'Java and SQL', 'C++ and CUDA'", 
                 font=('Arial', 8), foreground='gray').grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=(0, 20))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=16, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save Configuration", 
                  command=self.save_rag_config).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Load Preset", 
                  command=self.show_preset_menu).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Close", 
                  command=self.rag_window.destroy).grid(row=0, column=2, padx=(10, 0))
        
        # Store constraint entry for later use
        self.constraint_entry = constraint_entry
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(11, weight=1)
        
        # Center window on screen
        self.rag_window.update_idletasks()
        x = (self.rag_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.rag_window.winfo_screenheight() // 2) - (500 // 2)
        self.rag_window.geometry(f"600x500+{x}+{y}")
    
    def save_rag_config(self):
        """Save RAG configuration from the panel"""
        # Get values and validate
        domain = self.rag_domain_var.get().strip()
        focus = self.rag_focus_var.get().strip()
        constraint = self.constraint_entry.get('1.0', tk.END).strip()
        skill_level = self.rag_skill_level_var.get().strip()
        languages = self.rag_languages_var.get().strip()
        
        # Validate that all fields are filled
        if not domain or not focus or not constraint or not skill_level or not languages:
            messagebox.showerror("Validation Error", "All fields must be filled in!\n\nPlease complete all configuration fields before saving.")
            return
        
        # Save configuration
        self.config.rag_domain = domain
        self.config.rag_focus = focus
        self.config.rag_constraint = constraint
        self.config.rag_skill_level = skill_level
        self.config.rag_languages = languages
        
        # Update display in main window
        self.update_rag_info_display()
        
        messagebox.showinfo("Configuration Saved", "RAG configuration has been saved successfully!\n\nYou can now start generation with this configuration.")
        
        # Update status in main window
        self.update_status("RAG configuration updated:")
        self.update_status(f"Domain: {self.config.rag_domain}")
        self.update_status(f"Skill Level: {self.config.rag_skill_level}")
        self.update_status(f"Focus: {self.config.rag_focus}")
        self.update_status(f"Languages: {self.config.rag_languages}")
    
    def show_preset_menu(self):
        """Show preset configurations menu"""
        presets_window = tk.Toplevel(self.rag_window)
        presets_window.title("Load Preset Configuration")
        presets_window.geometry("500x400")
        presets_window.transient(self.rag_window)
        presets_window.grab_set()
        
        main_frame = ttk.Frame(presets_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Select a Preset:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 15))
        
        # Preset configurations
        presets = [
            {
                'name': '🟪 PHP/HTML Security',
                'domain': 'PHP 8 and HTML5',
                'skills': 'senior architect',
                'focus': 'security and performance',
                'constraint': 'proprietary library constraint (e.g., "use the `Sanitizer::filter()` class")',
                'languages': 'PHP and/or HTML'
            },
            {
                'name': '🔷 Python ML Integration',
                'domain': 'Python and Machine Learning',
                'skills': 'ML engineer specialist',
                'focus': 'AI/ML integration and model deployment',
                'constraint': 'ML pipeline constraint (e.g., "use custom preprocessing pipeline")',
                'languages': 'Python'
            },
            {
                'name': '🟨 JavaScript Modern Stack',
                'domain': 'JavaScript and Modern Frameworks',
                'skills': 'full-stack senior developer',
                'focus': 'performance and user experience',
                'constraint': 'framework constraint (e.g., "use React hooks and Context API")',
                'languages': 'JavaScript and/or TypeScript'
            },
            {
                'name': '🟦 Java Enterprise',
                'domain': 'Java Enterprise Applications',
                'skills': 'enterprise architect',
                'focus': 'scalability and maintainability',
                'constraint': 'enterprise pattern requirement (e.g., "use Spring Boot with microservices")',
                'languages': 'Java and SQL'
            },
            {
                'name': '🟩 Mobile Development',
                'domain': 'Mobile App Development',
                'skills': 'mobile development expert',
                'focus': 'cross-platform compatibility',
                'constraint': 'platform constraint (e.g., "use React Native with native modules")',
                'languages': 'React Native and/or Swift/Kotlin'
            },
            {
                'name': '🟥 DevOps Infrastructure',
                'domain': 'DevOps and CI/CD',
                'skills': 'DevOps engineer',
                'focus': 'automation and monitoring',
                'constraint': 'infrastructure as code requirement (e.g., "use Terraform with Docker")',
                'languages': 'Bash scripting and configuration as code'
            },
            {
                'name': '🍳 Cucina e Ricette',
                'domain': 'Cucina e Ricette Italiane',
                'skills': 'chef esperto e food writer',
                'focus': 'ricette tradizionali e tecniche culinarie',
                'constraint': 'vincolo culinario specifico (es. "usa solo ingredienti freschi di stagione" o "seguire il metodo tradizionale")',
                'languages': 'Ricette, tecniche culinarie e descrizioni gastronomiche'
            }
        ]
        
        # Create preset buttons
        for i, preset in enumerate(presets, start=1):
            btn_frame = ttk.Frame(main_frame)
            btn_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5)
            
            btn = ttk.Button(btn_frame, text=preset['name'],
                           command=lambda p=preset: self.load_preset(p, presets_window))
            btn.pack(side=tk.LEFT)
            
            # Info label
            info_text = f"{preset['domain']} | {preset['focus']}"
            ttk.Label(btn_frame, text=info_text, font=('Arial', 8), 
                     foreground='gray').pack(side=tk.LEFT, padx=(10, 0))
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=presets_window.destroy).grid(row=len(presets)+1, column=0, pady=20)
        
        # Center window
        presets_window.update_idletasks()
        x = (presets_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (presets_window.winfo_screenheight() // 2) - (400 // 2)
        presets_window.geometry(f"500x400+{x}+{y}")
    
    def load_preset(self, preset: dict, window):
        """Load preset configuration"""
        self.rag_domain_var.set(preset['domain'])
        self.rag_skill_level_var.set(preset['skills'])
        self.rag_focus_var.set(preset['focus'])
        self.constraint_entry.delete('1.0', tk.END)
        self.constraint_entry.insert('1.0', preset['constraint'])
        self.rag_languages_var.set(preset['languages'])
        
        # Also update config immediately (so it's available even if user doesn't click Save)
        self.config.rag_domain = preset['domain']
        self.config.rag_skill_level = preset['skills']
        self.config.rag_focus = preset['focus']
        self.config.rag_constraint = preset['constraint']
        self.config.rag_languages = preset['languages']
        
        # Update display in main window
        self.update_rag_info_display()
        
        window.destroy()
        messagebox.showinfo("Preset Loaded", f"Preset '{preset['name']}' loaded successfully!\n\nClick 'Save Configuration' to confirm, or start generation directly.")

    def update_rag_info_display(self):
        """Update the RAG configuration info display in main window"""
        # Check if configuration is complete
        is_complete = (self.config.rag_domain and self.config.rag_focus and 
                      self.config.rag_constraint and self.config.rag_skill_level and 
                      self.config.rag_languages)
        
        if is_complete:
            info_text = f"Domain: {self.config.rag_domain} | Focus: {self.config.rag_focus} | Languages: {self.config.rag_languages}"
            # Truncate if too long
            if len(info_text) > 120:
                info_text = info_text[:117] + "..."
            self.rag_info_label.config(text=info_text, foreground='darkblue')
            self.rag_status_label.config(text="✓", foreground='green')
        else:
            self.rag_info_label.config(text="Configuration incomplete - Click 'RAG Config' to configure", foreground='orange')
            self.rag_status_label.config(text="⚠", foreground='orange')
    
    def show_rag_config(self):
        """Show the RAG configuration panel"""
        if self.rag_window is None or not self.rag_window.winfo_exists():
            self.create_rag_config_panel()
        else:
            # Update values if window already exists
            self.rag_domain_var.set(self.config.rag_domain)
            self.rag_focus_var.set(self.config.rag_focus)
            self.rag_skill_level_var.set(self.config.rag_skill_level)
            self.rag_languages_var.set(self.config.rag_languages)
            if hasattr(self, 'constraint_entry'):
                self.constraint_entry.delete('1.0', tk.END)
                self.constraint_entry.insert('1.0', self.config.rag_constraint)
            self.rag_window.lift()
            self.rag_window.focus_force()

    def update_status(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_folder_content(self):
        """Update folder content display"""
        # Clear existing items
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        if not os.path.exists(OUTPUT_DIR):
            self.records_label.config(text="Records: 0")
            return
        
        files = []
        for filename in os.listdir(OUTPUT_DIR):
            if filename.endswith('.json') or filename.endswith('.html'):
                filepath = os.path.join(OUTPUT_DIR, filename)
                stat = os.stat(filepath)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.mtime).strftime("%Y-%m-%d %H:%M:%S")
                files.append((filename, size, modified))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x[2], reverse=True)
        
        # Add to treeview
        for filename, size, modified in files:
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            self.folder_tree.insert("", tk.END, text=filename, values=(size_str, modified))
        
        # Update records count
        self.records_label.config(text=f"Records: {len(files)}")
    
    def open_folder(self):
        """Open the output folder in file explorer"""
        if os.path.exists(OUTPUT_DIR):
            if sys.platform == "win32":
                os.startfile(OUTPUT_DIR)
            elif sys.platform == "darwin":
                os.system(f"open {OUTPUT_DIR}")
            else:
                os.system(f"xdg-open {OUTPUT_DIR}")
    
    def start_generation(self):
        """Start the generation process"""
        # Update config from UI
        self.config.max_records = self.max_records_var.get()
        self.config.max_consecutive_failures = self.max_failures_var.get()
        self.config.delay_between_records = self.delay_var.get()
        self.config.model_x_url = self.model_x_var.get().strip()
        self.config.model_y_url = self.model_y_var.get().strip()
        self.config.web_format = self.web_format_var.get()
        
        # Validate basic config
        if self.config.max_records <= 0:
            messagebox.showerror("Error", "Max records must be greater than 0")
            return
        
        if self.config.delay_between_records < 0:
            messagebox.showerror("Error", "Delay must be non-negative")
            return
        
        # Validate URLs
        if not self.config.model_x_url or not self.config.model_y_url:
            messagebox.showerror("Error", "Both Model X and Model Y URLs must be specified")
            return
        
        # Validate RAG configuration
        if not self.config.rag_domain or not self.config.rag_focus or not self.config.rag_constraint or not self.config.rag_skill_level or not self.config.rag_languages:
            messagebox.showerror("Error", "RAG configuration is incomplete!\n\nPlease configure the RAG settings using the 'RAG Config' button before starting generation.")
            return
        
        # Create generator
        self.generator = RagGenerator(self.config, self.update_status)
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Start generation in separate thread
        self.generation_thread = threading.Thread(target=self.generator.run)
        self.generation_thread.daemon = True
        self.generation_thread.start()
        
        # Start UI update loop
        self.update_generation_status()
    
    def stop_generation(self):
        """Stop the generation process"""
        if self.generator:
            self.generator.running = False
            self.update_status("Stopping generation...")
    
    def update_generation_status(self):
        """Update generation status periodically"""
        if self.generator and self.generation_thread and self.generation_thread.is_alive():
            # Update status
            self.failures_label.config(text=f"Failures: {self.generator.consecutive_failures}")
            
            # Update folder content every 5 seconds
            if hasattr(self, '_last_folder_update'):
                if time.time() - self._last_folder_update > 5:
                    self.update_folder_content()
                    self._last_folder_update = time.time()
            else:
                self._last_folder_update = time.time()
            
            # Schedule next update
            self.root.after(1000, self.update_generation_status)
        else:
            # Generation finished
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_folder_content()
            self.update_status("Generation completed")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # CLI mode
        config = GeneratorConfig()
        generator = RagGenerator(config)
        generator.run()
    else:
        # GUI mode
        root = tk.Tk()
        app = RagGeneratorUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()
