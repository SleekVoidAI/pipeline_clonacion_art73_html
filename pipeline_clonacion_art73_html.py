# #################################
# Autor: Jorge F. Ortiz Bravo
# Fecha de programación: 17/04/2026
#
# ART73_CLONACION_PIPELINE_V2_1.py
#
# V 4.0.0
# Script para clonar y adaptar páginas HTML del Artículo 73
# a una nueva estructura de carpetas por entidad federativa.
#
# Datos de la version
# 
# -Se añade diccionario de Estado - RXX
# -Se elimina funcion de firma oculta y responsables de informacion solo queda cambio de Directora.
# -Se modifican funciones para enlazar zips desde carpeta externa 
#
# Incluye:
# - Panel de configuración centralizado
# - Clonación de trimestre origen a trimestre destino
# - Actualización de nombres de trimestre/año
# - Relink de subpáginas
# - Vinculación de botones de descarga
# - Generación de página principal del trimestre
# - Breadcrumbs
# - Normalización de title y h1
# - Reemplazo automático de responsables
# - Inserción opcional de texto oculto de autoría técnica
# #################################

# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import csv
import shutil
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import time


# ============================================================
# 0) PANEL DE CONFIGURACIÓN
# ============================================================
# Esta es la sección más importante del script.
#
# Aquí se pueden cambiar fácilmente:
# - las rutas principales
# - el trimestre origen y destino
# - el nombre de la carpeta de ZIPs
# - los responsables de publicación e información
# - si se quiere insertar una firma técnica oculta en el HTML
#
# En la mayoría de los casos, una persona que no sabe programar
# solo necesita modificar esta sección.


CONFIG = {
    # --------------------------------------------------------
    # RUTAS PRINCIPALES
    # --------------------------------------------------------
    # SOURCE_ROOT:
    # Carpeta que contiene el trimestre base del que se copiarán
    # las páginas y subpáginas.
    #
    # DEST_ROOT:
    # Carpeta donde se creará el nuevo trimestre ya transformado.
    #
    # PLANTILLA_TRIMESTRE:
    # Archivo HTML base que se usará como plantilla para construir
    # la página principal del trimestre destino.
    "SOURCE_ROOT": Path(
        r"C:\Users\JorgeFernandoOrtizBr\Documents\HTML ACTUALIZACION ART 73 2025\HTML HON OFIS\PLANTILLA Segundo_Trimestre_2026"
    ),
    "DEST_ROOT": Path(
        r"D:\CLON Segundo_Trimestre_2026"
    ),
    "PLANTILLA_TRIMESTRE": Path(
        r"C:\Users\JorgeFernandoOrtizBr\Documents\HTML ACTUALIZACION ART 73 2025\HTML HON OFIS\PLANTILLA Segundo_Trimestre_2026\Segundo_Trimestre_2026.html"
    ),

    # --------------------------------------------------------
    # TRIMESTRE Y AÑO ORIGEN / DESTINO
    # --------------------------------------------------------
    # Valores permitidos para quarter_tag:
    # "1t" = Primer Trimestre
    # "2t" = Segundo Trimestre
    # "3t" = Tercer Trimestre
    # "4t" = Cuarto Trimestre

    "FROM_QTAG": "2t", 
    "FROM_YEAR": "2026",
    "TO_QTAG": "1t",   ## Trimestre de salida
    "TO_YEAR": "2026", ## Año de salida

    # -------------------------------------------------------- #Modificar
    # NOMBRE DE LA CARPETA DE ZIPs
    # --------------------------------------------------------
    # Solo cambiar si la carpeta ya no se llama "Archivos".

    "ARCHIVOS_FOLDER": "Archivos",

    # -------------------------------------------------------- #
    # RUTA OPCIONAL DE ZIPs EXTERNOS
    # --------------------------------------------------------
    # Si no se van a copiar ZIPs desde una ruta externa,
    # dejar este valor como None.
    #
    # Si sí se van a copiar, poner algo como:
    # Path(r"C:\...\DOCUMENTOS SEP TRIMESTRALES\Primer_Trimestre_2026")

    "ZIP_SOURCE_ROOT": Path(r"D:\Archivos de Joselyn López Roa - TRIMESTRE_2026_01__01_04_2026__11_57"), #Modificar ESCRIBIR RUTA A ARCHIVOS ZIP

    # --------------------------------------------------------
    # RESPONSABLES DEL PORTAL
    # --------------------------------------------------------
    # Estos textos se actualizarán automáticamente en todas
    # las páginas HTML procesadas.

    "RESPONSABLES": {
        "publicacion": {
            "nombre": 'Lic. Elizabeth Gonzalez',
            "cargo": 'Directora General del Sistema de Administración de la Nómina Educativa Federalizada',
        },
    },

}


