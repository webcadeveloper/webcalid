import requests
import time
from typing import Dict, Optional
import json

class PDLCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < 3600:  # 1 hour cache
                return entry['data']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Dict):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1]['timestamp'])
            del self.cache[oldest[0]]
        
        self.cache[key] = {
            'data': value,
            'timestamp': time.time()
        }

class PDLScraper:
    BASE_URL = "https://api.peopledatalabs.com/v5/person/search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.cache = PDLCache()
        self.search_stats = {
            'total_attempts': 0,
            'successful_attempts': 0,
            'not_found_attempts': 0,
            'failed_attempts': 0,
            'error_attempts': 0,
            'cache_errors': 0,
            'last_number': None,
            'last_error': None
        }

    def validate_api_key(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 20)

    def search(self, number: str) -> Dict:
        if not self.validate_api_key():
            return {
                'status': 'error',
                'error': 'API key not configured'
            }

        self.search_stats['total_attempts'] += 1
        self.search_stats['last_number'] = number

        # Check cache first
        cached_result = self._check_cache(number)
        if cached_result:
            self.search_stats['successful_attempts'] += 1
            return cached_result

        try:
            headers = {
                'X-Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            # Search using the number in various fields
            payload = {
                'query': {
                    'must': [
                        {'any': [
                            {'phone_numbers': number},
                            {'id': number}
                        ]}
                    ]
                }
            }

            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('total') > 0:
                    result = {
                        'status': 'success',
                        'data': data['data'][0]
                    }
                    self.search_stats['successful_attempts'] += 1
                else:
                    result = {
                        'status': 'not_found',
                        'error': 'No matches found'
                    }
                    self.search_stats['not_found_attempts'] += 1
            elif response.status_code == 401:
                result = {
                    'status': 'error',
                    'error': 'Invalid API key'
                }
                self.search_stats['error_attempts'] += 1
            else:
                result = {
                    'status': 'error',
                    'error': f'API error: {response.status_code}'
                }
                self.search_stats['failed_attempts'] += 1

            # Cache successful results
            if result['status'] == 'success':
                self._cache_result(number, result)

            return result

        except Exception as e:
            self.search_stats['error_attempts'] += 1
            self.search_stats['last_error'] = str(e)
            return {
                'status': 'error',
                'error': f'Request failed: {str(e)}'
            }

    def _check_cache(self, number: str) -> Optional[Dict]:
        try:
            return self.cache.get(number)
        except Exception as e:
            self.search_stats['cache_errors'] += 1
            self.search_stats['last_error'] = f'Cache error: {str(e)}'
            return None

    def _cache_result(self, number: str, result: Dict):
        try:
            self.cache.set(number, result)
        except Exception as e:
            self.search_stats['cache_errors'] += 1
            self.search_stats['last_error'] = f'Cache write error: {str(e)}'

    def get_stats(self) -> Dict:
        return self.search_stats.copy()
