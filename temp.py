import os
import subprocess
import shutil

SOURCE_DIR = "/Volumes/Plex/Processing/temp"
DEST_DIR = "/Volumes/Plex/Processing/temp_new"

def has_segment_uid(mkv_path):
    try:
        result = subprocess.run(["mkvinfo", mkv_path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        return "Segment UID" in result.stdout
    except Exception as e:
        print(f"[ERRO] Falha ao verificar UID em: {mkv_path} - {e}")
        return True  # Assume que tem UID para não reescrever por erro

def process_file(src_path, dst_path):
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    if has_segment_uid(src_path):
        print(f"[COPIANDO] {src_path} -> {dst_path} (UID já presente)")
        shutil.copy2(src_path, dst_path)
    else:
        print(f"[REESCREVENDO] {src_path} -> {dst_path} (sem UID)")
        subprocess.run(["mkvmerge", "-o", dst_path, src_path], check=True)

def main():
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.lower().endswith(".mkv"):
                src_path = os.path.join(root, file)
                relative_path = os.path.relpath(src_path, SOURCE_DIR)
                dst_path = os.path.join(DEST_DIR, relative_path)
                try:
                    process_file(src_path, dst_path)
                except Exception as e:
                    print(f"[ERRO] Falha ao processar {src_path} -> {e}")

if __name__ == "__main__":
    main()
