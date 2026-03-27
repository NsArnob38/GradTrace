"""GradeTrace CLI launcher — just run: python gradetrace.py"""
import sys
import os

# Ensure we can find packages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from packages.cli.main import main
main()
