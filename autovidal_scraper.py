# autovidal_scraper.py
import csv
import re
import time
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse, urljoin
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://autovidal.es/coches-usados/"
HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "accept-language": "es-ES,es;q=0.9"
}
TIMEOUT = 20
SLEEP = (0.6, 1.2)  # min/max seconds between requests

session = requests.Session()
session.headers.update(HEADERS)


def sleep_a_bit():
    lo, hi = SLEEP
    time.sleep(lo + (hi - lo) * 0.5)


def get_soup(url):
    resp = session.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def clean_text(txt: str) -> str:
    if not txt:
        return ""
    t = re.sub(r"\s+", " ", txt).strip()
    return t

def normalize_price_to_int(price_str: str) -> str:
    """
    Convierte '27.800' o '27.800,00' o '27 800' en '27800' (solo dígitos).
    Devuelve cadena para que el CSV no cambie tipos; si prefieres int, usa int(...).
    """
    if not price_str:
        return ""
    # Quitar todo lo que no sea dígito
    digits = re.sub(r"\D", "", price_str)
    return digits

def clean_price(txt: str) -> str:
    """
    Devuelve solo la parte numérica del precio (sin símbolo €).
    Mantiene el formato que venga de la web (p. ej., '27.800' o '27.800,00').
    """
    if not txt:
        return ""
    t = clean_text(txt)

    # 1) Si viene como "27.800 €" o "27.800,00 €"
    m = re.search(r"(\d[\d\.\s]*[,\.]?\d*)\s*€", t)
    if m:
        return clean_text(m.group(1))

    # 2) Si viene solo con números (p.ej. desde meta price)
    m2 = re.search(r"\d[\d\.\s]*[,\.]?\d*", t)
    return clean_text(m2.group(0)) if m2 else ""


def title_from_url(path_segment: str) -> str:
    # Convierte slug a título: "mercedes-benz" -> "Mercedes-Benz"
    seg = path_segment.replace("-", " ").strip()
    return " ".join(w.capitalize() if w.upper() != "PHEV" else "PHEV" for w in seg.split())


def extract_make_model_from_detail_url(detail_url: str):
    """
    La URL típica es:
    /coches/segunda-mano/islas-baleares/mercedes-benz/vito/diesel/...
    Tomamos los segmentos marca y modelo si existen.
    """
    try:
        path = urlparse(detail_url).path.strip("/")
        parts = path.split("/")
        # Buscar posición de "/coches/"
        if "coches" in parts:
            i = parts.index("coches")
            # Marca suele ser parts[i+3], Modelo parts[i+4] (depende del patrón)
            # Estructura vista: coches / segunda-mano / islas-baleares / <marca> / <modelo> / <combustible> / ...
            if len(parts) > i + 5:
                marca = title_from_url(parts[i + 3])
                modelo = title_from_url(parts[i + 4])
                return marca, modelo
    except Exception:
        pass
    return "", ""


def find_next_page(soup, current_url):
    """
    Intenta localizar el enlace a la siguiente página en distintos patrones comunes.
    """
    # rel=next
    a = soup.select_one('a[rel="next"]')
    if a and a.get("href"):
        return urljoin(current_url, a["href"])

    # aria-label Siguiente
    for sel in [
        'a[aria-label*="Siguiente" i]',
        'a[title*="Siguiente" i]',
        ".pagination a.next",
        ".pager a.next",
        "a.page-numbers.next",
    ]:
        a = soup.select_one(sel)
        if a and a.get("href"):
            return urljoin(current_url, a["href"])

    # En muchos WP, paginación tipo /page/2/
    # Si no encontramos next, devolvemos None
    return None


def parse_listing_collect_detail_urls(listing_url: str):
    """
    Devuelve un set de URLs de detalle de coches desde una URL de listado.
    """
    soup = get_soup(listing_url)
    sleep_a_bit()
    urls = set()

    # En el HTML dado, los enlaces están en <a class="vcard--link" href="...">
    for a in soup.select("a.vcard--link[href]"):
        href = a.get("href")
        if href and "/coches/" in href:
            urls.add(urljoin(listing_url, href))

    return urls, soup


def page_url(base_url: str, page: int) -> str:
    """
    Devuelve base_url con ?page=N (si N>1). Mantiene otros parámetros si ya existen.
    """
    if page <= 1:
        return base_url
    u = urlparse(base_url)
    qs = dict(parse_qsl(u.query, keep_blank_values=True))
    qs["page"] = str(page)
    new_q = urlencode(qs, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))


def enumerate_all_listing_pages(start_url: str, max_pages: int = 200):
    """
    Recorre todas las páginas usando ?page=N hasta que no haya resultados
    o se alcance max_pages. Devuelve un set con todas las URLs de detalle.
    """
    all_detail_urls = set()
    page = 1
    while page <= max_pages:
        current = page_url(start_url, page)
        try:
            detail_urls, _ = parse_listing_collect_detail_urls(current)
        except Exception as e:
            print(f"[WARN] Error leyendo {current}: {e}")
            break

        if not detail_urls:
            print(f"[INFO] Fin de paginación en page={page} (sin resultados).")
            break

        print(f"[INFO] page={page} -> {len(detail_urls)} URLs")
        all_detail_urls.update(detail_urls)
        page += 1  # siguiente página

    return all_detail_urls



