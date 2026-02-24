from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class OwnerRequiredMixin(UserPassesTestMixin):
    
    def test_func(self):
        obj = self.get_object()
        if hasattr(obj, 'personaje'):
            return obj.personaje.usuario == self.request.user
        if hasattr(obj, 'usuario'):
            return obj.usuario == self.request.user
        return False
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("No tienes permiso para acceder a este recurso.")
        return super().handle_no_permission()


class SetLastCharacterMixin:
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        obj = self.get_object()
        personaje_id = obj.id if hasattr(obj, 'usuario') else getattr(obj, 'personaje_id', None)
        if personaje_id:
            request.session['ultimo_personaje_id'] = personaje_id
        return response