# ============================================================
# 1) ACCESOS RÁPIDOS A CONFIGURACIÓN
# ============================================================

SOURCE_ROOT = CONFIG["SOURCE_ROOT"]
DEST_ROOT = CONFIG["DEST_ROOT"]
PLANTILLA_TRIMESTRE = CONFIG["PLANTILLA_TRIMESTRE"]

FROM_QTAG = CONFIG["FROM_QTAG"]
FROM_YEAR = CONFIG["FROM_YEAR"]
TO_QTAG = CONFIG["TO_QTAG"]
TO_YEAR = CONFIG["TO_YEAR"]

ARCHIVOS_FOLDER = CONFIG["ARCHIVOS_FOLDER"]
ZIP_SOURCE_ROOT = CONFIG["ZIP_SOURCE_ROOT"]


# ============================================================
# 2) CONSTANTES Y MAPAS
# ============================================================

MAPA_ENTIDADES = {
    "aguascalientes": "r01",
    "baja_california": "r02",
    "baja_california_sur": "r03",
    "campeche": "r04",
    "coahuila": "r05",
    "colima": "r06",
    "chiapas": "r07",
    "chihuahua": "r08",
    "durango": "r10",
    "guanajuato": "r11",
    "guerrero": "r12",
    "hidalgo": "r13",
    "jalisco": "r14",
    "estado_de_mexico": "r15",
    "michoacan": "r16",
    "morelos": "r17",
    "nayarit": "r18",
    "nuevo_leon": "r19",
    "oaxaca": "r20",
    "puebla": "r21",
    "queretaro": "r22",
    "quintana_roo": "r23",
    "san_luis_potosi": "r24",
    "sinaloa": "r25",
    "sonora": "r26",
    "tabasco": "r27",
    "tamaulipas": "r28",
    "tlaxcala": "r29",
    "veracruz": "r30",
    "yucatan": "r31",
    "zacatecas": "r32",
}

QUARTER = {
    "1t": ("Primer",  "Primer_Trimestre",  "01"),
    "2t": ("Segundo", "Segundo_Trimestre", "02"),
    "3t": ("Tercer",  "Tercer_Trimestre",  "03"),
    "4t": ("Cuarto",  "Cuarto_Trimestre",  "04"),
}

REPORT_KEYS = [
    "analitico_de_plazas",
    "catalogo_de_tabuladores",
    "catalogo_de_percepciones_y_deducciones",
    "movimientos_de_plazas",
    "plazas_docentes_administrativas_y_directivas",
    "personal_con_pagos_retroactivos_hasta_por_45_dias_naturales",
    "personal_con_licencia",
    "personal_comisionado",
    "personal_con_licencia_prejubilatoria",
    "personal_jubilado",
]

REPORT_TITLE = {
    "analitico_de_plazas": "Analitico de Plazas",
    "catalogo_de_percepciones_y_deducciones": "Catalogo de Percepciones y Deducciones",
    "catalogo_de_tabuladores": "Catalogo de Tabuladores",
    "movimientos_de_plazas": "Movimientos de Plazas",
    "personal_comisionado": "Personal Comisionado",
    "personal_jubilado": "Personal Jubilado",
    "personal_con_licencia": "Personal con Licencia",
    "personal_con_pagos_retroactivos_hasta_por_45_dias_naturales": "Personal con Pagos Retroactivos",
    "personal_con_licencia_prejubilatoria": "Personal con Licencia Prejubilatoria",
    "plazas_docentes_administrativas_y_directivas": "Plazas Docentes Administrativas y Directivas",
}

ZIP_PREFIX = {
    "analitico_de_plazas": "AnaliticoPlazas_",
    "catalogo_de_percepciones_y_deducciones": "CatalogoPercepDeduc_",
    "catalogo_de_tabuladores": "CatalogoTabuladores_",
    "movimientos_de_plazas": "MovimientosPlaza_",
    "personal_comisionado": "PersonalComisionado_",
    "personal_jubilado": "PersonalJubilado_",
    "personal_con_licencia": "PersonalLicencias_",
    "personal_con_pagos_retroactivos_hasta_por_45_dias_naturales": "PersonalPagosRetroactivos_",
    "personal_con_licencia_prejubilatoria": "PersonalPrejubilatoria_",
    "plazas_docentes_administrativas_y_directivas": "PlazasDocAdmtvasDirec_",
}

REPORT_LABELS = {
    "analitico_de_plazas": (1, "Analítico de Plazas"),
    "catalogo_de_tabuladores": (2, "Catálogo de Tabuladores"),
    "catalogo_de_percepciones_y_deducciones": (3, "Catálogo de Percepciones y Deducciones"),
    "movimientos_de_plazas": (4, "Movimientos de Plazas"),
    "plazas_docentes_administrativas_y_directivas": (5, "Plazas Docentes Administrativas y Directivas"),
    "personal_con_pagos_retroactivos_hasta_por_45_dias_naturales": (6, "Personal con Pagos Retroactivos hasta por 45 días naturales"),
    "personal_con_licencia": (7, "Personal con Licencia"),
    "personal_comisionado": (8, "Personal Comisionado"),
    "personal_con_licencia_prejubilatoria": (9, "Personal con Licencia Prejubilatoria"),
    "personal_jubilado": (10, "Personal Jubilado"),
}


