import requests
import os
import main  # Your processing module

# Configuration
PASSWORD = "your-hardcoded-password-here"

def main(INURL, PROCESSID):
    # Setup paths
    home_dir = os.path.expanduser("~")
    input_path = os.path.join(home_dir, f"VIDEOIN#{PROCESSID}.mp4")
    output_path = os.path.join(home_dir, f"OUT#{PROCESSID}.json")
    
    headers = {"Authorization": PASSWORD}

    try:
        # 1. Download (GET)
        print(f"[*] Downloading: {PROCESSID}")
        with requests.get(INURL, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(input_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # 2. Process
        print(f"[*] Processing: {input_path}")
        run.main(input_path)

        # 3. Upload File Directly (POST)
        if os.path.exists(output_path):
            print(f"[*] Uploading result: {output_path}")
            with open(output_path, 'rb') as f:
                # We send the raw file handle. 'requests' streams it automatically.
                up_res = requests.post(
                    INURL, 
                    headers=headers, 
                    data=f 
                )
            up_res.raise_for_status()
            print("[+] Done.")
        else:
            print(f"[!] Error: {output_path} was not created.")

    except Exception as e:
        print(f"[!] Worker Error: {e}")
    
    finally:
        # Cleanup
        for p in [input_path, output_path]:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    # Example: main("https://your-service.loca.lt/gateway/101", "101")
    pass