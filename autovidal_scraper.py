import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin

class AutoVidalScraper:
    def __init__(self):
        self.base_url = "https://autovidal.es"
        self.session = requests.Session()
        # Headers para evitar ser bloqueado
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.car_urls = []

    def get_car_urls_from_page(self, page_url):
        """Extrae las URLs de los coches de una página específica"""
        try:
            print(f"Scrapeando página: {page_url}")
            response = self.session.get(page_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar todos los div de vehículos
            vehicle_divs = soup.find_all('div', class_='dpdsh-storefront__vehicle')
            
            urls_found = []
            for div in vehicle_divs:
                # Buscar el enlace del vehículo
                link = div.find('a', href=True)
                if link and '/vehiculo/' in link['href']:
                    full_url = urljoin(self.base_url, link['href'])
                    urls_found.append(full_url)
                    print(f"  Encontrado coche: {full_url}")
            
            print(f"  Total coches encontrados en esta página: {len(urls_found)}")
            return urls_found
            
        except requests.RequestException as e:
            print(f"Error al acceder a {page_url}: {e}")
            return []
        except Exception as e:
            print(f"Error inesperado al procesar {page_url}: {e}")
            return []

    def get_all_car_urls(self, max_pages=15):
        """Obtiene todas las URLs de coches navegando por las páginas paginadas"""
        print("=== INICIANDO EXTRACCIÓN DE URLS DE COCHES ===")
        
        # Empezar con la primera página
        page = 1
        base_list_url = "https://autovidal.es/coches-usados"
        
        while page <= max_pages:
            if page == 1:
                page_url = base_list_url
            else:
                page_url = f"{base_list_url}/page/{page}"
            
            urls_from_page = self.get_car_urls_from_page(page_url)
            
            if not urls_from_page:
                print(f"No se encontraron más coches en la página {page}. Terminando.")
                break
            
            self.car_urls.extend(urls_from_page)
            page += 1
            
            # Pausa entre páginas para ser respetuosos
            time.sleep(2)
        
        # Eliminar duplicados
        self.car_urls = list(set(self.car_urls))
        print(f"\n=== RESUMEN ===")
        print(f"Total de URLs únicas encontradas: {len(self.car_urls)}")
        return self.car_urls

    def get_car_details(self, car_url):
        """Extrae los detalles completos de un coche desde su página individual"""
        try:
            print(f"Extrayendo detalles de: {car_url}")
            response = self.session.get(car_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Inicializar datos
            car_data = {
                'matricula': 'N/A',
                'marca': 'N/A', 
                'modelo': 'N/A',
                'precio': 'N/A'
            }
            
            # MÉTODO 1: Intentar extraer de los campos hidden del formulario (más confiable)
            hidden_inputs = soup.find_all('input', {'type': 'hidden'})
            for input_elem in hidden_inputs:
                name = input_elem.get('name', '')
                value = input_elem.get('value', '')
                
                if name == 'matricula' and value:
                    car_data['matricula'] = value.strip()
                elif name == 'marca' and value:
                    car_data['marca'] = value.strip()
                elif name == 'modelo' and value:
                    car_data['modelo'] = value.strip() 
                elif name == 'precio' and value:
                    car_data['precio'] = value.strip()
            
            # MÉTODO 2: Si no encontramos datos en los hidden, usar los elementos HTML
            if car_data['matricula'] == 'N/A':
                matricula_elem = soup.find('span', {'data-postname': 'number_plate'})
                if matricula_elem:
                    car_data['matricula'] = matricula_elem.get_text(strip=True)
            
            if car_data['marca'] == 'N/A':
                # Buscar en la sección de datos técnicos
                marca_sections = soup.find_all('div', class_='dpdsh-taxonomy__container')
                for section in marca_sections:
                    prev_text = section.find_previous('div', class_='ct-text-block')
                    if prev_text and 'Marca:' in prev_text.get_text():
                        car_data['marca'] = section.get_text(strip=True)
                        break
            
            if car_data['modelo'] == 'N/A':
                # Buscar en la sección de datos técnicos
                modelo_sections = soup.find_all('div', class_='dpdsh-taxonomy__container')
                for section in modelo_sections:
                    prev_text = section.find_previous('div', class_='ct-text-block')
                    if prev_text and 'Modelo:' in prev_text.get_text():
                        car_data['modelo'] = section.get_text(strip=True)
                        break
            
            # Si aún no tenemos precio, intentar extraerlo de otros lugares
            if car_data['precio'] == 'N/A':
                # Buscar precio en la página
                precio_patterns = [
                    r'Precio[^:]*:?\s*([\d.,]+)\s*€',
                    r'([\d.,]+)\s*€',
                ]
                page_text = soup.get_text()
                for pattern in precio_patterns:
                    precio_match = re.search(pattern, page_text, re.IGNORECASE)
                    if precio_match:
                        car_data['precio'] = precio_match.group(1).replace('.', '').replace(',', '')
                        break
            
            print(f"  ✓ Matrícula: {car_data['matricula']}")
            print(f"  ✓ Marca: {car_data['marca']}")
            print(f"  ✓ Modelo: {car_data['modelo']}")
            print(f"  ✓ Precio: {car_data['precio']}")
            
            return car_data
            
        except requests.RequestException as e:
            print(f"  ✗ Error de conexión con {car_url}: {e}")
            return None
        except Exception as e:
            print(f"  ✗ Error inesperado al procesar {car_url}: {e}")
            return None
    
    def scrape_all_cars_details(self, urls_file="car_urls.txt", max_cars=None):
        """Extrae los detalles de todos los coches y genera un CSV"""
        print("\n=== INICIANDO EXTRACCIÓN DE DETALLES DE COCHES ===\n")
        
        # Leer URLs del archivo
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {urls_file}")
            return []
        
        if max_cars:
            urls = urls[:max_cars]
        
        cars_data = []
        total_urls = len(urls)
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{total_urls}] Procesando coche...")
            
            car_details = self.get_car_details(url)
            if car_details:
                cars_data.append(car_details)
            
            # Pausa entre requests para ser respetuosos
            time.sleep(1)
        
        return cars_data
    
    def save_to_csv(self, cars_data, filename="VEHICULOS.csv"):
        """Guarda los datos de los coches en un archivo CSV"""
        if not cars_data:
            print("No hay datos para guardar en CSV")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['Matricula', 'Marca', 'Modelo', 'Precio']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Escribir cabecera
                writer.writeheader()
                
                # Escribir datos
                for car in cars_data:
                    writer.writerow({
                        'Matricula': car['matricula'],
                        'Marca': car['marca'],
                        'Modelo': car['modelo'],
                        'Precio': car['precio']
                    })
            
            print(f"\n✅ Datos guardados en {filename}")
            print(f"✅ Total de coches procesados: {len(cars_data)}")
            
        except Exception as e:
            print(f"Error al guardar CSV: {e}")

    def save_urls_to_file(self, filename="car_urls.txt"):
        """Guarda las URLs encontradas en un archivo de texto"""
        with open(filename, 'w', encoding='utf-8') as f:
            for url in self.car_urls:
                f.write(f"{url}\n")
        print(f"URLs guardadas en {filename}")

def main():
    scraper = AutoVidalScraper()
    
    # FASE 1: Obtener URLs (ya completada anteriormente)
    print("=== FASE 1: OBTENER URLS DE COCHES ===")
    
    # Verificar si ya tenemos el archivo de URLs
    import os
    if os.path.exists("car_urls.txt"):
        print("✅ Archivo car_urls.txt encontrado. Saltando extracción de URLs...")
        with open("car_urls.txt", 'r', encoding='utf-8') as f:
            car_urls = [line.strip() for line in f if line.strip()]
        print(f"✅ {len(car_urls)} URLs cargadas desde el archivo")
    else:
        print("🔄 Extrayendo URLs de coches...")
        car_urls = scraper.get_all_car_urls(max_pages=20)
        scraper.save_urls_to_file()
        print(f"✅ {len(car_urls)} URLs extraídas y guardadas")
    
    # FASE 2: Extraer detalles de cada coche
    print("\n=== FASE 2: EXTRAER DETALLES DE CADA COCHE ===")
    
    # Para prueba inicial, procesar solo los primeros 10 coches
    # Puedes cambiar este número o quitar la limitación
    MAX_CARS_TEST = None  # Cambiar a None para procesar todos
    
    if MAX_CARS_TEST:
        print(f"⚠️  MODO PRUEBA: Procesando solo los primeros {MAX_CARS_TEST} coches")
        print("   (Cambia MAX_CARS_TEST = None en el código para procesar todos)")
    
    cars_data = scraper.scrape_all_cars_details(max_cars=MAX_CARS_TEST)
    
    # FASE 3: Generar CSV
    print("\n=== FASE 3: GENERAR CSV ===")
    scraper.save_to_csv(cars_data)
    
    print(f"\n🎉 PROCESO COMPLETADO 🎉")
    print(f"📊 Total URLs encontradas: {len(car_urls)}")
    print(f"📊 Total coches procesados: {len(cars_data)}")
    print(f"📁 Archivo CSV generado: coches_autovidal.csv")
    print("\n✅ Revisa el archivo 'coches_autovidal.csv' en la misma carpeta donde está este ejecutable.")
    
    # Pausa al final para evitar que se cierre la ventana
    try:
        input("\nPresiona ENTER para cerrar...")
    except:
        pass  # En caso de que no se pueda leer input

if __name__ == "__main__":
    main()
