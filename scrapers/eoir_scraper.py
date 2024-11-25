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
        self.attempted_numbers = set()
        self.search_stats = {
            'total_attempts': 0,
            'successful_attempts': 0,
            'last_number': None
        }
    
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
    def search_until_found(self, start_number: str, max_attempts: int = 1000, delay: float = 1.0,
                          progress_callback: Callable = None, stop_flag: Optional[threading.Event] = None) -> Dict:
        """
        Realiza búsquedas continuas hasta encontrar un caso o alcanzar el límite de intentos
        
        Args:
            start_number: Número inicial para comenzar la búsqueda
            max_attempts: Número máximo de intentos
            delay: Tiempo de espera entre intentos en segundos
            progress_callback: Función opcional para reportar progreso
            stop_flag: Event para detener la búsqueda
        """
        try:
            if stop_flag is None:
                stop_flag = threading.Event()
            
            result = {
                'status': 'in_progress',
                'current_number': start_number,
                'attempts': 0,
                'found_case': None,
                'stats': self.search_stats,
                'progress': 0.0,
                'last_error': None
            }
            
            current_number = int(start_number)
            
            for attempt in range(max_attempts):
                if stop_flag.is_set():
                    result['status'] = 'stopped'
                    return result
                
                # Actualizar progreso
                progress = (attempt + 1) / max_attempts * 100
                result.update({
                    'progress': progress,
                    'current_number': str(current_number).zfill(9)
                })
                
                if progress_callback:
                    progress_callback(progress, current_number)
                
                str_number = str(current_number).zfill(9)
                
                # Verificar caché con manejo de errores
                try:
                    cached_result = self.cache.get(str_number)
                    if cached_result and cached_result.get('status') == 'success':
                        result.update({
                            'status': 'found',
                            'found_case': cached_result,
                            'from_cache': True
                        })
                        return result
                except Exception as cache_error:
                    self.search_stats['cache_errors'] += 1
                    result['last_error'] = f"Cache error: {str(cache_error)}"
                
                if str_number not in self.attempted_numbers:
                    self.attempted_numbers.add(str_number)
                    self.search_stats['total_attempts'] += 1
                    self.search_stats['last_number'] = str_number
                    
                    try:
                        search_result = self.search(str_number)
                        result['attempts'] += 1
                        
                        # Guardar en caché con manejo de errores
                        try:
                            self.cache.set(str_number, search_result)
                        except Exception as cache_error:
                            self.search_stats['cache_errors'] += 1
                            result['last_error'] = f"Cache write error: {str(cache_error)}"
                        
                        if search_result['status'] == 'success':
                            self.search_stats['successful_attempts'] += 1
                            result.update({
                                'status': 'found',
                                'found_case': search_result,
                                'from_cache': False
                            })
                            return result
                        elif search_result['status'] == 'not_found':
                            self.search_stats['not_found_attempts'] += 1
                            result['last_error'] = 'Case not found'
                        else:
                            self.search_stats['error_attempts'] += 1
                            result['last_error'] = f"Unknown status: {search_result['status']}"
                        
                    except Exception as search_error:
                        self.search_stats['failed_attempts'] += 1
                        result['last_error'] = f"Search error: {str(search_error)}"
                        if not isinstance(search_error, (ConnectionError, TimeoutError)):
                            time.sleep(delay * 2)  # Increased delay for non-connection errors
                        continue
                    
                    time.sleep(delay)
                current_number += 1
            
            result['status'] = 'max_attempts_reached'
            return result
            
        except Exception as e:
            self.search_stats['critical_errors'] += 1
            return {
                'status': 'error',
                'error': str(e),
                'attempts': result.get('attempts', 0),
                'stats': self.search_stats
            }
    
    def get_search_stats(self) -> Dict:
        """Retorna las estadísticas actuales de búsqueda"""
        return self.search_stats.copy()
    
    def reset_stats(self):
        """Reinicia las estadísticas de búsqueda"""
        self.attempted_numbers.clear()
        self.search_stats = {
            'total_attempts': 0,
            'successful_attempts': 0,
            'last_number': None
        }
            
            def _extract_text(self, element: Optional[BeautifulSoup]) -> Optional[str]:
        """Extrae el texto de un elemento BeautifulSoup"""
        return element.get_text(strip=True) if element else None
        
    def _safe_extract(self, data: Dict, key: str) -> Optional[str]:
        """Extrae de forma segura un valor del diccionario"""
        return data.get(key)

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
