#!/usr/bin/env bash

# Instalacja standardowych pakietów
pip install -r requirements.txt

# Instalacja niewidocznej przeglądarki Chromium dla Playwrighta
playwright install chromium
