#!/usr/bin/env python3
"""
Ollama Helper Script - Auto-start Ollama if needed
"""

import subprocess
import time
import requests
import os
import signal
import sys

# ✅ Get Ollama host from environment variable
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
OLLAMA_URL = f"http://{OLLAMA_HOST}"

def is_ollama_running():
    """Check if Ollama server is running."""
    try:
        response = requests.get(OLLAMA_URL, timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def start_ollama_server():
    """Start Ollama server if not running."""
    if is_ollama_running():
        print(f"✅ Ollama server is already running on {OLLAMA_HOST}")
        return True
    
    print(f"🚀 Starting Ollama server on {OLLAMA_HOST}...")
    try:
        # Start Ollama in background with the correct host
        env = os.environ.copy()
        env['OLLAMA_HOST'] = OLLAMA_HOST
        
        # Use full path to ensure we get the correct Ollama version
        ollama_path = os.path.expanduser('~/.local/bin/ollama')
        if not os.path.exists(ollama_path):
            ollama_path = 'ollama'  # Fallback to system PATH
        
        process = subprocess.Popen([ollama_path, 'serve'], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL,
                                 env=env)
        
        # Wait for server to start
        for i in range(10):
            time.sleep(1)
            if is_ollama_running():
                print(f"✅ Ollama server started successfully on {OLLAMA_HOST}!")
                return True
            print(f"   Waiting for server... ({i+1}/10)")
        
        print("❌ Ollama server failed to start within 10 seconds")
        return False
        
    except FileNotFoundError:
        print("❌ Ollama not found. Please install it first:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        return False
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False

def check_and_start_ollama(auto_start=True):
    """Check if Ollama is running, optionally start it."""
    if is_ollama_running():
        print(f"✅ Ollama server is running on {OLLAMA_HOST}")
        return True
    
    if auto_start:
        print("🔧 Ollama server not running. Attempting to start...")
        return start_ollama_server()
    else:
        print("❌ Ollama server is not running!")
        print("💡 Start it manually with: ollama serve &")
        print("   Or run this script with auto-start: python ollama_helper.py --start")
        return False

def stop_ollama_server():
    """Stop Ollama server."""
    try:
        # Find Ollama processes
        result = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"🛑 Stopped Ollama process {pid}")
        print("✅ Ollama server stopped")
    except Exception as e:
        print(f"❌ Error stopping Ollama: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ollama Helper Script")
    parser.add_argument("--start", action="store_true", help="Start Ollama server")
    parser.add_argument("--stop", action="store_true", help="Stop Ollama server")
    parser.add_argument("--check", action="store_true", help="Check if Ollama is running")
    args = parser.parse_args()
    
    if args.stop:
        stop_ollama_server()
    elif args.start:
        start_ollama_server()
    elif args.check:
        if is_ollama_running():
            print("✅ Ollama is running")
            sys.exit(0)
        else:
            print("❌ Ollama is not running")
            sys.exit(1)
    else:
        print("🔧 Ollama Helper")
        print("================")
        check_and_start_ollama(auto_start=True)
