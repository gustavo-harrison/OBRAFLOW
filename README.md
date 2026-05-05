# OBRAFLOW 🏗️

Sistema web desarrollado como proyecto final académico para la gestión administrativa y operativa de obras de construcción.

OBRAFLOW centraliza procesos entre Inspector Técnico de Obras, Empresas Contratistas y Administración del sistema, permitiendo controlar obras, contratos, garantías, trabajadores, actas oficiales y estados de pago en una sola plataforma.

---

# Objetivo del Proyecto

Diseñar e implementar una solución digital funcional, abordable y escalable, enfocada en optimizar la administración documental y operativa de proyectos de construcción.

---

# 👥 Usuarios de Prueba

## 🔐 Administrador del Sistema

- Usuario: `harrison93`
- Contraseña: `Obraflow#123`
- Rol: Administrador

Funciones principales del Administrador:

- Tener acceso completo a la administración del sistema a través de la interfaz de Django

## 👷 Inspector Técnico de Obras

- Usuario: `inspector1`
- Contraseña: `Obraflow#123`
- Rol: Inspector

Funciones principales del inspector:

- Crear y administrar obras
- Gestionar contratos
- Controlar garantías
- Crear Estados de Pago
- Firmar y aprobar EDP
- Emitir actas oficiales
- Supervisar trabajadores
- Generar reportes PDF
- Visualizar dashboard ejecutivo
- Revisar alertas inteligentes

## 🏭 Empresa Contratista

- Usuario: `empresa1`
- Contraseña: `Obraflow#123`
- Rol: Contratista

Funciones principales:

- Visualizar obras asignadas
- Registrar trabajadores
- Subir documentación laboral
- Firmar actas
- Firmar estados de pago
- Revisar dashboard empresa
- Consultar estados de pago
- Descargar documentos PDF

---

# Módulos Implementados

- Gestión de Obras
- Gestión de Contratos
- Garantías Contractuales
- Estados de Pago
- Actas Digitales
- Firmas Digitales
- Gestión de Trabajadores
- Documentación Laboral
- Dashboard Inspector
- Dashboard Empresa
- Alertas Inteligentes
- Reportes PDF

---

# Tecnologías Utilizadas

## Backend

- Python 3
- Django

## Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript

## Base de Datos

- SQLite3

## Librerías

- ReportLab

## Control de Versiones

- Git
- GitHub

---

# Ejecución Local

Comandos para ejecutar el proyecto:

    git clone https://github.com/gustavo-harrison/OBRAFLOW.git
    cd OBRAFLOW
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

Acceso local:

    http://127.0.0.1:8000/

---

# Escalabilidad Futura

El sistema fue desarrollado con una estructura modular, permitiendo futuras mejoras como:

- Calendario de obras
- Contador de días corridos y días hábiles
- Agenda de reuniones
- Integración con Google Calendar
- Notificaciones automáticas
- Libro de obras
- PostgreSQL
- KPIs avanzados
- Firma electrónica avanzada
- Deploy en la nube

---

# Observaciones

Proyecto desarrollado buscando equilibrio entre alcance realista, complejidad técnica y proyección futura.

Se priorizó una solución funcional, ordenada, abordable y adaptable a crecimiento futuro.

---

# Evidencia Visual

Para revisión funcional, utilizar los usuarios de prueba indicados anteriormente.

Se recomienda revisar:

- Dashboard Inspector
- Dashboard Empresa
- Estados de Pago
- Actas Digitales
- Reportes PDF
- Alertas Inteligentes
- Firmas digitales

# Autor

**Harrison Gustavo Guerrero**

Desarrollador de OBRAFLOW.

- Estudiante de Analista Programador Computacional
- Ingeniero Constructor Titulado con más de 5 años de experiencia en el rubro

Proyecto desarrollado de forma integral, considerando análisis, diseño, desarrollo e implementación con enfoque escalable.

