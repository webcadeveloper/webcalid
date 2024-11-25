
README del Proyecto
Dashboard Inteligente para Búsqueda y Gestión de Información
Este proyecto tiene como objetivo proporcionar un sistema interactivo basado en un dashboard que permita a los usuarios y supervisores gestionar, buscar y analizar información relacionada con personas, basándose en números generados. El sistema incluye múltiples iframes para acceder a diversas fuentes de datos, integración con Excel y funcionalidades de llamadas telefónicas.

Características Principales
1. Generación de Números
Genera números aleatorios o secuenciales.
Presenta un listado interactivo con opciones para:
Buscar información basada en un número.
Confirmar o copiar datos directamente.
2. Búsqueda de Información
Motor de búsqueda conectado a diversas fuentes de datos en línea mediante iframes.
Sincronización dinámica entre el número generado y los resultados mostrados en los iframes.
3. Integración con Excel
Posibilidad de exportar los datos obtenidos en un archivo Excel para análisis y seguimiento.
Gestión automatizada de los datos dentro del dashboard.
4. Múltiples Iframes
Panel central con varios iframes configurados para interactuar con herramientas y páginas específicas.
Fácil navegación entre los iframes mediante botones o pestañas.
5. Llamadas Telefónicas
Integración con un servicio de llamadas (como Twilio) para contactar directamente desde el dashboard.
Registro y estado de las llamadas para control administrativo.
6. Panel de Supervisión
Permite a los supervisores ver estadísticas y gestionar los datos obtenidos.
Generación de reportes personalizados.
Tecnologías Utilizadas
Frontend
HTML5 y CSS3 para diseño estático y adaptable.
JavaScript para funcionalidad interactiva y gestión dinámica.
Bootstrap para una interfaz moderna y responsiva.
Backend
Integración con APIs para extracción de datos.
Uso de servicios para llamadas telefónicas y exportación de datos.
Almacenamiento
Soporte para bases de datos (como MongoDB o MySQL) para persistencia de datos procesados.
Requisitos del Sistema
Navegador Moderno:
Compatible con Chrome, Firefox, Edge, entre otros.
Servidor Backend:
Node.js o Python con Flask/Django.
Servicios Adicionales:
Cuenta en Twilio (para llamadas).
Acceso a APIs de búsqueda (si están disponibles).
Instrucciones de Uso
Usuario Final
Accede al dashboard.
Genera un número o selecciona uno existente.
Interactúa con los iframes para buscar información relevante.
Exporta los datos a Excel o realiza una llamada directamente.
Supervisor
Inicia sesión en el panel de supervisión.
Revisa estadísticas generales.
Genera reportes o administra la información exportada.
Próximos Pasos
Mejorar la sincronización entre los números generados y las fuentes de datos en los iframes.
Implementar autenticación de usuarios y roles.
Agregar soporte multilingüe.