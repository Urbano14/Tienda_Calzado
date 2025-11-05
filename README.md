Tienda de Calzado

Proyecto académico desarrollado en Django para la asignatura de Planificación y Gestión de Proyectos Informáticos.


Guía rápida para el equipo
1. Clonar el proyecto
git clone https://github.com/Urbano14/Tienda_Calzado.git
cd Tienda_Calzado

2. Crear entorno virtual e instalar dependencias
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

3. Ejecutar el servidor local
python manage.py migrate
python manage.py runserver


Abrir en el navegador:
http://127.0.0.1:8000/

4. Flujo de trabajo con Git

Crear una nueva rama para trabajar:

git checkout -b feature/iteracion-1


Guardar los cambios:

git add .
git commit -m "feat: descripcion breve del cambio"


Subirlos al repositorio remoto:

git push origin feature/iteracion-1


En GitHub, abrir un Pull Request hacia la rama main.

5. Actualizar el proyecto

Antes de empezar una nueva tarea o sesión de trabajo:

git checkout main
git pull origin main

6. Normas básicas del equipo

No subir .venv/, db.sqlite3 ni archivos temporales (ya están en .gitignore).

Realizar commits pequeños, claros y frecuentes.

Solo se fusiona a main código que funcione correctamente.

Utilizar las issues de GitHub para seguir las tareas de cada iteración.