# ============================================================
# 3) ESTRUCTURA DE REPORTE
# ============================================================

@dataclass
class Stats:
    paginas_clonadas: int = 0
    entidades_clonadas: int = 0

    carpetas_estados_renombradas: int = 0

    relinks_principales: int = 0
    titles_modificados: int = 0
    h1_modificados: int = 0
    breadcrumbs_modificados: int = 0
    pagina_trimestral_generada: int = 0

    zips_encontrados_total: int = 0
    zips_copiados_entidades: int = 0
    zips_no_encontrados_entidades: int = 0

    descargas_vinculadas: int = 0
    descargas_faltantes: int = 0

    responsables_actualizados: int = 0
    firma_oculta_insertada: int = 0

    warnings: list[str] = field(default_factory=list)


# ============================================================
# 4) HELPERS GENERALES
# ============================================================

def read_text_smart(p: Path) -> tuple[str, str]:
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            return p.read_text(encoding=enc), enc
        except Exception:
            pass
    return p.read_text(encoding="latin-1", errors="replace"), "latin-1"


def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def slugify_text(s: str) -> str:
    s = strip_accents(s)
    s = s.lower().strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def smart_title_case(words: str) -> str:
    lower_keep = {"de", "del", "y", "la", "el", "los", "las"}
    parts = words.split()
    out = []
    for i, w in enumerate(parts):
        wl = w.lower()
        if i != 0 and wl in lower_keep:
            out.append(wl)
        else:
            out.append(wl.capitalize())
    return " ".join(out)


def estado_title_from_slug(slug: str) -> str:
    txt = smart_title_case(slug.replace("_", " ").strip())
    return txt


def reporte_title_from_key(key: str) -> str:
    return REPORT_TITLE.get(key, smart_title_case(key.replace("_", " ")))


def infer_report_key_from_filename(fname: str) -> Optional[str]:
    base = fname.lower().removesuffix(".html")
    m = re.search(r"_(1t|2t|3t|4t)_(\d{4})_", base)
    if not m:
        return None
    report_key = base[:m.start()].strip("_")
    report_key = re.sub(r"_+", "_", report_key)
    return report_key


def is_state_folder(p: Path) -> bool:
    if not p.is_dir():
        return False

    has_main = any(p.glob(f"*_{FROM_QTAG}_{FROM_YEAR}.html"))
    has_sub = any(p.glob(f"*_{FROM_QTAG}_{FROM_YEAR}_*.html"))
    return has_main or has_sub


def find_main_html(entity_dir: Path, qtag: str, year: str) -> Optional[Path]:
    pattern = re.compile(rf"^[a-z0-9_]+_{qtag}_{year}\.html$", re.IGNORECASE)
    candidates = []

    for p in entity_dir.glob("*.html"):
        if pattern.match(p.name):
            if infer_report_key_from_filename(p.name) is None:
                candidates.append(p)

    if candidates:
        return sorted(candidates, key=lambda x: x.name.lower())[0]

    return None


def replace_all(text: str) -> str:
    from_word, from_slug, from_num = QUARTER[FROM_QTAG]
    to_word, to_slug, to_num = QUARTER[TO_QTAG]

    text = text.replace(f"_{FROM_QTAG}_{FROM_YEAR}", f"_{TO_QTAG}_{TO_YEAR}")

    text = re.sub(
        rf"{from_word}(\s|&nbsp;)Trimestre\s+{FROM_YEAR}",
        rf"{to_word}\1Trimestre {TO_YEAR}",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        rf'(/es/sep1/){re.escape(from_slug)}_{FROM_YEAR}',
        rf'\1{to_slug}_{TO_YEAR}',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        rf'(\.\./){re.escape(from_slug)}_{FROM_YEAR}\.html',
        rf'\1{to_slug}_{TO_YEAR}.html',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        rf'(Trimestre_){from_num}(_){FROM_YEAR}(\.zip)',
        rf'\1{to_num}\2{TO_YEAR}\3',
        text,
        flags=re.IGNORECASE
    )

    return text


