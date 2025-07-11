from django.db.models.functions import Now
from django.contrib.gis.db import models as models
from core.models import Source, Text


class Biome(models.Model):
    name = models.CharField()
    area = models.GeometryField()
    country = models.ForeignKey('Country', on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."biomes"'
        unique_together = (('name', 'country'),)


class ClimateNormal(models.Model):
    country = models.ForeignKey('Country', on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    municipality = models.ForeignKey('Municipality', on_delete=models.DO_NOTHING, blank=True, null=True)
    period_first_year = models.IntegerField(blank=True, null=True)
    period_last_year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    precipitation_mm = models.IntegerField(blank=True, null=True)
    temperature_c_average = models.IntegerField(blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."climate_normals"'


class Country(models.Model):
    area = models.GeometryField()
    name_text = models.OneToOneField(Text, on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."countries"'


class MonthlyDroughtArea(models.Model):
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    area = models.GeometryField()
    year = models.CharField()
    month = models.CharField()
    drought_level = models.CharField()
    drought_level_code = models.CharField(blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."monthly_drought_areas"'


class Municipality(models.Model):
    name = models.CharField()
    area = models.GeometryField()
    fiscal_module_size_sqrm = models.IntegerField(blank=True, null=True)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."municipalities"'
        unique_together = (('name', 'state'),)


class SoilAcidityLevel(models.Model):
    name_text = models.ForeignKey(Text, on_delete=models.DO_NOTHING)
    ph_min = models.DecimalField(max_digits=3, decimal_places=1)
    ph_max = models.DecimalField(max_digits=3, decimal_places=1)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."soil_acidity_levels"'


class SoilPhMap(models.Model):
    rast = models.RasterField()
    filename = models.CharField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."soil_ph_maps"'


class SoilTextureArea(models.Model):
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    state = models.ForeignKey('State', on_delete=models.DO_NOTHING, blank=True, null=True)
    area = models.GeometryField()
    texture = models.CharField()
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."soil_texture_areas"'


class State(models.Model):
    name = models.CharField()
    code = models.CharField(blank=True, null=True)
    area = models.GeometryField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."states"'
        unique_together = (('name', 'country'),)


class VegetationArea(models.Model):
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    state = models.ForeignKey(State, on_delete=models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biome, on_delete=models.DO_NOTHING, blank=True, null=True)
    area = models.GeometryField()
    vegetation_type = models.ForeignKey('VegetationType', on_delete=models.DO_NOTHING)
    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."vegetation_areas"'


class VegetationType(models.Model):
    name = models.CharField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"geography"."vegetation_types"'
        unique_together = (('name', 'country'),)
