import os

def find_large_files(root='.', threshold_mb=0.5):
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if '.git' in dirpath: continue
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                size = os.path.getsize(fp)
                if size > threshold_mb * 1024 * 1024:
                    all_files.append((fp, size))
            except: pass
    
    all_files.sort(key=lambda x: x[1], reverse=True)
    print(f"{'File Path':<60} | {'Size (MB)':<10}")
    print("-" * 75)
    for path, size in all_files[:40]:
        print(f"{path:<60} | {size/1024/1024:>10.2f}")

if __name__ == "__main__":
    find_large_files()