def safe_rename_dir(src: Path, dst: Path, stats: Stats, label: str, retries: int = 5, wait_s: float = 0.4) -> bool:
    if dst.exists():
        stats.warnings.append(f"[{label}] NO renombré (ya existe destino): {src.name} -> {dst.name}")
        return False

    last_err = None
    for _ in range(retries):
        try:
            src.rename(dst)
            return True
        except PermissionError as e:
            last_err = e
            time.sleep(wait_s)
        except OSError as e:
            last_err = e
            time.sleep(wait_s)

    stats.warnings.append(f"[{label}] ERROR renombrando {src.name} -> {dst.name}: {last_err}")
    return False


# ============================================================
# 5) HELPERS DE RESPONSABLES Y FIRMA OCULTA
# ============================================================

def replace_responsables_text(html: str) -> tuple[str, bool]:
    """
    Actualiza los textos visibles de responsables dentro del HTML.
    Intenta reemplazar:
    - Responsable de la publicación
    - Responsable de la información
    """

    original = html

    nombre = CONFIG["RESPONSABLES"]["publicacion"]["nombre"]
    cargo = CONFIG["RESPONSABLES"]["publicacion"]["cargo"]

    # Caso 1: bloque completo con comillas
    pattern_pub_block = re.compile(
        r'(Responsable de la publicación\s*</p>\s*.*?<p[^>]*>\s*")([^"]*)("\s*</p>\s*.*?<p[^>]*>\s*")([^"]*)("\s*</p>)',
        flags=re.IGNORECASE | re.DOTALL
    )

    html, n1 = pattern_pub_block.subn(
        rf'\1{nombre}\3{cargo}\5',
        html,
        count=1
    )

    # Caso 2: si el HTML trae texto más libre
    if n1 == 0:
        html = re.sub(
            r'(Responsable de la publicación.*?")([^"]*)(")',
            rf'\1{nombre}\3',
            html,
            flags=re.IGNORECASE | re.DOTALL,
            count=1
        )

        html = re.sub(
            r'(")(Director[a]?[^"]*)(")',
            rf'\1{cargo}\3',
            html,
            flags=re.IGNORECASE | re.DOTALL,
            count=1
        )

    return html, (html != original)


# ============================================================
# 6) MÓDULO A: CLONACIÓN
# ============================================================

def clone_entity_folder(src_entity: Path, dst_entity: Path, stats: Stats):
    dst_entity.mkdir(parents=True, exist_ok=True)

    for item in src_entity.iterdir():
        if item.is_dir():
            shutil.copytree(item, dst_entity / item.name, dirs_exist_ok=True)
        else:
            if item.suffix.lower() != ".html":
                shutil.copy2(item, dst_entity / item.name)

    for src_html in src_entity.glob("*.html"):
        new_name = src_html.name.replace(f"_{FROM_QTAG}_{FROM_YEAR}", f"_{TO_QTAG}_{TO_YEAR}")
        dst_html = dst_entity / new_name

        txt, _enc = read_text_smart(src_html)
        text2 = replace_all(txt)
        dst_html.write_text(text2, encoding="utf-8")

        stats.paginas_clonadas += 1


def step_clone(stats: Stats):
    if not SOURCE_ROOT.exists():
        stats.warnings.append(f"[CLONAR] No existe SOURCE_ROOT: {SOURCE_ROOT}")
        return

    DEST_ROOT.mkdir(parents=True, exist_ok=True)

    for src_entity in sorted(SOURCE_ROOT.iterdir(), key=lambda x: x.name.lower()):
        if not is_state_folder(src_entity):
            continue

        dst_entity = DEST_ROOT / src_entity.name
        clone_entity_folder(src_entity, dst_entity, stats)
        stats.entidades_clonadas += 1


# ============================================================
# 7) MÓDULO B: RENOMBRE DE CARPETAS DE ESTADOS
# ============================================================

def step_rename_state_folders_official(stats: Stats):
    """
    Obsoleto en la nueva estructura.
    Las carpetas ya vienen con nombre oficial.
    """
    return


# ============================================================
# 8) MÓDULO C: RELINK DE SUBPÁGINAS
# ============================================================

def find_existing_subpage(entity_dir: Path, report_key: str, qtag: str, year: str) -> Optional[str]:
    patt = re.compile(rf"^{re.escape(report_key)}_{qtag}_{year}_.+\.html$", re.IGNORECASE)
    for f in sorted(entity_dir.glob("*.html"), key=lambda x: x.name.lower()):
        if patt.match(f.name):
            return f.name
    return None


def relink_main(main_text: str, entity_dir: Path, qtag: str, year: str) -> str:
    new_text = main_text
    for key in REPORT_KEYS:
        real_file = find_existing_subpage(entity_dir, key, qtag, year)
        if not real_file:
            continue

        new_text = re.sub(
            rf'href="[^"]*{re.escape(key)}_{qtag}_{year}_[^"]*\.html"',
            f'href="{real_file}"',
            new_text,
            flags=re.IGNORECASE
        )
        new_text = re.sub(
            rf'href="[^"]*/{re.escape(key)}_{qtag}_{year}_[^"]*"',
            f'href="{real_file}"',
            new_text,
            flags=re.IGNORECASE
        )
        new_text = re.sub(
            rf'href="[^"]*{re.escape(key)}_{qtag}_{year}_[^"]*"',
            f'href="{real_file}"',
            new_text,
            flags=re.IGNORECASE
        )
    return new_text


