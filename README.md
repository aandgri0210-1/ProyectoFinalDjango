# ProyectoFinalDjango

Aplicación web RPG desarrollada con Django para gestionar personajes, inventario, zonas, enemigos/jefes, combates por turnos y estadísticas, con base de datos PostgreSQL y ejecución mediante Docker.

## 1) Descripción breve y funcionalidades principales

El proyecto permite que cada usuario gestione su progresión dentro de un entorno de juego:

- Autenticación: registro, inicio y cierre de sesión.
- Personajes: crear, listar, ver detalle, editar/eliminar (según permisos).
- Inventario: agregar objetos, equipar/desequipar y usar consumibles.
- Mundo: administración de zonas, enemigos y jefes.
- Combates: sistema por turnos con acciones (`atacar`, `huir`, `usar consumible`).
- Estadísticas: vista personal para usuarios normales y vista global para administradores.
- Preferencias: cambio de tema claro/oscuro mediante cookies.

## Tecnologías principales

- Python
- Django
- PostgreSQL
- Docker
 
## 2) Instalación y ejecución (con Docker)

1. Construir y levantar servicios:

   ```bash
   docker compose up --build -d
   ```

1. Detener servicios:

   ```bash
   docker compose down
   ```

## 3) Credenciales de prueba / Superusuario

### Credenciales de prueba (si existen en la base actual)

- Usuario: `admin`
- Contraseña: `admin`

### Crear superusuario (alternativa recomendada)

Si no existe usuario administrador en la base de datos actual:

```bash
python manage.py createsuperuser
```

Con Docker:

```bash
docker compose exec web python manage.py createsuperuser
```

## 4) Flujo de trabajo en GitHub

### Organización del equipo

- **Victor Chacón Cintado**:
  - Módulo de personajes.
  - Módulo de inventario.
- **Juan Antonio Castro Ruíz**:
  - Módulo de enemigos.
  - Módulo de zonas.
  - Módulo de jefes.
- **Alejandro Andrada Grimaldi**:
  - Módulo de combates.
  - Módulo de estadísticas.
  - Dockerización y despliegue local con PostgreSQL.

### Flujo aplicado

- Repositorio central en GitHub para integración de cambios.
- Commits por bloques funcionales (combate, estadísticas, dockerización, estilos, navegación, etc.).
- Integración principal en la rama `master` del repositorio actual.
- Para siguientes iteraciones, se recomienda mantener un flujo con ramas por funcionalidad (`feature/*`) y revisión mediante Pull Request antes de merge.

## 5) Mapa de trazabilidad (requisitos técnicos)

| Requisito técnico | Dónde se cumple |
|---|---|
| Autenticación (login/registro/logout) | `juego/views.py`, `juego/urls.py`, plantillas `inicio-sesion.html` y `registro.html` |
| Gestión de personajes | `juego/models.py` (`Personaje`), `juego/forms.py` (`PersonajeForm`), vistas y templates en `juego/templates/personajes/` |
| Gestión de inventario y consumibles | `juego/models.py` (`Inventario`, `Objeto`), vistas de inventario en `juego/views.py`, templates en `juego/templates/inventario/` |
| Zonas, enemigos y jefes | `juego/models.py` (`Zona`, `Enemigo`), formularios `ZonaForm` y `EnemigoForm`, vistas CRUD y templates en `juego/templates/juego/` |
| Combate por turnos | `juego/views.py` (`CombateCreateView`, `CombateArenaView`), `juego/forms.py` (`CombateForm`), templates `combate_form.html` y `combate_arena.html` |
| Estadísticas por rol (usuario/admin) | `juego/views.py` (`estadisticas_view`), template `juego/templates/juego/estadisticas.html` |
| Persistencia en PostgreSQL | `ProyectoFinalDjango/settings.py` (config `DATABASES` por `POSTGRES_*`) |
| Dockerización | `Dockerfile`, `docker-compose.yml`, `.dockerignore` |
| Navegación y estilo global | `juego/templates/base.html`, `juego/static/css/basic.css` |
| Tema claro/oscuro por cookies | `juego/views.py` (`fijar_tema`, `cambiar_tema_view`), `juego/templates/base.html`, `juego/static/css/basic.css` |

