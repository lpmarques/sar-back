from django.db import models
from django.db.models.functions import Now
from catalog.querysets import InvasionRiskRegionQuerySet, NaturalOccurrenceRegionQuerySet, PlantQuerySet, TraitQuerySet, TraitValueQuerySet
from core.models import Content, Text
from core.querysets import ContentQuerySet
from geography.models import Biome, Country, State, VegetationType

class Plant(models.Model):
    content = models.OneToOneField(Content, models.DO_NOTHING)
    accepted_taxon_name = models.CharField(blank=True, null=True)
    accepted_family_name = models.CharField(blank=True, null=True)
    color_hex = models.CharField(blank=True, null=True)

    objects = PlantQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."plants"'


class InvasionRiskRegion(models.Model):
    class EICAT(models.TextChoices):
        MO = "Moderate", "moderate"
        MR = "Major", "major"
        MV = "Massive", "massive"

    content = models.OneToOneField(Content, models.DO_NOTHING)
    taxon_name = models.CharField()
    plant = models.ForeignKey(Plant, models.DO_NOTHING, blank=True, null=True, related_name='invasion_risk_regions')
    country = models.ForeignKey(Country, models.DO_NOTHING)
    state = models.ForeignKey(State, models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biome, models.DO_NOTHING, blank=True, null=True)
    eicat_category = models.CharField(blank=True, null=True, choices=EICAT.choices)

    objects = InvasionRiskRegionQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."invasion_risk_regions"'


class NaturalOccurrenceRegion(models.Model):
    content = models.OneToOneField(Content, models.DO_NOTHING)
    plant = models.ForeignKey(Plant, models.DO_NOTHING, related_name='natural_occurrence_regions')
    country = models.ForeignKey(Country, models.DO_NOTHING)
    state = models.ForeignKey(State, models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biome, models.DO_NOTHING, blank=True, null=True)
    vegetation_type = models.ForeignKey(VegetationType, models.DO_NOTHING, blank=True, null=True)

    objects = NaturalOccurrenceRegionQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."natural_occurrence_regions"'


class PopularName(models.Model):
    content = models.OneToOneField(Content, models.DO_NOTHING)
    plant = models.ForeignKey(Plant, models.DO_NOTHING, related_name='popular_names')
    name = models.CharField()

    objects = ContentQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."popular_names"'


class Taxon(models.Model):
    class STATUS(models.TextChoices):
        ACC = "accepted"
        SYN = "synonym"

    content = models.OneToOneField(Content, models.DO_NOTHING)
    plant = models.ForeignKey(Plant, models.DO_NOTHING, related_name='taxa')
    family = models.CharField()
    genus = models.CharField()
    species = models.CharField()
    subspecies = models.CharField(blank=True, null=True)
    variety = models.CharField(blank=True, null=True)
    taxonomic_status = models.CharField(choices=STATUS.choices)

    objects = ContentQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."taxa"'


class Trait(models.Model):
    name = models.CharField()
    name_text = models.ForeignKey(Text, models.DO_NOTHING, related_name='name_text_traits')
    section = models.CharField(blank=True, null=True)
    section_text = models.ForeignKey(Text, models.DO_NOTHING, blank=True, null=True, related_name='section_text_traits')
    description_text = models.OneToOneField(Text, models.DO_NOTHING, blank=True, null=True, related_name='description_text_traits')
    data_type = models.CharField()
    schema = models.JSONField()
    is_nullable = models.BooleanField()
    is_site_specific = models.BooleanField()
    numeric_value_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    numeric_value_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    text_value_options = models.ManyToManyField(Text, through='TraitTextValueOption', through_fields=('trait', 'value_text'))

    objects = TraitQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."traits"'
        unique_together = (('name_text', 'section_text'),)


class TraitTextValueOption(models.Model):
    pk = models.CompositePrimaryKey('trait', 'value_text')
    trait = models.ForeignKey(Trait, models.DO_NOTHING, related_name='trait_text_value_options')
    value_text = models.ForeignKey(Text, models.DO_NOTHING, related_name='trait_value_text_options')
    description_text = models.ForeignKey(Text, models.DO_NOTHING, blank=True, null=True, related_name='trait_description_text_options')
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"catalog"."trait_text_value_options"'


class TraitValue(models.Model):
    content = models.OneToOneField(Content, models.DO_NOTHING, related_name='trait_value')
    plant = models.ForeignKey(Plant, models.DO_NOTHING, related_name='trait_values')
    trait = models.ForeignKey(Trait, models.DO_NOTHING)
    value = models.CharField()

    texts = models.ManyToManyField(Text, through='catalog.TraitValueText')

    objects = TraitValueQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"catalog"."trait_values"'


class TraitValueText(models.Model):
    pk = models.CompositePrimaryKey('trait_value', 'text')
    trait_value = models.ForeignKey(TraitValue, models.DO_NOTHING)
    text = models.ForeignKey(Text, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = '"catalog"."trait_values_texts"'
