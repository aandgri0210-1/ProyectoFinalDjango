from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin

# Aquí irán tus mixins personalizados
# Vamos a crearlos paso a paso
class OwnerRequiredMixin(LoginRequiredMixin,UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        return obj.creada_por == user or user.is_superuser
