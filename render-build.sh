#!/bin/bash

# Install system dependencies for Tesseract & PDF processing
apt-get update && apt-get install -y tesseract-ocr poppler-utils
