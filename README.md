
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Status](https://img.shields.io/badge/status-production--ready-success)
![Automation](https://img.shields.io/badge/type-automation-purple)

![Made With Love](https://img.shields.io/badge/made%20with-%E2%9D%A4-red)


# PIPELINE DE CLONACIÓN Y ADAPTACIÓN HTML - ARTÍCULO 73


## DESCRIPCIÓN

Este proyecto implementa un pipeline automatizado para la clonación, transformación y normalización de páginas HTML del Artículo 73 de la Ley General de Contabilidad Gubernamental.

El sistema permite generar una nueva estructura trimestral a partir de una plantilla base, adaptando automáticamente nombres de archivos, enlaces, breadcrumbs, títulos, responsables y vínculos de descarga.

Está diseñado para automatizar procesos repetitivos de actualización de contenido web institucional, reduciendo significativamente el tiempo de trabajo manual.


## FUNCIONALIDADES PRINCIPALES

Clonación de estructura HTML por entidad federativa  
Transformación automática de trimestre y año  
Normalización de nombres de archivos  
Relink de subpáginas  
Actualización de títulos (`<title>`)  
Corrección de encabezados (`<h1>`)  
Generación dinámica de breadcrumbs  
Vinculación automática de archivos ZIP  
Copia de archivos desde fuente externa  
Generación de página principal del trimestre  
Actualización de responsables institucionales  
Generación de reporte CSV de inconsistencias  


## TECNOLOGÍAS UTILIZADAS

Python  
pathlib  
dataclasses  
regex (re)  
shutil  
csv  
unicodedata  


## FLUJO DEL PROCESO

1. Lectura de plantilla base  
2. Clonación de estructura HTML  
3. Reemplazo de trimestre y año  
4. Relink de subpáginas  
5. Copia de archivos ZIP  
6. Vinculación de descargas  
7. Generación de página principal  
8. Actualización de breadcrumbs  
9. Normalización de títulos y encabezados  
10. Actualización de responsables  
11. Generación de resumen del proceso  


## ESTRUCTURA REQUERIDA

El script requiere una carpeta plantilla con HTMLs base:

plantilla_ejemplo/
├── segundo_trimestre_2026.html
├── entidad_1/
│   ├── archivos/
│   ├── entidad_1_2t_2026.html
│   ├── analitico_de_plazas_2t_2026_e01.html
│   └── ...
├── entidad_2/
│   ├── archivos/
│   └── ...


## CONFIGURACIÓN

Modificar el panel de configuración en el script:

"SOURCE_ROOT": Path(r"C:\RUTA\PLANTILLA"),
"DEST_ROOT": Path(r"C:\RUTA\SALIDA"),
"PLANTILLA_TRIMESTRE": Path(r"C:\RUTA\PLANTILLA\archivo.html"),
"ZIP_SOURCE_ROOT": Path(r"C:\RUTA\ZIPs"),


## DEPENDENCIAS

No requiere librerías externas.


## NOTAS IMPORTANTES

El script depende de la estructura HTML de la plantilla
Se recomienda usar datos de prueba o anonimizar contenido
No incluir rutas reales en repositorios públicos
El pipeline está diseñado para procesamiento batch


## CASO DE USO

Automatización de actualización de portales institucionales
Gestión de información pública estructurada
Reducción de carga operativa en procesos repetitivos
Estandarización de contenido web


AUTOR:
Jorge Fernando Ortiz Bravo
