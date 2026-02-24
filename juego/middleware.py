import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class LogAccesosPersonajesMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        
        path = request.path
        
        if '/personajes/' in path:
            try:
                parts = path.split('/')
                if 'personajes' in parts:
                    idx = parts.index('personajes')
                    if len(parts) > idx + 1 and parts[idx + 1].isdigit():
                        personaje_id = parts[idx + 1]
                        
                        accion = 'ver'
                        if 'editar' in path:
                            accion = 'editar'
                        elif 'inventario' in path:
                            accion = 'inventario'
                        elif 'eliminar' in path:
                            accion = 'eliminar'
                        
                        logger.info(
                            f"Acceso - Usuario: {request.user.username}, "
                            f"Personaje: {personaje_id}, Acción: {accion}"
                        )
            except (ValueError, IndexError):
                pass
        
        return None
    
    def process_response(self, request, response):
        if response.status_code == 403 and '/personajes/' in request.path:
            if request.user.is_authenticated:
                logger.warning(f"Acceso denegado - Usuario: {request.user.username}")
        
        return response