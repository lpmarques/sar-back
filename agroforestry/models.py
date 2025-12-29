from django.contrib.gis.db import models
from django.db.models.functions import Now
from catalog.models import Plant, Trait
from core.models import Content, Text, User
from geography.models import Biome, Country, Municipality, State, VegetationType
from agroforestry.querysets import FarmQuerySet, FieldQuerySet, SiteTraitQuerySet, SiteTraitValueQuerySet

class CroppingPatternCrop(models.Model):
    pk = models.CompositePrimaryKey('pattern_id', 'pattern_row_id', 'position')
    pattern = models.ForeignKey('CroppingPattern', models.DO_NOTHING)
    pattern_row = models.ForeignKey('CroppingPatternRow', models.DO_NOTHING)
    plant = models.ForeignKey(Plant, models.DO_NOTHING)
    position = models.IntegerField()
    distance_to_next_position_cm = models.IntegerField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."cropping_pattern_crops"'


class CroppingPatternRow(models.Model):
    pattern = models.ForeignKey('CroppingPattern', models.DO_NOTHING)
    purpose_text = models.ForeignKey(Text, models.DO_NOTHING)
    position = models.IntegerField()
    distance_to_next_position_cm = models.IntegerField()
    copied_row = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."cropping_pattern_rows"'
        unique_together = (('pattern', 'position'),)


class CroppingPattern(models.Model):
    name = models.CharField()
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField()
    public_content = models.OneToOneField(Content, models.DO_NOTHING, blank=True, null=True)
    copied_pattern = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    author = models.ForeignKey(User, models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."cropping_patterns"'
        unique_together = (('name', 'author'),)


class CroppingRowPurposeOption(models.Model):
    option_text = models.OneToOneField(Text, models.DO_NOTHING, db_comment='[diversidade, preenchimento, anuais, cobertura, outra]')
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."cropping_row_purpose_options"'


class RuleSet(models.Model):
    name = models.CharField()
    description = models.TextField(blank=True, null=True)
    logical_operator = models.CharField(blank=True, null=True)
    is_parent = models.BooleanField(blank=True, null=True)
    parent_rule_set = models.ForeignKey('self', models.DO_NOTHING, related_name='children_rule_sets', blank=True, null=True)
    copied_rule_set = models.ForeignKey('self', models.DO_NOTHING, related_name='copy_rule_sets', blank=True, null=True)
    author = models.ForeignKey(User, models.DO_NOTHING)
    public = models.BooleanField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."rule_sets"'
        unique_together = (('name', 'author'),)


class Rule(models.Model):
    rule_set = models.ForeignKey(RuleSet, models.DO_NOTHING)
    metric_name = models.CharField()
    metric_function = models.ForeignKey('Function', models.DO_NOTHING)
    metric_function_input = models.JSONField()
    metric_post_transforms = models.JSONField(blank=True, null=True)
    comparison_operator = models.CharField()
    threshold_constant = models.DecimalField(max_digits=10, decimal_places=5)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."rules"'


class Farm(models.Model):
    name = models.CharField()
    site = models.OneToOneField('Site', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)

    objects = FarmQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"agroforestry"."farms"'


class Field(models.Model):
    name = models.CharField()
    site = models.OneToOneField('Site', models.DO_NOTHING)
    farm = models.ForeignKey(Farm, models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    cropping_summary = models.JSONField(blank=True, null=True)
    cropping_geometry = models.JSONField(blank=True, null=True)
    cropping_pattern = models.ForeignKey(CroppingPattern, models.DO_NOTHING, blank=True, null=True)
    cropping_rule_set = models.ForeignKey(RuleSet, models.DO_NOTHING, blank=True, null=True)

    objects = FieldQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"agroforestry"."fields"'


class Function(models.Model):
    name = models.CharField(unique=True)
    arguments_schema = models.JSONField(blank=True, null=True)
    body = models.JSONField()
    return_schema = models.JSONField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."functions"'


class PlantSiteFitting(models.Model):
    pk = models.CompositePrimaryKey('plant_trait', 'site_trait')
    plant_trait = models.ForeignKey(Trait, models.DO_NOTHING)
    site_trait = models.ForeignKey('SiteTrait', models.DO_NOTHING)
    pre_transforms = models.JSONField(blank=True, null=True)
    fitting_function = models.ForeignKey(Function, models.DO_NOTHING)
    fitting_function_input = models.JSONField()
    fitting_weight = models.IntegerField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."plant_site_fitting"'


class Site(models.Model):
    class TYPE(models.TextChoices):
        FRM = "farm"
        FLD = "field"

    type = models.CharField(choices=TYPE.choices)
    location = models.PointField()
    polygon = models.GeometryField(blank=True, null=True)
    country = models.ForeignKey(Country, models.DO_NOTHING)
    state = models.ForeignKey(State, models.DO_NOTHING, blank=True, null=True)
    municipality = models.ForeignKey(Municipality, models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biome, models.DO_NOTHING, blank=True, null=True)
    vegetation_type = models.ForeignKey(VegetationType, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."sites"'


class SiteTrait(models.Model):
    name = models.CharField()
    name_text = models.ForeignKey(Text, models.DO_NOTHING, related_name='name_text_site_traits')
    section = models.CharField()
    section_text = models.ForeignKey(Text, models.DO_NOTHING, related_name='section_text_site_traits')
    description_text = models.OneToOneField(Text, models.DO_NOTHING, blank=True, null=True, related_name='description_text_site_traits')
    schema = models.JSONField()
    is_nullable = models.BooleanField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    text_value_options = models.ManyToManyField(Text, through='agroforestry.SiteTraitTextValueOption', through_fields=('trait', 'value_text'))

    objects = SiteTraitQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"agroforestry"."site_traits"'


class SiteTraitTextValueOption(models.Model):
    pk = models.CompositePrimaryKey('trait', 'value_text')
    trait = models.ForeignKey(SiteTrait, models.DO_NOTHING, related_name='site_trait_text_value_options')
    value_text = models.ForeignKey(Text, models.DO_NOTHING, related_name='site_trait_value_text_options')
    description_text = models.ForeignKey(Text, models.DO_NOTHING, blank=True, null=True, related_name='site_trait_description_text_options')
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"agroforestry"."site_trait_text_value_options"'


class SiteTraitValue(models.Model):
    site = models.ForeignKey(Site, models.DO_NOTHING, blank=True, null=True)
    trait = models.ForeignKey(SiteTrait, models.DO_NOTHING)
    value = models.CharField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    texts = models.ManyToManyField(Text, through='agroforestry.SiteTraitValueText')

    objects = SiteTraitValueQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"agroforestry"."site_trait_values"'
        unique_together = (('site', 'trait', 'deleted_at'),)


class SiteTraitValueText(models.Model):
    pk = models.CompositePrimaryKey('site_trait_value', 'text')
    site_trait_value = models.ForeignKey(SiteTraitValue, models.DO_NOTHING)
    text = models.ForeignKey(Text, models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = '"agroforestry"."site_trait_value_texts"'
