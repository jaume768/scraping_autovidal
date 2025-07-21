# AutoVidal Car Scraper

Este proyecto extrae información de coches usados del sitio web autovidal.es y genera un archivo CSV con los datos de matrícula, marca, modelo y precio.

## Características

- Extrae URLs de coches de múltiples páginas del sitio web
- Obtiene detalles específicos de cada coche (matrícula, marca, modelo, precio)
- Guarda los datos en formato CSV para fácil análisis
- Manejo de errores robusto con reintentos automáticos

## Requisitos del Sistema

- Windows 10/11
- Python 3.7 o superior
- Conexión a Internet

## Instalación y Configuración

### Opción 1: Ejecutar desde Código Fuente (Entorno Virtual)

1. **Abrir PowerShell como Administrador**
   ```powershell
   # Navegar al directorio del proyecto
   cd "c:\Users\jaume\OneDrive\Escritorio\Proyectos"
   ```

2. **Crear y Activar Entorno Virtual**
   ```powershell
   # Crear entorno virtual
   python -m venv autovidal_env
   
   # Activar entorno virtual
   .\autovidal_env\Scripts\Activate.ps1
   ```
   
   **Nota**: Si aparece un error de política de ejecución, ejecuta:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Instalar Dependencias**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Ejecutar el Script**
   ```powershell
   python autovidal_scraper.py
   ```

### Opción 2: Ejecutar el Archivo Ejecutable (.exe)

1. **Descargar el ejecutable** `autovidal_scraper.exe` desde la carpeta `dist/`
2. **Hacer doble clic** en el archivo o ejecutarlo desde la línea de comandos:
   ```cmd
   .\autovidal_scraper.exe
   ```

## Cómo Funciona

El scraper funciona en dos fases:

### Fase 1: Extracción de URLs
- Navega por las páginas paginadas de coches usados
- Extrae las URLs individuales de cada coche
- Guarda las URLs en `car_urls.txt`
- Por defecto procesa 15 páginas (configurable)

### Fase 2: Extracción de Detalles
- Lee las URLs desde `car_urls.txt`
- Visita cada página individual del coche
- Extrae: matrícula, marca, modelo y precio
- Guarda los datos en `coches_autovidal.csv`

## Archivos Generados

- `car_urls.txt`: Lista de URLs de coches extraídas
- `coches_autovidal.csv`: Datos finales con formato: Matricula,Marca,Modelo,Precio

## Configuración Avanzada

### Modificar Número de Páginas
En `autovidal_scraper.py`, línea 54, cambiar el valor de `max_pages`:
```python
def get_all_car_urls(self, max_pages=15):  # Cambiar este número
```

### Modo de Prueba
Para probar con pocos coches, modificar `MAX_CARS_TEST` en la línea 149:
```python
MAX_CARS_TEST = 10  # Cambiar a None para procesar todos
```

## Solución de Problemas

### Error de Política de Ejecución en PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error de Conexión a Internet
- Verificar conexión a internet
- El script tiene reintentos automáticos para errores temporales

### Error de Permisos
- Ejecutar PowerShell como Administrador
- Verificar que no hay antivirus bloqueando el script

### El CSV está Vacío
- Revisar si `car_urls.txt` contiene URLs válidas
- Verificar la conectividad a autovidal.es

## Estructura del Proyecto

```
Proyectos/
├── autovidal_scraper.py      # Script principal
├── requirements.txt          # Dependencias de Python
├── README.md                # Este archivo
├── autovidal_env/           # Entorno virtual (generado)
├── car_urls.txt             # URLs extraídas (generado)
├── coches_autovidal.csv     # Datos finales (generado)
└── dist/                    # Ejecutables (generado)
    └── autovidal_scraper.exe
```

## Dependencias

- `requests`: Para realizar peticiones HTTP
- `beautifulsoup4`: Para parsear HTML
- `lxml`: Parser XML/HTML rápido
- `pyinstaller`: Para generar ejecutables (solo desarrollo)

## Licencia

Este proyecto es para uso educativo y personal. Respeta los términos de uso del sitio web autovidal.es.

## Contacto

Para reportar problemas o sugerir mejoras, contacta con el desarrollador.
