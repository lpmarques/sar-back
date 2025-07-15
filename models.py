# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.gis.db import models


class Biomes(models.Model):
    name = models.CharField()
    area = models.TextField()  # This field type is a guess.
    country = models.ForeignKey('Countries', models.DO_NOTHING)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'biomes'
        unique_together = (('name', 'country'),)


class ClimateNormals(models.Model):
    country = models.ForeignKey('Countries', models.DO_NOTHING)
    state = models.ForeignKey('States', models.DO_NOTHING, blank=True, null=True)
    municipality = models.ForeignKey('Municipalities', models.DO_NOTHING, blank=True, null=True)
    period_first_year = models.IntegerField(blank=True, null=True)
    period_last_year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    precipitation_mm = models.IntegerField(blank=True, null=True)
    temperature_c_average = models.IntegerField(blank=True, null=True)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'climate_normals'


class ContentEndorsements(models.Model):
    plant_value_id = models.IntegerField(blank=True, null=True)
    plant_popular_name_id = models.IntegerField(blank=True, null=True)
    plant_scientific_name_id = models.IntegerField(blank=True, null=True)
    content_type = models.CharField(db_comment='[plant_values, plant_popular_name, plant_scientific_name]')
    endorser = models.ForeignKey('Users', models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'content_endorsements'
        unique_together = (('plant_value_id', 'plant_popular_name_id', 'plant_scientific_name_id', 'endorser'),)


class Countries(models.Model):
    area = models.TextField()  # This field type is a guess.
    name_text_id = models.IntegerField(unique=True)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'countries'


class CroppingPatternPlants(models.Model):
    pk = models.CompositePrimaryKey('pattern_id', 'pattern_row_id', 'position')
    pattern = models.ForeignKey('CroppingPatterns', models.DO_NOTHING)
    pattern_row = models.ForeignKey('CroppingPatternRows', models.DO_NOTHING)
    position = models.IntegerField()
    plant_id = models.IntegerField()
    distance_to_next_plant_cm = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cropping_pattern_plants'


class CroppingPatternRows(models.Model):
    pattern = models.ForeignKey('CroppingPatterns', models.DO_NOTHING)
    position = models.IntegerField()
    purpose = models.CharField(db_comment='[diversidade, preenchimento, anuais, cobertura, outra]')
    distance_to_next_row_cm = models.IntegerField()
    copied_pattern_row = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cropping_pattern_rows'
        unique_together = (('pattern', 'position'),)


class CroppingPatterns(models.Model):
    name = models.CharField()
    description = models.TextField(blank=True, null=True)
    public = models.BooleanField()
    copied_pattern = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    author_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cropping_patterns'
        unique_together = (('name', 'author_id'),)


class CroppingRuleSets(models.Model):
    name = models.CharField()
    description = models.TextField(blank=True, null=True)
    logical_operator = models.CharField(blank=True, null=True)
    is_parent = models.BooleanField(blank=True, null=True)
    is_child = models.BooleanField(blank=True, null=True)
    parent_rule_set = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    copied_rule_set = models.ForeignKey('self', models.DO_NOTHING, related_name='croppingrulesets_copied_rule_set_set', blank=True, null=True)
    author_id = models.IntegerField()
    public = models.BooleanField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cropping_rule_sets'


class CroppingRules(models.Model):
    rule_set = models.ForeignKey(CroppingRuleSets, models.DO_NOTHING)
    metric_name = models.CharField()
    metric_function = models.ForeignKey('Functions', models.DO_NOTHING)
    metric_function_input = models.TextField()  # This field type is a guess.
    metric_post_transforms = models.TextField(blank=True, null=True)  # This field type is a guess.
    comparison_operator = models.CharField()
    threshold_constant = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cropping_rules'


class Farms(models.Model):
    name = models.CharField()
    perimeter = models.TextField(blank=True, null=True)  # This field type is a guess.
    gcs_central_point = models.TextField()  # This field type is a guess.
    country_id = models.IntegerField()
    state_id = models.IntegerField(blank=True, null=True)
    municipality_id = models.IntegerField(blank=True, null=True)
    biome_id = models.IntegerField(blank=True, null=True)
    vegetation_type_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'farms'
        unique_together = (('name', 'user_id'),)


class Fields(models.Model):
    farm = models.ForeignKey(Farms, models.DO_NOTHING)
    name = models.CharField()
    perimeter = models.TextField()  # This field type is a guess.
    cropping_summary = models.TextField(blank=True, null=True)  # This field type is a guess.
    cropping_geometry = models.TextField(blank=True, null=True)  # This field type is a guess.
    cropping_geometry_type = models.CharField(blank=True, null=True, db_comment='[grid, free lines]')
    cropping_pattern = models.ForeignKey(CroppingPatterns, models.DO_NOTHING, blank=True, null=True)
    cropping_rule_set = models.ForeignKey(CroppingRuleSets, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fields'
        unique_together = (('farm', 'name'),)


class Functions(models.Model):
    name = models.CharField()
    arguments = models.TextField(blank=True, null=True)  # This field type is a guess.
    body = models.TextField()  # This field type is a guess.
    return_type = models.CharField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'functions'


class MonthlyDroughtAreas(models.Model):
    country = models.ForeignKey(Countries, models.DO_NOTHING)
    state = models.ForeignKey('States', models.DO_NOTHING, blank=True, null=True)
    area = models.TextField()  # This field type is a guess.
    year = models.CharField()
    month = models.CharField()
    drought_level = models.CharField()
    drought_level_code = models.CharField(blank=True, null=True)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'monthly_drought_areas'


class Municipalities(models.Model):
    name = models.CharField()
    area = models.TextField()  # This field type is a guess.
    fiscal_module_size_sqrm = models.IntegerField(blank=True, null=True)
    state = models.ForeignKey('States', models.DO_NOTHING)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'municipalities'
        unique_together = (('name', 'state'),)


class PlantInvasionRiskRegions(models.Model):
    plant_scientific_name = models.CharField()
    plant = models.ForeignKey('Plants', models.DO_NOTHING, blank=True, null=True)
    country_id = models.IntegerField()
    state_id = models.IntegerField(blank=True, null=True)
    biome_id = models.IntegerField(blank=True, null=True)
    source_id = models.IntegerField()
    content_status = models.CharField(blank=True, null=True)
    content_author_id = models.IntegerField()
    content_author_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_invasion_risk_regions'
        unique_together = (('plant_scientific_name', 'plant', 'country_id', 'state_id', 'biome_id'),)


class PlantNaturalDistributionRegions(models.Model):
    plant = models.ForeignKey('Plants', models.DO_NOTHING)
    country_id = models.IntegerField()
    state_id = models.IntegerField(blank=True, null=True)
    biome_id = models.IntegerField(blank=True, null=True)
    vegetation_type_id = models.IntegerField(blank=True, null=True)
    source_id = models.IntegerField()
    content_status = models.CharField(blank=True, null=True)
    content_author_id = models.IntegerField()
    content_author_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_natural_distribution_regions'
        unique_together = (('plant', 'country_id', 'state_id', 'biome_id', 'vegetation_type_id'),)


class PlantPopularNames(models.Model):
    name = models.CharField()
    plant = models.ForeignKey('Plants', models.DO_NOTHING)
    content_status = models.CharField(blank=True, null=True, db_comment='[proposed, accepted, rejected]')
    content_author_id = models.IntegerField()
    content_author_comment = models.TextField(blank=True, null=True)
    source_id = models.IntegerField()
    endorsements = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_popular_names'
        unique_together = (('plant', 'name', 'content_status', 'rejected_at'),)


class PlantScientificNames(models.Model):
    name = models.CharField(unique=True)
    plant = models.ForeignKey('Plants', models.DO_NOTHING)
    taxonomic_status = models.CharField(db_comment='[accepted, synonym]')
    content_status = models.CharField(blank=True, null=True, db_comment='[proposed, accepted, rejected]')
    content_author_id = models.IntegerField()
    content_author_comment = models.TextField(blank=True, null=True)
    source_id = models.IntegerField()
    endorsements = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_scientific_names'
        unique_together = (('plant', 'name', 'content_status', 'rejected_at'),)


class PlantSiteFitting(models.Model):
    pk = models.CompositePrimaryKey('plant_trait_id', 'site_trait_id')
    plant_trait_id = models.IntegerField()
    site_trait = models.ForeignKey('SiteTraits', models.DO_NOTHING)
    pre_transforms = models.TextField(blank=True, null=True)  # This field type is a guess.
    fitting_function = models.ForeignKey(Functions, models.DO_NOTHING)
    fitting_function_input = models.TextField()  # This field type is a guess.
    fitting_weight = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_site_fitting'


class PlantTraitTextValueOptions(models.Model):
    pk = models.CompositePrimaryKey('plant_trait_id', 'option_text_id')
    plant_trait = models.ForeignKey('PlantTraits', models.DO_NOTHING)
    option_text_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_trait_text_value_options'


class PlantTraits(models.Model):
    name = models.CharField()
    name_text_id = models.IntegerField()
    section = models.CharField(blank=True, null=True)
    section_text_id = models.IntegerField(blank=True, null=True)
    data_type = models.CharField()
    is_nullable = models.BooleanField()
    is_site_specific = models.BooleanField()
    numeric_value_min = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    numeric_value_max = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_traits'
        unique_together = (('name', 'section'),)


class PlantValueTexts(models.Model):
    pk = models.CompositePrimaryKey('plant_value_id', 'text_id')
    plant_value = models.ForeignKey('PlantValues', models.DO_NOTHING)
    text_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'plant_value_texts'


class PlantValues(models.Model):
    plant = models.ForeignKey('Plants', models.DO_NOTHING)
    trait = models.ForeignKey(PlantTraits, models.DO_NOTHING)
    value = models.CharField()
    content_status = models.CharField(blank=True, null=True, db_comment='[proposed, accepted, rejected]')
    content_author_id = models.IntegerField()
    content_author_comment = models.TextField(blank=True, null=True)
    source_id = models.IntegerField()
    endorsements = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plant_values'
        unique_together = (('plant', 'trait', 'value', 'content_status', 'rejected_at'),)


class Plants(models.Model):
    accepted_scientific_name = models.CharField(unique=True)
    color_hex = models.CharField(unique=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'plants'


class SiteTraitTextValueOptions(models.Model):
    pk = models.CompositePrimaryKey('site_trait_id', 'option_text_id')
    site_trait = models.ForeignKey('SiteTraits', models.DO_NOTHING)
    option_text_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'site_trait_text_value_options'


class SiteTraits(models.Model):
    name = models.CharField(unique=True)
    type = models.CharField()
    nullable = models.BooleanField()
    values_range = models.TextField(blank=True, null=True)  # This field type is a guess.
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'site_traits'


class SiteValueTexts(models.Model):
    pk = models.CompositePrimaryKey('site_value_id', 'text_id')
    site_value = models.ForeignKey('SiteValues', models.DO_NOTHING)
    text_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'site_value_texts'


class SiteValues(models.Model):
    farm = models.ForeignKey(Farms, models.DO_NOTHING, blank=True, null=True)
    field = models.ForeignKey(Fields, models.DO_NOTHING, blank=True, null=True)
    site_type = models.CharField(db_comment='[field, farm]')
    trait = models.ForeignKey(SiteTraits, models.DO_NOTHING)
    value = models.CharField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'site_values'
        unique_together = (('farm', 'field', 'site_type', 'trait'),)


class SoilAcidityLevels(models.Model):
    name_text_id = models.IntegerField()
    ph_min = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    ph_max = models.DecimalField(max_digits=10, decimal_places=5)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'soil_acidity_levels'


class SoilPhMaps(models.Model):
    rast = models.TextField()  # This field type is a guess.
    filename = models.CharField(blank=True, null=True)
    country = models.ForeignKey(Countries, models.DO_NOTHING)
    state = models.ForeignKey('States', models.DO_NOTHING, blank=True, null=True)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'soil_ph_maps'


class SoilTextureAreas(models.Model):
    country = models.ForeignKey(Countries, models.DO_NOTHING)
    state = models.ForeignKey('States', models.DO_NOTHING, blank=True, null=True)
    area = models.TextField()  # This field type is a guess.
    texture = models.CharField()
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'soil_texture_areas'


class Sources(models.Model):
    name = models.CharField(unique=True, blank=True, null=True)
    type = models.CharField()
    year = models.IntegerField(blank=True, null=True)
    publication_title = models.CharField()
    publication_authors = models.TextField(blank=True, null=True)  # This field type is a guess.
    publisher = models.CharField(blank=True, null=True)
    url = models.CharField(blank=True, null=True)
    description = models.CharField(blank=True, null=True)
    content_author = models.ForeignKey('Users', models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sources'


class States(models.Model):
    name = models.CharField()
    code = models.CharField(blank=True, null=True)
    area = models.TextField()  # This field type is a guess.
    country = models.ForeignKey(Countries, models.DO_NOTHING)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'states'
        unique_together = (('name', 'country'),)


class Texts(models.Model):
    pt_br = models.CharField()
    en = models.CharField(blank=True, null=True)
    es = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'texts'


class Users(models.Model):
    first_name = models.CharField()
    last_name = models.CharField()
    email = models.CharField(unique=True)
    password = models.CharField()
    role = models.CharField(blank=True, null=True)
    occupation = models.CharField()
    company = models.CharField(blank=True, null=True)
    country_id = models.IntegerField(blank=True, null=True)
    state_id = models.IntegerField(blank=True, null=True)
    municipality_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(blank=True, null=True)
    is_staff = models.BooleanField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    is_verified = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'


class VegetationAreas(models.Model):
    country = models.ForeignKey(Countries, models.DO_NOTHING)
    state = models.ForeignKey(States, models.DO_NOTHING, blank=True, null=True)
    biome = models.ForeignKey(Biomes, models.DO_NOTHING, blank=True, null=True)
    area = models.TextField()  # This field type is a guess.
    vegetation_type = models.ForeignKey('VegetationTypes', models.DO_NOTHING)
    source_id = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vegetation_areas'


class VegetationTypes(models.Model):
    name = models.CharField()
    country = models.ForeignKey(Countries, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vegetation_types'
        unique_together = (('name', 'country'),)
