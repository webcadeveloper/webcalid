import requests
from bs4 import BeautifulSoup

class EOIRScraper:
    BASE_URL = "https://acis.eoir.justice.gov/en/"

    def __init__(self):
        self.session = requests.Session()

    def search(self, number):
        result = {'status': 'error', 'data': None}

        if not number.isdigit() or len(number) != 9:
            result['error'] = 'Formato de número de caso inválido. Debe ser un número de 9 dígitos.'
            return result

        try:
            response = self.session.get(self.BASE_URL, params={'caseNumber': number}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            error_message = soup.find('div', class_='error-message')
            if error_message and "No case information found" in error_message.text:
                result['status'] = 'not_found'
                return result

            case_info = self._extract_case_info(soup)
            if case_info:
                result['status'] = 'success'
                result['data'] = case_info
            else:
                result['status'] = 'not_found'
            return result

        except requests.RequestException as e:
            result['error'] = f'Error de conexión: {str(e)}'
            return result

    def _extract_case_info(self, soup):
        # Implementa la lógica para extraer información del caso aquí
        case_info = {}
        # Ejemplo de extracción de datos...
        return case_info