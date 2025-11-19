Tienda de Calzado

Proyecto académico en Django para la asignatura de Planificación y Gestión de Proyectos Informáticos.

Guía rápida
1) Clonar el proyecto
- `git clone https://github.com/Urbano14/Tienda_Calzado.git`
- `cd Tienda_Calzado`

2) Entorno y dependencias
- `python -m venv .venv`
- `.\.venv\Scripts\Activate.ps1`
- `pip install -r requirements.txt`

3) Ejecutar el servidor local
- `python manage.py migrate`
- `python manage.py loaddata productos`
- `python manage.py runserver`

Rutas disponibles
- Listado HTML de productos: http://127.0.0.1:8000/productos/
- Detalle de producto: http://127.0.0.1:8000/productos/<id>/
- Carrito de compra: http://127.0.0.1:8000/carrito/
- API REST - Productos: http://127.0.0.1:8000/api/productos/
- API REST - Categorias: http://127.0.0.1:8000/api/categorias/
- Panel de administración: http://127.0.0.1:8000/admin/

Testing
- Ejecutar toda la suite: `python manage.py test`
- Cubrimos: modelos y vistas/API de productos (stock, imagen destacada, precio vigente) y flujos del carrito (stock general y por talla, uso de precio_oferta, ajustes de cantidad y avisos).
- Antes de probar manualmente, arranca el server con `python manage.py runserver` y usa las rutas de arriba.

Flujo Git sugerido
- Crear rama: `git checkout -b feature/lo-que-sea`
- Guardar cambios: `git add . && git commit -m "feat: descripcion breve"`
- Subir: `git push origin feature/lo-que-sea` y abrir PR hacia main.

Normas rápidas
- No subir `.venv/`, `db.sqlite3` ni archivos temporales (ya están en `.gitignore`).
- Commits pequeños y claros; solo se fusiona a `main` código que funcione.
- Describir y seguir tareas en issues de GitHub.