def extract_plate(soup: BeautifulSoup) -> str:
    # Basado en el bloque facilitado:
    # li.stock-vehicle-highlights-list__item--plate-number .stock-vehicle-highlights-list__item-value
    el = soup.select_one(
        ".stock-vehicle-highlights-list__item--plate-number .stock-vehicle-highlights-list__item-value"
    )
    if el:
        return clean_text(el.get_text())
    # Fallbacks habituales
    for sel in [
        'li[class*="plate"] .stock-vehicle-highlights-list__item-value',
        'li[class*="matr"] .stock-vehicle-highlights-list__item-value',
        'span:contains("Matrícula") + span',
    ]:
        el = soup.select_one(sel)
        if el:
            return clean_text(el.get_text())
    # Último recurso: buscar patrón matrícula (XXXXXXX con letras/números)
    txt = soup.get_text(" ", strip=True)
    m = re.search(r"\b([0-9]{4}[A-Z]{3}|[A-Z]{1,2}-\d{4}-[A-Z]{1,2}|[A-Z0-9]{6,8})\b", txt)
    return m.group(1) if m else ""


def extract_price(soup: BeautifulSoup) -> str:
    # Intento 1: meta schema.org
    meta = soup.select_one('meta[itemprop="price"]')
    if meta and meta.get("content"):
        # Intentar sacar currency también
        curr = "€"
        curr_meta = soup.select_one('meta[itemprop="priceCurrency"]')
        if curr_meta and curr_meta.get("content"):
            if curr_meta["content"].upper() == "EUR":
                curr = "€"
        return clean_price(meta.get("content", ""))

    # Intento 2: selectores típicos de precio en la ficha
    for sel in [
        ".stock-vehicle-purchase__price .price__amount",
        ".stock-vehicle-price__price .price__amount",
        ".vehicle-price .price__amount",
        ".price__current",
        ".price .amount",
        ".vcard-price__price",  # por si en detalle reutilizan
    ]:
        el = soup.select_one(sel)
        if el:
            return clean_price(el.get_text())

    # Último recurso: buscar el primer número con símbolo euro
    txt = soup.get_text(" ", strip=True)
    return clean_price(txt)


def extract_title_based_make_model(soup: BeautifulSoup):
    # Preferimos <h1> principal de la ficha
    h1 = soup.find("h1")
    if h1:
        title = clean_text(h1.get_text())
        # Partimos por espacio: primera palabra(s) pueden ser la marca con guiones
        # Heurística: si contiene marca + modelo juntos (p. ej. "Mercedes-Benz Vito")
        parts = title.split()
        if len(parts) >= 2:
            # Marca: primera palabra (o 2 si la primera contiene '-')
            if "-" in parts[0] and len(parts) >= 2:
                marca = parts[0]
                modelo = " ".join(parts[1:])
            else:
                marca = parts[0]
                modelo = " ".join(parts[1:])
            return clean_text(marca), clean_text(modelo)

    # Fallback: meta og:title
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        title = clean_text(og["content"])
        parts = title.split()
        if len(parts) >= 2:
            marca = parts[0]
            modelo = " ".join(parts[1:])
            return clean_text(marca), clean_text(modelo)

    return "", ""


def scrape_car(detail_url: str):
    soup = get_soup(detail_url)
    sleep_a_bit()

    # Matrícula (desde bloque que nos pasaste)
    matricula = extract_plate(soup)

    # Marca / Modelo: 1) desde H1/og:title; 2) desde la URL
    marca, modelo = extract_title_based_make_model(soup)
    if not marca or not modelo:
        m2, mo2 = extract_make_model_from_detail_url(detail_url)
        marca = marca or m2
        modelo = modelo or mo2

    # Precio
    precio = normalize_price_to_int(extract_price(soup))

    return {
        "Matricula": matricula,
        "Marca": marca,
        "Modelo": modelo,
        "Precio": precio,
    }


def main():
    print("[INFO] Recolectando enlaces de coches…")
    detail_urls = enumerate_all_listing_pages(BASE_URL)
    print(f"[INFO] Encontradas {len(detail_urls)} fichas.")

    rows = []
    for i, url in enumerate(sorted(detail_urls)):
        try:
            data = scrape_car(url)
            # Solo guardamos si tiene algo de info
            if any(data.values()):
                rows.append(data)
            print(f"[OK] ({i+1}/{len(detail_urls)}) {url} -> {data['Matricula']} | {data['Marca']} {data['Modelo']} | {data['Precio']}")
        except Exception as e:
            print(f"[WARN] Error en {url}: {e}")

    # Escritura CSV
    out_file = "coches_autovidal.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Matricula", "Marca", "Modelo", "Precio"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] Guardado en {out_file}. Registros: {len(rows)}")


if __name__ == "__main__":
    main()
