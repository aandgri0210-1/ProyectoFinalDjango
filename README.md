# ProyectoFinalDjango

Aplicación web desarrollada con Django para gestionar un juego tipo RPG con personajes, inventario, zonas, enemigos, jefes, combates por turnos y estadísticas.

## Descripción general

El sistema permite a cada usuario crear y gestionar su personaje, administrar su inventario de objetos, combatir contra enemigos de distintas zonas y revisar estadísticas del juego. La aplicación está dockerizada y configurada para trabajar con PostgreSQL.

## Tecnologías principales

- Python
- Django
- PostgreSQL
- Docker

## Funcionalidades principales

- Autenticación de usuarios (registro, inicio y cierre de sesión).
- Gestión de personajes:
  - Crear, listar, ver detalle, editar/eliminar (según permisos).
- Gestión de inventario:
  - Ver inventario por personaje.
  - Agregar objetos.
  - Equipar/desequipar.
  - Usar consumibles.
- Catálogo de contenido del mundo:
  - Zonas.
  - Enemigos.
  - Jefes.
- Combates:
  - Flujo de combate por turnos.
  - Acciones en combate (atacar, huir, usar consumible).
  - Registro de resultados y EXP ganada.
- Estadísticas:
  - Vista personalizada para usuario normal.
  - Vista global para administrador.

## Estructura del proyecto

- `ProyectoFinalDjango/`: configuración principal de Django.
- `juego/`: app principal con modelos, vistas, formularios, URLs y templates.
- `docker-compose.yml`: orquestación de servicios `web` + `db`.
- `Dockerfile`: imagen de la aplicación Django.

## Ejecución con Docker (recomendado)

1. Construir y levantar servicios:

   ```bash
   docker compose up --build -d
   ```

1. Detener servicios:

   ```bash
   docker compose down
   ```

## Base de datos

La aplicación está preparada para PostgreSQL dentro de Docker Compose.

URL de conexión interna (servicio `web` -> servicio `db`):

`postgresql://proyectofinaluser:proyectofinalpass@db:5432/proyectofinaldb`

## Roles y permisos (resumen)

- Usuario normal:
  - Gestiona sus propios personajes e inventario.
  - Ve sus estadísticas.
- Administrador:
  - Puede gestionar contenido global (zonas/enemigos, según configuración de permisos).
  - Ve estadísticas globales con listado completo de personajes.

## Responsables por módulos

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
