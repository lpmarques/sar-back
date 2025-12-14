from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import IntegerField, QuerySet, Value, Prefetch
from geography.functions import ST_Value

class ClimateNormalQuerySet(QuerySet):
    def with_station_distance(self, point: Point):
        return self.annotate(
            station_distance_m=Value(Distance('location', point), output_field=IntegerField())
        )
    
    def get_nearest_station(self, point: Point, filters: dict):
        return self.annotate(
            station_distance_m=Distance('location', point)
        ).values(
            'station_code',
            'station_distance_m',
        ).filter(
            **filters
        ).order_by(
            'station_distance_m',
        ).first()
    
    def get_latest_year(self, filters: dict):
        return self.values(
            'period_last_year',
        ).filter(
            **filters
        ).order_by(
            '-period_last_year',
        ).first()

class CountryQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'name_text',
        )

class SoilAcidityLevelQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'name_text',
        )

class SoilPhMapQuerySet(QuerySet):
    def get_pixel_value(self, point: Point, filters: dict):
        return self.annotate(
            value=ST_Value('rast', point)
        ).filter(
            **filters
        ).first()

class SoilTextureTypeQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'name_text',
        )
