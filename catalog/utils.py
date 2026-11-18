# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

import hashlib
import io
import os
import uuid
from PIL import Image, ImageOps
from django.core.files.uploadedfile import InMemoryUploadedFile
from catalog.models import Image as PlantImage


def string_to_md5(string):
    return hashlib.md5(string.encode('utf-8')).hexdigest()

def md5_to_color(md5):
    return "#" + md5[-6:]

def none_if_empty(value: str):
    value = value.strip()
    if len(value) == 0:
        return None

    return value

def strip_exif_metadata(image_file):
    # 1. Abre a imagem usando o Pillow
    img = Image.open(image_file)
    img_format = img.format

    # 2. Mantém a orientação correta da imagem antes de limpar os metadados
    img = ImageOps.exif_transpose(img)
    
    output_buffer = io.BytesIO()
    # 3. Salva a imagem no formato original (JPEG, PNG, etc.) SEM os metadados EXIF
    img.save(output_buffer, format=img_format if img_format else 'JPEG')
    output_buffer.seek(0)
    
    # 4. Reconstrói o arquivo no formato que o Django espera receber
    cleaned_file = InMemoryUploadedFile(
        file=output_buffer,
        field_name=image_file.field_name,
        name=image_file.name,
        content_type=image_file.content_type,
        size=output_buffer.getbuffer().nbytes,
        charset=image_file.charset
    )
    
    return cleaned_file