def step_relink_subpages(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[RELINK] No existe DEST_ROOT: {DEST_ROOT}")
        return

    for entity_dir in sorted([p for p in DEST_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
        main_html = find_main_html(entity_dir, TO_QTAG, TO_YEAR)
        if not main_html:
            continue

        txt, enc = read_text_smart(main_html)
        new_txt = relink_main(txt, entity_dir, TO_QTAG, TO_YEAR)
        if new_txt != txt:
            main_html.write_text(new_txt, encoding=enc)
            stats.relinks_principales += 1


# ============================================================
# 9) MÓDULO D: COPIAR ZIPS (OPCIONAL) + CONTAR
# ============================================================

def step_copy_zips(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[ZIPS] No existe DEST_ROOT: {DEST_ROOT}")
        return

    for entity_dir in sorted([p for p in DEST_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
        zdir = entity_dir / ARCHIVOS_FOLDER
        if zdir.exists():
            stats.zips_encontrados_total += len(list(zdir.glob("*.zip")))

    if ZIP_SOURCE_ROOT is None:
        return

    if not ZIP_SOURCE_ROOT.exists():
        stats.warnings.append(f"[ZIPS] No existe ZIP_SOURCE_ROOT: {ZIP_SOURCE_ROOT}")
        return

    origen_idx = {}
    for p in ZIP_SOURCE_ROOT.iterdir():
        if p.is_dir():
            origen_idx[slugify_text(p.name)] = p

    for entity_dir in sorted([p for p in DEST_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
        estado_slug = slugify_text(entity_dir.name)

        codigo_r = MAPA_ENTIDADES.get(estado_slug) # V4.0

        if not codigo_r:
            print(f"No hay mapeo para: {estado_slug}")
            stats.zips_no_encontrados_entidades += 1
            continue

        src_state = origen_idx.get(codigo_r)

        if not src_state:
            stats.zips_no_encontrados_entidades += 1
            continue

        source_archivos = src_state / ARCHIVOS_FOLDER
        target_archivos = entity_dir / ARCHIVOS_FOLDER

        # Si no existe carpeta Archivos, tomar los ZIP directos desde la raíz de la entidad
        if source_archivos.exists():
            real_source = source_archivos
            zip_files = [z for z in real_source.glob("*.zip") if not z.name.startswith("._")]
        else:
            real_source = src_state
            zip_files = [z for z in real_source.glob("*.zip") if not z.name.startswith("._")]

        if not zip_files:
            stats.zips_no_encontrados_entidades += 1
            continue

        if target_archivos.exists():
            shutil.rmtree(target_archivos)

        target_archivos.mkdir(parents=True, exist_ok=True)

        for z in zip_files:
            shutil.copy2(z, target_archivos / z.name)

        stats.zips_copiados_entidades += 1


# ============================================================
# 10) MÓDULO E: VINCULAR DESCARGAS
# ============================================================

def find_zip_for_prefix(zips_dir: Path, prefix: str) -> Optional[str]:
    for z in sorted(zips_dir.glob("*.zip"), key=lambda x: x.name.lower()):
        if z.name.startswith("._"):
            continue
        if z.name.startswith(prefix):
            return z.name
    return None


def replace_download_href(html: str, new_href: str) -> str:
    patterns = [
        re.compile(
            r'(<a\s+href=")[^"]+(">\s*[\r\n\s]*<button[^>]*>\s*Descargar archivo\s*</button>\s*[\r\n\s]*</a>)',
            flags=re.IGNORECASE
        ),
        re.compile(
            r'(<a\s+href=")[^"]+(" [^>]*>\s*Descargar archivo\s*</a>)',
            flags=re.IGNORECASE
        ),
        re.compile(
            r'(<a[^>]*\shref=")[^"]+("[^>]*>\s*[\r\n\s]*(?:<span[^>]*>)?\s*Descargar archivo)',
            flags=re.IGNORECASE
        ),
    ]

    for patt in patterns:
        new_html, count = patt.subn(rf'\1{new_href}\2', html, count=1)
        if count > 0:
            return new_html

    return html


def step_link_downloads(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[DESCARGAS] No existe DEST_ROOT: {DEST_ROOT}")
        return

    faltantes = []

    for entity_dir in sorted([p for p in DEST_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
        zips_dir = entity_dir / ARCHIVOS_FOLDER
        if not zips_dir.exists():
            continue

        for html_file in sorted(entity_dir.glob("*.html"), key=lambda x: x.name.lower()):
            if re.search(rf"_{TO_QTAG}_{TO_YEAR}\.html$", html_file.name, flags=re.IGNORECASE):
                continue

            report_key = infer_report_key_from_filename(html_file.name)
            if not report_key or report_key not in ZIP_PREFIX:
                stats.descargas_faltantes += 1
                faltantes.append({
                    "entidad": entity_dir.name,
                    "html": html_file.name,
                    "report_key": report_key or "",
                    "prefijo_esperado": "",
                    "zip_encontrado": "",
                    "motivo": "report_key_no_inferida_o_no_en_diccionario"
                })
                continue

            prefix = ZIP_PREFIX[report_key]
            zip_name = find_zip_for_prefix(zips_dir, prefix)

            if not zip_name:
                stats.descargas_faltantes += 1
                faltantes.append({
                    "entidad": entity_dir.name,
                    "html": html_file.name,
                    "report_key": report_key,
                    "prefijo_esperado": prefix,
                    "zip_encontrado": "",
                    "motivo": "no_hay_zip_con_prefijo"
                })
                continue

            txt, enc = read_text_smart(html_file)
            new_txt = replace_download_href(txt, f"{ARCHIVOS_FOLDER}/{zip_name}")

            if new_txt != txt:
                html_file.write_text(new_txt, encoding=enc)
                stats.descargas_vinculadas += 1

    if faltantes:
        out_csv = DEST_ROOT / "reporte_faltantes_zip.csv"
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["entidad", "html", "report_key", "prefijo_esperado", "zip_encontrado", "motivo"]
            )
            w.writeheader()
            w.writerows(faltantes)


# ============================================================
# 11) MÓDULO F: GENERAR PÁGINA TRIMESTRAL
# ============================================================

def replace_trimestre_text_everywhere(html: str, qtag: str, year: str) -> str:
    word, slug, _num = QUARTER[qtag]

    html = re.sub(
        r"<h2>\s*(Primer|Segundo|Tercer|Cuarto)(?:&nbsp;|\s)Trimestre\s+\d{4}\s*</h2>",
        f"<h2>{word}&nbsp;Trimestre {year}</h2>",
        html,
        flags=re.IGNORECASE
    )

    html = re.sub(
        r'<a href="[^"]+_(?:Trimestre)_\d{4}\.html">\s*(Primer|Segundo|Tercer|Cuarto)\s+Trimestre\s+\d{4}\s*</a>',
        f'<a href="{slug}_{year}.html">{word} Trimestre {year}</a>',
        html,
        flags=re.IGNORECASE
    )

    return html


def rebuild_trimestre_links(html: str, items: list[tuple[str, str]]) -> str:
    new_block = []
    for text, href in items:
        new_block.append(f'            <p><a href="{href}">{text}</a></p>')
        new_block.append("            <hr>")

    block_str = "\n".join(new_block) + "\n"

    pattern = re.compile(
        r"(?:\s*<p>\s*<a href=.*?</a>\s*</p>\s*<hr>\s*)+",
        flags=re.IGNORECASE | re.DOTALL
    )

    return pattern.sub(block_str, html, count=1)


def step_generate_trimestre_page(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[TRIMESTRE] No existe DEST_ROOT: {DEST_ROOT}")
        return

    if not PLANTILLA_TRIMESTRE.exists():
        stats.warnings.append(f"[TRIMESTRE] No existe PLANTILLA_TRIMESTRE: {PLANTILLA_TRIMESTRE}")
        return

    entities = []

    for folder in sorted([p for p in DEST_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
        main_html = find_main_html(folder, TO_QTAG, TO_YEAR)
        if not main_html:
            continue

        display = folder.name
        href = f"{folder.name}/{main_html.name}"
        entities.append((display, href))

    if not entities:
        stats.warnings.append("[TRIMESTRE] No se detectaron entidades con HTML principal.")
        return

    _word, slug, _num = QUARTER[TO_QTAG]
    trimestre_out = DEST_ROOT / f"{slug}_{TO_YEAR}.html"

    base_html, _enc = read_text_smart(PLANTILLA_TRIMESTRE)
    base_html = replace_trimestre_text_everywhere(base_html, TO_QTAG, TO_YEAR)
    base_html = rebuild_trimestre_links(base_html, entities)

    trimestre_out.write_text(base_html, encoding="utf-8")
    stats.pagina_trimestral_generada = 1


# ============================================================
# 12) MÓDULO G: BREADCRUMB
# ============================================================

def build_breadcrumb(entity_name: str, entity_main_filename: str, qtag: str, year: str,
                     current_filename: str, report_item: Optional[tuple[int, str]]) -> str:
    q_word, q_slug, _n = QUARTER[qtag]
    trimestre_href = f"../{q_slug}_{year}.html"
    trimestre_text = f"{q_word}&nbsp;Trimestre {year}"

    lines = [
        '<ol class="breadcrumb">',
        '    <li class="active"><a href="http://www.gob.mx/"><i class="icon icon-home"></i></a></li>',
        '    <li class="active"><a href="https://dgsanef.sep.gob.mx/">Inicio</a></li>',
        '    <li class="active"><a href="https://dgsanef.sep.gob.mx/Transparencia">Transparencia</a></li>',
        '    <li class="active"><a href="https://dgsanef.sep.gob.mx/art73lgcg">Artículo 73 de la Ley General de',
        '            Contabilidad Gubernamental</a></li>',
        f'    <li class="active"><a href="{trimestre_href}">{trimestre_text}</a></li>',
        f'    <li class="active"><a href="{entity_main_filename}">{entity_name}</a></li>',
    ]

    if report_item is not None:
        n, title = report_item
        lines.append(f'    <li class="active"><a href="{current_filename}">{n}. {title}</a></li>')

    lines.append("</ol>")
    return "\n".join(lines)


def replace_ol_breadcrumb(html: str, new_ol: str) -> str:
    pattern = re.compile(r'<ol class="breadcrumb">.*?</ol>', flags=re.DOTALL | re.IGNORECASE)
    return pattern.sub(new_ol, html, count=1)


def step_breadcrumbs(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[BREADCRUMB] No existe DEST_ROOT: {DEST_ROOT}")
        return

    for entity_dir in sorted([p for p in DEST_ROOT.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
        entity_name_official = entity_dir.name

        main_html = find_main_html(entity_dir, TO_QTAG, TO_YEAR)
        if not main_html:
            continue

        txt, enc = read_text_smart(main_html)
        new_ol = build_breadcrumb(
            entity_name=entity_name_official,
            entity_main_filename=main_html.name,
            qtag=TO_QTAG,
            year=TO_YEAR,
            current_filename=main_html.name,
            report_item=None
        )
        new_txt = replace_ol_breadcrumb(txt, new_ol)
        if new_txt != txt:
            main_html.write_text(new_txt, encoding=enc)
            stats.breadcrumbs_modificados += 1

        for sub in sorted(entity_dir.glob("*.html"), key=lambda x: x.name.lower()):
            if sub.name.lower() == main_html.name.lower():
                continue

            rkey = infer_report_key_from_filename(sub.name)
            report_item = REPORT_LABELS.get(rkey) if rkey else None

            txt2, enc2 = read_text_smart(sub)
            new_ol2 = build_breadcrumb(
                entity_name=entity_name_official,
                entity_main_filename=main_html.name,
                qtag=TO_QTAG,
                year=TO_YEAR,
                current_filename=sub.name,
                report_item=report_item
            )
            new_txt2 = replace_ol_breadcrumb(txt2, new_ol2)
            if new_txt2 != txt2:
                sub.write_text(new_txt2, encoding=enc2)
                stats.breadcrumbs_modificados += 1


# ============================================================
# 13) MÓDULO H: TITLES + H1
# ============================================================

TITLE_RE = re.compile(r"(<title\b[^>]*>)(.*?)(</title>)", flags=re.IGNORECASE | re.DOTALL)
H1_RE = re.compile(r"(<h1\b[^>]*>)(.*?)(</h1>)", flags=re.IGNORECASE | re.DOTALL)

RE_ESTADO_HTML = re.compile(r"^([a-z0-9_]+)_(1t|2t|3t|4t)_(\d{4})\.html$", re.IGNORECASE)
RE_REPORTE_HTML = re.compile(r"^([a-z0-9_]+)_(1t|2t|3t|4t)_(\d{4})_([a-z0-9_]{2,30})\.html$", re.IGNORECASE)
RE_TRIMESTRE_MAIN = re.compile(r"^(primer|segundo|tercer|cuarto)_trimestre_(\d{4})\.html$", re.IGNORECASE)

TRIMESTRE_MAP = {"primer": "Primer", "segundo": "Segundo", "tercer": "Tercer", "cuarto": "Cuarto"}


def replace_title(html: str, new_title: str) -> tuple[str, bool]:
    m = TITLE_RE.search(html)
    if not m:
        return html, False
    out = html[:m.start(2)] + new_title + html[m.end(2):]
    return out, (out != html)


def replace_first_h1(html: str, new_h1: str) -> tuple[str, bool]:
    m = H1_RE.search(html)
    if not m:
        return html, False
    out = html[:m.start(2)] + new_h1 + html[m.end(2):]
    return out, (out != html)


def step_titles_and_h1(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[TITLES] No existe DEST_ROOT: {DEST_ROOT}")
        return

    for html_path in sorted(DEST_ROOT.rglob("*.html"), key=lambda x: x.name.lower()):
        txt, enc = read_text_smart(html_path)
        new_txt = txt

        new_title: Optional[str] = None
        name = html_path.name

        mrep = RE_REPORTE_HTML.match(name)
        if mrep:
            key = mrep.group(1).lower()
            new_title = reporte_title_from_key(key)

            parent_name = html_path.parent.name
            new_txt, changed_h1 = replace_first_h1(new_txt, parent_name)
            if changed_h1:
                stats.h1_modificados += 1

        else:
            mest = RE_ESTADO_HTML.match(name)
            if mest:
                slug_estado = mest.group(1).lower()
                new_title = estado_title_from_slug(slug_estado)

            else:
                mtri = RE_TRIMESTRE_MAIN.match(name)
                if mtri:
                    tri = TRIMESTRE_MAP.get(mtri.group(1).lower(), mtri.group(1).capitalize())
                    year = mtri.group(2)
                    new_title = f"{tri} Trimestre {year}"

        if new_title:
            new_txt, changed_title = replace_title(new_txt, new_title)
            if changed_title:
                stats.titles_modificados += 1

        if new_txt != txt:
            html_path.write_text(new_txt, encoding=enc)


# ============================================================
# 14) MÓDULO I: RESPONSABLES + FIRMA OCULTA
# ============================================================

def step_responsables(stats: Stats):
    if not DEST_ROOT.exists():
        stats.warnings.append(f"[RESPONSABLES] No existe DEST_ROOT: {DEST_ROOT}")
        return

    for html_path in sorted(DEST_ROOT.rglob("*.html"), key=lambda x: x.name.lower()):
        txt, enc = read_text_smart(html_path)

        new_txt, changed_resp = replace_responsables_text(txt)

        if changed_resp:
            stats.responsables_actualizados += 1
            html_path.write_text(new_txt, encoding=enc)

# ============================================================
# 15) RESUMEN
# ============================================================

def print_summary(stats: Stats):
    print("\n================== RESUMEN PIPELINE ART 73 ==================")
    print(f"Se clonaron {stats.paginas_clonadas} páginas (en {stats.entidades_clonadas} entidades).")
    print(f"Se renombraron {stats.carpetas_estados_renombradas} carpetas de estados.")
    print(f"Se vincularon {stats.relinks_principales} páginas principales (relink subpáginas).")
    print(f"Se modificó el <title> de {stats.titles_modificados} páginas.")
    print(f"Se corrigió el <h1> de {stats.h1_modificados} subpáginas.")
    print(f"Se generó la página trimestral: {'SI' if stats.pagina_trimestral_generada else 'NO'}.")
    print(f"Se generó/actualizó breadcrumb en {stats.breadcrumbs_modificados} páginas.")
    print(f"Se actualizaron responsables en {stats.responsables_actualizados} páginas.")
    print(f"Se insertó firma oculta en {stats.firma_oculta_insertada} páginas.")

    if stats.zips_encontrados_total == 0:
        print("No se encontraron archivos .zip en carpetas Archivos (para descargas).")
    else:
        print(f"Se detectaron {stats.zips_encontrados_total} archivos .zip en total en Archivos/.")

    if ZIP_SOURCE_ROOT is not None:
        print(f"Se copiaron Archivos/ a {stats.zips_copiados_entidades} entidades (faltaron {stats.zips_no_encontrados_entidades}).")

    if stats.descargas_vinculadas == 0 and stats.descargas_faltantes == 0:
        print("No se procesaron botones de descarga (no había subpáginas o no había Archivos/).")
    else:
        print(f"Se vincularon {stats.descargas_vinculadas} botones de descarga.")
        if stats.descargas_faltantes:
            print(f"Faltaron ZIP para {stats.descargas_faltantes} páginas (ver reporte_faltantes_zip.csv).")

    if stats.warnings:
        print("\n--- WARNINGS (resumen) ---")
        print(f"Total warnings: {len(stats.warnings)}")
        for w in stats.warnings[:10]:
            print("•", w)
        if len(stats.warnings) > 10:
            print(f"... y {len(stats.warnings)-10} más.")

    print("============================================================\n")


# ============================================================
# 16) MAIN
# ============================================================

def main():
    stats = Stats()

    step_clone(stats)                         # 1) clonar estructura
    step_rename_state_folders_official(stats) # 2) obsoleto, no hace nada
    step_relink_subpages(stats)              # 3) relink de subpáginas
    step_copy_zips(stats)                    # 4) copiar o contar ZIPs
    step_link_downloads(stats)               # 5) vincular descargas
    step_generate_trimestre_page(stats)      # 6) generar página trimestral
    step_breadcrumbs(stats)                  # 7) actualizar breadcrumb
    step_titles_and_h1(stats)                # 8) normalizar titles y h1
    step_responsables(stats)                 # 9) responsables

    print_summary(stats)


if __name__ == "__main__":
    main()