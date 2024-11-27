import psutil
import requests
import websockets
import asyncio
import logging
from datetime import datetime
import json
from typing import Dict, Any, Optional
import os
import socket
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceMonitor:
    def __init__(self):
        self.services = {
            'streamlit': {
                'port': 8502,
                'type': 'http',
                'url': 'http://0.0.0.0:8502/_stcore/health',
                'name': 'Streamlit Dashboard',
                'expected_status': 200
            },
            'api': {
                'port': 3000,
                'type': 'http',
                'url': 'http://0.0.0.0:3000/health',
                'name': 'API REST Server',
                'expected_status': 200
            },
            'webrtc': {
                'port': 3001,
                'type': 'websocket',
                'url': 'ws://0.0.0.0:3001',
                'name': 'WebRTC Signaling',
                'ping_timeout': 5
            }
        }
        self.metrics: Dict[str, Any] = {}
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.last_check: Dict[str, datetime] = {}

    async def check_port(self, port: int) -> bool:
        """Check if a port is in use with enhanced error handling"""
        try:
            # First check using psutil
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True

            # Additional check using socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            return result == 0
        except Exception as e:
            logger.error(f"Error checking port {port}: {str(e)}")
            return False

    async def check_http_service(self, service_name: str, service_info: Dict) -> Dict[str, Any]:
        """Check health of HTTP-based services with timeout and retry logic"""
        retries = 2
        timeout = 5
        
        for attempt in range(retries):
            try:
                start_time = datetime.now()
                async with asyncio.timeout(timeout):
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        self._executor,
                        lambda: requests.get(service_info['url'], timeout=timeout)
                    )
                response_time = (datetime.now() - start_time).total_seconds() * 1000

                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        status = health_data.get('status', 'healthy')
                    except:
                        status = 'healthy'
                else:
                    status = 'unhealthy'

                return {
                    'status': status,
                    'response_time': response_time,
                    'last_check': datetime.now().isoformat(),
                    'error': None if status == 'healthy' else f"HTTP {response.status_code}"
                }
            except asyncio.TimeoutError:
                error_msg = f"Timeout after {timeout}s on attempt {attempt + 1}/{retries}"
                logger.warning(f"{service_info['name']}: {error_msg}")
                if attempt == retries - 1:
                    return self._create_error_metric(error_msg)
            except Exception as e:
                error_msg = f"Error on attempt {attempt + 1}/{retries}: {str(e)}"
                logger.error(f"{service_info['name']}: {error_msg}")
                if attempt == retries - 1:
                    return self._create_error_metric(error_msg)

    async def check_websocket_service(self, service_name: str, service_info: Dict) -> Dict[str, Any]:
        """Check health of WebSocket services with enhanced error handling"""
        try:
            start_time = datetime.now()
            async with asyncio.timeout(5):
                async with websockets.connect(service_info['url'], timeout=5) as websocket:
                    try:
                        await websocket.ping()
                        await websocket.pong()
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        return {
                            'status': 'healthy',
                            'response_time': response_time,
                            'last_check': datetime.now().isoformat(),
                            'error': None
                        }
                    except Exception as e:
                        return self._create_error_metric(f"WebSocket communication error: {str(e)}")
        except asyncio.TimeoutError:
            return self._create_error_metric("WebSocket connection timeout")
        except Exception as e:
            return self._create_error_metric(f"WebSocket connection error: {str(e)}")

    def _create_error_metric(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error metric"""
        return {
            'status': 'unhealthy',
            'response_time': None,
            'last_check': datetime.now().isoformat(),
            'error': error_message
        }

    async def monitor_services(self) -> Dict[str, Any]:
        """Monitor all services with concurrent execution and enhanced error handling"""
        tasks = []
        
        for service_name, service_info in self.services.items():
            # Check port first
            port_active = await self.check_port(service_info['port'])
            if not port_active:
                self.metrics[service_name] = self._create_error_metric(
                    f"Puerto {service_info['port']} no está activo"
                )
                continue

            # Create monitoring task based on service type
            if service_info['type'] == 'http':
                task = self.check_http_service(service_name, service_info)
            else:  # websocket
                task = self.check_websocket_service(service_name, service_info)
            
            tasks.append(task)

        # Execute all monitoring tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update metrics with results
            for service_name, result in zip(
                [s for s, i in self.services.items() if await self.check_port(i['port'])],
                results
            ):
                if isinstance(result, Exception):
                    self.metrics[service_name] = self._create_error_metric(str(result))
                else:
                    self.metrics[service_name] = result
                    
        except Exception as e:
            logger.error(f"Error monitoring services: {str(e)}")
            
        return self.metrics

    def get_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics"""
        return self.metrics

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific service"""
        return self.metrics.get(service_name)

    def get_overall_health(self) -> str:
        """Get overall system health status with warning state"""
        if not self.metrics:
            return 'unknown'
        
        status_counts = {
            'healthy': 0,
            'unhealthy': 0,
            'unknown': 0
        }
        
        for metric in self.metrics.values():
            status = metric['status'].lower()
            status_counts[status if status in status_counts else 'unknown'] += 1
            
        if status_counts['unhealthy'] > 0:
            return 'unhealthy'
        elif status_counts['unknown'] > 0 or status_counts['healthy'] < len(self.services):
            return 'warning'
        else:
            return 'healthy'

# Singleton instance
monitor = ServiceMonitor()
