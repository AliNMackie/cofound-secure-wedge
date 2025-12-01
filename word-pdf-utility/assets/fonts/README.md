# Font Directory

This directory contains custom fonts used by WeasyPrint for PDF generation.

## Adding Fonts

Place your `.ttf` or `.otf` font files in this directory. The Dockerfile will automatically:
1. Copy these fonts to `/usr/share/fonts/truetype/custom` in the container
2. Run `fc-cache` to update the font cache

## Note

A placeholder file is included to ensure this directory is tracked by Git. Replace with your actual font files before deployment.
