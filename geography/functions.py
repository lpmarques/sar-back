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
