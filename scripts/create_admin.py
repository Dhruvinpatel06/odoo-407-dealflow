"""Root forwarder for backend/scripts/create_admin.py."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(REPO_ROOT) == "scripts":
    REPO_ROOT = os.path.dirname(REPO_ROOT)

BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

sys.path.insert(0, os.path.join(BACKEND_DIR, "scripts"))
import create_admin

if __name__ == "__main__":
    create_admin.main()
