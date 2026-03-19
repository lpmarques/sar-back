# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.contrib.gis.db.models.functions import Func, Transform
from django.contrib.gis.geos import Point
from django.db.models import FloatField

class ST_Value(Func):
    """
    Django ORM representation of the PostGIS ST_Value function.
    ST_Value(raster rast, integer band, geometry pt, boolean exclude_nodata_value)
    """
    function = 'ST_Value'
    output_field = FloatField()

    def __init__(self, raster_field: str, point_geometry: Point, band=1, **kwargs):
        # This tells GeoDjango to treat 'point_geometry' as a spatial object
        adapted_point = Transform(point_geometry, point_geometry.srid)

        super().__init__(raster_field, band, adapted_point, **kwargs)
