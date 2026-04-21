import os

if os.environ.get("CODESPACES") == "true":
    GOOGLE_REDIRECT_URI = "https://ubiquitous-space-memory-g4rgqppwvppv296p6-5000.app.github.dev/auth/google/callback"
else:
    GOOGLE_REDIRECT_URI = "http://localhost:5000/auth/google/callback"


GOOGLE_CLIENT_ID = "664495909279-5g3dldsa8h7t3pd45uk42bti3in9ampg.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

FLASK_SECRET_KEY = "4c7a8c6d6aa4fd1ad5d056febb6aae972ca20b85b30df14997febe4bd26767c6"
