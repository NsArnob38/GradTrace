import sys
import os
from dotenv import load_dotenv

# Load local environment variables (.env)
load_dotenv()

# Ensure we can find packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packages.cli.main import main
main()
