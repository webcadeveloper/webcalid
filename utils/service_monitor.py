import psutil
import requests
import websockets
import asyncio
import logging
from datetime import datetime
import json
from typing import Dict, Any, Optional
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceMonitor:
    def __init__(self):
        self.services = {
            'streamlit': {'port': 8502, 'type': 'http', 'url': 'http://0.0.0.0:8502/_stcore/health'},
            'api': {'port': 3000, 'type': 'http', 'url': 'http://0.0.0.0:3000/health'},
            'webrtc': {'port': 3001, 'type': 'websocket', 'url': 'ws://0.0.0.0:3001'}
        }
        self.metrics: Dict[str, Any] = {}

    async def check_http_service(self, service_name: str, service_info: Dict) -> Dict[str, Any]:
        """Check health of HTTP-based services"""
        try:
            start_time = datetime.now()
            response = requests.get(service_info['url'], timeout=5)
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response_time,
                'last_check': datetime.now().isoformat(),
                'error': None if response.status_code == 200 else f"HTTP {response.status_code}"
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': None,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }

    async def check_websocket_service(self, service_name: str, service_info: Dict) -> Dict[str, Any]:
        """Check health of WebSocket services"""
        try:
            start_time = datetime.now()
            async with websockets.connect(service_info['url'], timeout=5):
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'last_check': datetime.now().isoformat(),
                    'error': None
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': None,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }

    async def check_port(self, port: int) -> bool:
        """Check if a port is in use"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            return False

    async def monitor_services(self) -> Dict[str, Any]:
        """Monitor all services and collect metrics"""
        for service_name, service_info in self.services.items():
            # Check port first
            port_active = await self.check_port(service_info['port'])
            if not port_active:
                self.metrics[service_name] = {
                    'status': 'down',
                    'response_time': None,
                    'last_check': datetime.now().isoformat(),
                    'error': f"Port {service_info['port']} is not active"
                }
                continue

            # Check service health
            if service_info['type'] == 'http':
                self.metrics[service_name] = await self.check_http_service(service_name, service_info)
            else:  # websocket
                self.metrics[service_name] = await self.check_websocket_service(service_name, service_info)

        return self.metrics

    def get_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics"""
        return self.metrics

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific service"""
        return self.metrics.get(service_name)

    def get_overall_health(self) -> str:
        """Get overall system health status"""
        if not self.metrics:
            return 'unknown'
        
        return 'healthy' if all(
            metric['status'] == 'healthy' 
            for metric in self.metrics.values()
        ) else 'unhealthy'

# Singleton instance
monitor = ServiceMonitor()
