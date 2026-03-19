# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.functions import Now
from geography.querysets import ClimateNormalQuerySet, CountryQuerySet, SoilAcidityLevelQuerySet, SoilPhMapQuerySet, SoilTextureTypeQuerySet
from core.models import Source, Text

class Biome(models.Model):
    name = models.CharField()
    area = models.GeometryField()
    country = models.ForeignKey('Country', on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."biomes"'
        unique_together = (('name', 'country'),)


class ClimateNormal(models.Model):
    station_code = models.IntegerField()
    country = models.ForeignKey('Country', on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    location = models.PointField()
    elevation_m = models.IntegerField()
    period_first_year = models.IntegerField(blank=True, null=True)
    period_last_year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    precipitation_mm = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=1)
    temperature_c_minimum = models.DecimalField(blank=True, null=True, max_digits=3, decimal_places=1)
    temperature_c_average = models.DecimalField(blank=True, null=True, max_digits=3, decimal_places=1)
    temperature_c_maximum = models.DecimalField(blank=True, null=True, max_digits=3, decimal_places=1)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    objects = ClimateNormalQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"geography"."climate_normals"'


class Country(models.Model):
    area = models.GeometryField()
    name_text = models.OneToOneField(Text, on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    objects = CountryQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"geography"."countries"'


class MonthlyDroughtArea(models.Model):
    class DROUGHT_LEVEL(models.TextChoices):
        L0 = "Si", "ausente"
        L1 = "S0", "fraca"
        L2 = "S1", "moderada"
        L3 = "S2", "grave"
        L4 = "S3", "extrema"
        L5 = "S4", "excepcional"

    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    area = models.GeometryField()
    year = models.IntegerField()
    month = models.IntegerField()
    drought_level = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    drought_level_code = models.CharField(blank=True, null=True, choices=DROUGHT_LEVEL.choices)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."monthly_drought_areas"'


class Municipality(models.Model):
    name = models.CharField()
    fiscal_module_size_sqrm = models.IntegerField(blank=True, null=True)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."municipalities"'
        unique_together = (('name', 'state'),)


class SoilAcidityLevel(models.Model):
    name_text = models.OneToOneField(Text, on_delete=models.DO_NOTHING)
    ph_min = models.DecimalField(max_digits=3, decimal_places=1)
    ph_max = models.DecimalField(max_digits=3, decimal_places=1)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    objects = SoilAcidityLevelQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"geography"."soil_acidity_levels"'


class SoilPhMap(models.Model):
    rast = models.RasterField()
    tile_extent = models.GeometryField()
    valued_extent = models.GeometryField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    objects = SoilPhMapQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"geography"."soil_ph_maps"'


class SoilTextureArea(models.Model):
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    texture_type = models.ForeignKey('SoilTextureType', on_delete=models.DO_NOTHING, related_name='soil_texture_areas')
    area = models.GeometryField()
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."soil_texture_areas"'


class SoilTextureType(models.Model):
    name_text = models.OneToOneField(Text, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    objects = SoilTextureTypeQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"geography"."soil_texture_types"'


class State(models.Model):
    name = models.CharField()
    code = models.CharField(blank=True, null=True)
    area = models.GeometryField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."states"'
        unique_together = (('name', 'country'),)


class VegetationArea(models.Model):
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, related_name='vegetation_areas')
    state = models.ForeignKey(State, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='vegetation_areas')
    biome = models.ForeignKey(Biome, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='vegetation_areas')
    vegetation_type = models.ForeignKey('VegetationType', on_delete=models.DO_NOTHING, related_name='vegetation_areas')
    area = models.GeometryField(blank=True, null=True) # temporarily nullable to save space by storing only Mata Atlântica polygons
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."vegetation_areas"'


class VegetationType(models.Model):
    name = models.CharField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"geography"."vegetation_types"'
        unique_together = (('name', 'country'),)
