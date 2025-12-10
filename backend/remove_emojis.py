#!/usr/bin/env python3
"""
Script simple para eliminar todos los emojis de archivos Python
NO requiere imports del proyecto
"""

import re
from pathlib import Path

# Patrón regex para detectar emojis
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # símbolos y pictogramas
    "\U0001F680-\U0001F6FF"  # transporte y símbolos de mapa
    "\U0001F1E0-\U0001F1FF"  # banderas
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # símbolos suplementarios
    "\U0001FA70-\U0001FAFF"  # símbolos extendidos
    "]+",
    flags=re.UNICODE
)

def remove_emojis(text: str) -> str:
    """Elimina todos los emojis de un texto"""
    return EMOJI_PATTERN.sub('', text)

def process_file(file_path: Path) -> tuple:
    """
    Procesa un archivo eliminando emojis
    
    Returns:
        (changed, emoji_count): Si hubo cambios y cuántos emojis se eliminaron
    """
    try:
        # Leer archivo
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Eliminar emojis
        cleaned_content = remove_emojis(original_content)
        
        # Contar emojis eliminados
        emoji_count = len(EMOJI_PATTERN.findall(original_content))
        
        # Si hubo cambios, escribir archivo
        if cleaned_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True, emoji_count
        
        return False, 0
        
    except Exception as e:
        print(f"[ERROR] procesando {file_path}: {e}")
        return False, 0

def clean_project(root_dir: str = "src") -> dict:
    """
    Limpia todos los archivos .py del proyecto
    
    Returns:
        Diccionario con estadísticas
    """
    root = Path(root_dir)
    
    if not root.exists():
        print(f"[ERROR] Directorio no encontrado: {root_dir}")
        return {
            "total_files": 0,
            "files_changed": 0,
            "total_emojis_removed": 0,
            "files_processed": []
        }
    
    stats = {
        "total_files": 0,
        "files_changed": 0,
        "total_emojis_removed": 0,
        "files_processed": []
    }
    
    # Buscar todos los archivos .py
    for py_file in root.rglob("*.py"):
        stats["total_files"] += 1
        changed, emoji_count = process_file(py_file)
        
        if changed:
            stats["files_changed"] += 1
            stats["total_emojis_removed"] += emoji_count
            stats["files_processed"].append({
                "file": str(py_file.relative_to(root)),
                "emojis_removed": emoji_count
            })
            print(f"[OK] {py_file.name}: {emoji_count} emojis eliminados")
    
    return stats

def print_report(stats: dict):
    """Imprime reporte de limpieza"""
    print("\n" + "=" * 70)
    print("LIMPIEZA DE EMOJIS COMPLETADA")
    print("=" * 70)
    print(f"\nEstadisticas:")
    print(f"  Total archivos escaneados: {stats['total_files']}")
    print(f"  Archivos modificados: {stats['files_changed']}")
    print(f"  Total emojis eliminados: {stats['total_emojis_removed']}")
    
    if stats["files_processed"]:
        print(f"\nArchivos modificados:")
        for item in stats["files_processed"]:
            print(f"  - {item['file']}: {item['emojis_removed']} emojis")
    else:
        print("\n[OK] No se encontraron emojis en el codigo")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    print("Iniciando limpieza de emojis...\n")
    
    # Limpiar proyecto
    stats = clean_project("src")
    
    # Mostrar reporte
    print_report(stats)
    
    # Sugerencias finales
    if stats["files_changed"] > 0:
        print("\nProximos pasos:")
        print("  1. git add .")
        print('  2. git commit -m "refactor: eliminar emojis del codigo"')
        print("  3. git push team Jhon_Mantilla")