from typing import List
from django.db import connection, transaction
from django.db.models.functions import Now
from rest_framework.exceptions import NotFound, PermissionDenied
from agroforestry.models import Farm, Field, Site, SiteTrait, SiteTraitValue
from agroforestry.queries import PlantsFitnessQuery
from agroforestry.utils import json_to_dict
from core.models import Text
import pandas as pd

def get_farm(farm_id, user_id, queryset=Farm.objects):
    try:
        farm = queryset.get(id=farm_id)
    except Farm.DoesNotExist:
        raise NotFound('Propriedade não cadastrada.')
    
    if farm.site.deleted_at:
        raise NotFound('Propriedade indisponível.')
    
    if farm.user_id != user_id:
        raise PermissionDenied('Você não tem autorização para acessar essa propriedade.')
    
    return farm
    
def delete_farm(farm: Farm, delete_ts=Now()):
    with transaction.atomic():
        fields = Field.objects.filter(farm_id=farm.id)
        for field in fields:
            delete_field(field, delete_ts)

        SiteTraitValue.objects.filter(site_id=farm.site_id).update(deleted_at=delete_ts)

        farm.site.deleted_at = delete_ts
        farm.site.save()

def get_field(field_id, user_id):
    try:
        field = Field.objects.get(id=field_id)
    except Field.DoesNotExist:
        raise NotFound('Área não cadastrada.')
    
    if field.site.deleted_at:
        raise NotFound('Área indisponível.')
    
    if field.user_id != user_id:
        raise PermissionDenied('Você não tem autorização para acessar essa área.')
    
    return field
    
def delete_field(field: Field, delete_ts=Now()):
    with transaction.atomic():
        SiteTraitValue.objects.filter(site_id=field.site_id).update(deleted_at=delete_ts)

        field.site.deleted_at = delete_ts
        field.site.save()

def get_site_owner_id(site: Site):
    if site.TYPE.FRM:
        return Farm.objects.get(site_id=site.id).user_id
    else:
        return Field.objects.get(site_id=site.id).farm.user_id
    
def get_trait_value(site_trait_value_id, user_id):        
    try:
        trait_value = SiteTraitValue.objects.get(id=site_trait_value_id)
    except SiteTraitValue.DoesNotExist:
        raise NotFound('Informação não encontrada.')
    
    if trait_value.deleted_at:
        raise NotFound('Informação indisponível.')

    if user_id != get_site_owner_id(trait_value.site):
        raise PermissionDenied('Você não tem autorização para acessar informação referentes a esse local.')
    
    return trait_value

def get_value_texts(trait: SiteTrait, value) -> List[Text]:
    if trait.schema['type'] == "array" and trait.schema['items']['type'] == "string":
        return Text.objects.filter(**{'pt_br__in': value})
    elif trait.schema['type'] == "string":
        return Text.objects.filter(**{'pt_br': value})

    return []

def get_site_plants_fitness_data(site_id: int, plant_id: int=None):
    query = PlantsFitnessQuery(site_id, plant_id)
    
    df = query.execute()

    df['site_trait_schema'] = df['site_trait_schema'].apply(json_to_dict)
    df['fitting_pre_transforms'] = df['fitting_pre_transforms'].apply(json_to_dict)
    df['fitting_function_input'] = df['fitting_function_input'].apply(json_to_dict)

    plant_ids = df.index.get_level_values('plant_id')

    if plant_id:
        return df

    return [df[plant_ids == pid] for pid in plant_ids.unique()]
