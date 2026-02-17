import os

def get_dir_size(start_path='.'):
    all_files = []
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    size = os.path.getsize(fp)
                    if size > 1024 * 1024: # > 1MB
                        all_files.append((fp, size))
                except OSError:
                    pass
    
    all_files.sort(key=lambda x: x[1], reverse=True)
    print(f"{'Path':<60} | {'Size (MB)':<10}")
    print("-" * 75)
    for p, s in all_files:
        print(f"{p:<60} | {s/1024/1024:>10.2f}")

if __name__ == "__main__":
    get_dir_size()
