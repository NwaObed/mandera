"""
Loads the project .env file exactly once.

Every per-service settings module imports this module for its side
effect (`from config import env`), so environment variables are
available no matter which settings module is imported first.
"""

from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(Path(__file__).parent.parent / ".env")