import uvicorn
import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    port = int(os.environ.get("PORT", 8000))
    print(f"\n========================================================")
    print(f"🦷 Dental Assistant Copilot - Clinical AI Chatbot")
    print(f"🚀 Running locally on: http://localhost:{port}")
    print(f"🔗 Also available at: http://127.0.0.1:{port}")
    print(f"========================================================\n")
    uvicorn.run("backend.server:app", host="127.0.0.1", port=port, reload=False)

if __name__ == "__main__":
    main()
