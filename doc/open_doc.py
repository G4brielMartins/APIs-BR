#!/usr/bin/env python3
import os

html_path = os.path.abspath("doc/apisbr/index.html")
html_url = "file://" + html_path

os.system(f'python -m webbrowser "{html_url}"')