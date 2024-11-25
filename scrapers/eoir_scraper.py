import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Optional
import json

class EOIRScraper:
    BASE_URL = "https://acis.eoir.justice.gov/es"
    SEARCH_URL = "https://acis.eoir.justice.gov/es/buscar"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search(self, number: str, max_retries: int = 3) -> Dict:
        """
        Buscar un número de caso en el sistema EOIR
        """
        # Initialize result dictionary
        result = {
            'status': 'error',
            'data': None,
            'error': None
        }

        try:
            # Make the search request with proper Spanish parameters
            for attempt in range(max_retries):
                try:
                    response = self.session.post(
                        self.SEARCH_URL,
                        data={
                            'numero_caso': number,
                            'idioma': 'es'
                        },
                        timeout=10
                    )
                    
                    # Handle different response status codes
                    if response.status_code == 404:
                        result['status'] = 'not_found'
                        result['error'] = 'Caso no encontrado'
                        return result
                    
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        result['status'] = 'not_found'
                        result['error'] = 'Caso no encontrado'
                        return result
                    elif attempt == max_retries - 1:
                        raise e
                except (requests.RequestException, requests.Timeout) as e:
                    if attempt == max_retries - 1:
                        result['error'] = f'Error de conexión: {str(e)}'
                        return result
                    time.sleep(1)
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract case information
            case_info = self._extract_case_info(soup)
            
            if case_info:
                result['status'] = 'success'
                result['data'] = case_info
            else:
                result['status'] = 'not_found'
                result['error'] = 'No se encontró información del caso'
            
            return result
            
        except Exception as e:
            result['error'] = f'Error inesperado: {str(e)}'
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'data': None,
                'error': str(e)
            }
    
    def _extract_case_info(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract case information from the parsed HTML
        """
        try:
            # Find the main case information container
            case_container = soup.find('div', {'class': 'case-information'})
            
            if not case_container:
                return None
                
            # Extract relevant information
            info = {
                'numero_caso': self._safe_extract(case_container, 'numero-caso'),
                'tipo_caso': self._safe_extract(case_container, 'tipo-caso'),
                'estado': self._safe_extract(case_container, 'estado'),
                'ubicacion': self._safe_extract(case_container, 'ubicacion'),
                'fecha_presentacion': self._safe_extract(case_container, 'fecha-presentacion'),
                'ultima_actualizacion': self._safe_extract(case_container, 'ultima-actualizacion'),
                'informacion_personal': self._extract_personal_info(case_container)
            }
            
            return info
            
        except Exception:
            return None
    
    def _safe_extract(self, container: BeautifulSoup, class_name: str) -> Optional[str]:
        """
        Safely extract text from an element
        """
        element = container.find(class_=class_name)
    def _extract_personal_info(self, container: BeautifulSoup) -> Optional[Dict]:
        """
        Extract personal information when available
        """
        try:
            personal_info = container.find('div', {'class': 'personal-information'})
            if not personal_info:
                return None
                
            info = {
                'nombre': self._safe_extract(personal_info, 'nombre'),
                'apellidos': self._safe_extract(personal_info, 'apellidos'),
                'fecha_nacimiento': self._safe_extract(personal_info, 'fecha-nacimiento'),
                'nacionalidad': self._safe_extract(personal_info, 'nacionalidad'),
                'idioma': self._safe_extract(personal_info, 'idioma-preferido'),
                'direccion': self._safe_extract(personal_info, 'direccion')
            }
            
            return {k: v for k, v in info.items() if v is not None}
            
        except Exception:
            return None

        return element.get_text(strip=True) if element else None

# Cache implementation
class EOIRCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached result if it exists and is not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < 3600:  # 1 hour cache
                return entry['data']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Dict):
        """Cache the result"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest = min(self.cache.items(), key=lambda x: x[1]['timestamp'])
            del self.cache[oldest[0]]
        
        self.cache[key] = {
            'data': value,
            'timestamp': time.time()
        }
