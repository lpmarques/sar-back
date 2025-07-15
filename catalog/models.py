from django.db import models
from django.db.models.functions import Now
from core.models import Source, User, Text
from geography.models import Biome, Country, State, VegetationType

class Plant(models.Model):
    accepted_scientific_name = models.CharField(unique=True)
    color_hex = models.CharField(unique=True)
    content_status = models.CharField(db_default='proposed', db_comment='[proposed, accepted, rejected]')
    content_author = models.ForeignKey(User, models.DO_NOTHING)
    content_author_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    accepted_at = models.DateTimeField(db_default=Now())
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plants"'


class PlantInvasionRiskRegion(models.Model):
    plant_scientific_name = models.CharField()
    plant = models.ForeignKey(Plant, models.DO_NOTHING, blank=True, null=True)
    country = models.ForeignKey(Country, models.DO_NOTHING)
    state = models.ForeignKey(State, models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biome, models.DO_NOTHING, blank=True, null=True)
    source = models.ForeignKey(Source, models.DO_NOTHING)
    content_status = models.CharField(db_default='proposed')
    content_author = models.ForeignKey(User, models.DO_NOTHING)
    content_author_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_invasion_risk_regions"'
        unique_together = (('plant_scientific_name', 'plant', 'country', 'state', 'biome'),)


class PlantNaturalDistributionRegion(models.Model):
    plant = models.ForeignKey(Plant, models.DO_NOTHING)
    country = models.ForeignKey(Country, models.DO_NOTHING)
    state = models.ForeignKey(State, models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biome, models.DO_NOTHING, blank=True, null=True)
    vegetation_type = models.ForeignKey(VegetationType, models.DO_NOTHING, blank=True, null=True)
    source = models.ForeignKey(Source, models.DO_NOTHING)
    content_status = models.CharField(db_default='proposed', db_comment='[proposed, accepted, rejected]')
    content_author = models.ForeignKey(User, models.DO_NOTHING)
    content_author_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_natural_distribution_regions"'
        unique_together = (('plant', 'country', 'state', 'biome', 'vegetation_type'),)


class PlantPopularName(models.Model):
    name = models.CharField()
    plant = models.ForeignKey(Plant, models.DO_NOTHING, related_name='popular_names')
    content_status = models.CharField(db_default='proposed', db_comment='[proposed, accepted, rejected]')
    content_author = models.ForeignKey(User, models.DO_NOTHING)
    content_author_comment = models.TextField(blank=True, null=True)
    source = models.ForeignKey(Source, models.DO_NOTHING)
    endorsements = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_popular_names"'
        unique_together = (('plant', 'name', 'content_status', 'rejected_at'),)


class PlantScientificName(models.Model):
    name = models.CharField(unique=True)
    plant = models.ForeignKey(Plant, models.DO_NOTHING, related_name='scientific_names')
    taxonomic_status = models.CharField(db_comment='[accepted, synonym]')
    content_status = models.CharField(db_default='proposed', db_comment='[proposed, accepted, rejected]')
    content_author = models.ForeignKey(User, models.DO_NOTHING)
    content_author_comment = models.TextField(blank=True, null=True)
    source = models.ForeignKey(Source, models.DO_NOTHING)
    endorsements = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_scientific_names"'
        unique_together = (('plant', 'name', 'content_status', 'rejected_at'),)


class PlantTrait(models.Model):
    name = models.CharField()
    name_text = models.ForeignKey(Text, models.DO_NOTHING, related_name='trait_name_text')
    section = models.CharField(blank=True, null=True)
    section_text = models.ForeignKey(Text, models.DO_NOTHING, blank=True, null=True)
    data_type = models.CharField()
    is_nullable = models.BooleanField()
    is_site_specific = models.BooleanField()
    numeric_value_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    numeric_value_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_traits"'
        unique_together = (('name', 'section'),)


class PlantTraitTextValueOption(models.Model):
    pk = models.CompositePrimaryKey('plant_trait_id', 'option_text')
    plant_trait = models.ForeignKey(PlantTrait, models.DO_NOTHING)
    option_text = models.ForeignKey(Text, models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_trait_text_value_options"'


class PlantValue(models.Model):
    plant = models.ForeignKey(Plant, models.DO_NOTHING)
    trait = models.ForeignKey(PlantTrait, models.DO_NOTHING)
    value = models.CharField()
    content_status = models.CharField(db_default='proposed', db_comment='[proposed, accepted, rejected]')
    content_author = models.ForeignKey(User, models.DO_NOTHING)
    content_author_comment = models.TextField(blank=True, null=True)
    source = models.ForeignKey(Source, models.DO_NOTHING)
    endorsements = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"catalog"."plant_values"'
        unique_together = (('plant', 'trait', 'value', 'content_status', 'rejected_at'),)


class PlantValueText(models.Model):
    pk = models.CompositePrimaryKey('plant_value', 'text')
    plant_value = models.ForeignKey(PlantValue, models.DO_NOTHING)
    text = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"catalog"."plant_value_texts"'
