from django.db import connection
import pandas as pd

class PlantsFitnessQuery:
    QUERY_TEMPLATE = """
        select 
            p.id as plant_id,
            p.accepted_taxon_name,
            p.color_hex,
            case when max(nor.id) is not null then true else false end as is_native,
            case when max(irr.id) is not null then true else false end as is_invasive,
            max(irr.eicat_category) as eicat_category,
            st.name as site_trait_slug,
            st.schema as site_trait_schema,
            max(stv.value) as site_trait_value,
            array_agg(distinct stvtt.pt_br) filter (where stvtt.pt_br is not null) as site_trait_text_values,
            pt.name as plant_trait_slug,
            pt.data_type as plant_trait_type,
            max(ptv.value) as plant_trait_value,
            array_agg(distinct ptvtt.pt_br) filter (where ptvtt.pt_br is not null) as plant_trait_text_values,
            psf.pre_transforms as fitting_pre_transforms,
            f.name as fitting_function_name,
            psf.fitting_function_input,
            psf.fitting_weight
        from agroforestry.plant_site_fitting psf
        join agroforestry.functions f on f.id = psf.fitting_function_id
        join agroforestry.site_traits st on st.id = psf.site_trait_id
        join agroforestry.site_trait_values stv on stv.trait_id = st.id
        join agroforestry.sites s on s.id = stv.site_id
        left join agroforestry.site_trait_value_texts stvt on stvt.site_trait_value_id = stv.id
        left join core.texts stvtt on stvtt.id = stvt.text_id
        join catalog.traits pt on pt.id = psf.plant_trait_id
        join catalog.trait_values ptv on ptv.trait_id = pt.id
        join core.contents ptvc
            on ptvc.id = ptv.content_id
            and ptvc.status = 'accepted'
        join catalog.plants p on p.id = ptv.plant_id
        left join catalog.trait_values_texts ptvt on ptvt.trait_value_id = ptv.id
        left join core.texts ptvtt on ptvtt.id = ptvt.text_id
        left join catalog.natural_occurrence_regions nor
            on nor.plant_id = p.id
            and nor.country_id = s.country_id
            and (nor.state_id = s.state_id or nor.state_id is null)
            and (nor.biome_id = s.biome_id or nor.biome_id is null)
            and (nor.vegetation_type_id = s.vegetation_type_id or nor.vegetation_type_id is null)
        left join catalog.invasion_risk_regions irr
            on irr.plant_id = p.id
            and irr.country_id = s.country_id
            and (irr.state_id = s.state_id or nor.state_id is null)
            and (irr.biome_id = s.biome_id or nor.biome_id is null)
        where s.id = %s
        {plant_filter_snippet}
        group by
            p.id,
            psf.site_trait_id,
            psf.plant_trait_id,
            f.id,
            st.id,
            pt.id
    """

    PLANT_FILTER_SNIPPET = "and p.id = %s"

    INDEX_COLUMN_NAMES = [   
        'plant_id',
        'accepted_taxon_name',
        'color_hex',
        'is_native',
        'is_invasive',
        'eicat_category',
    ]

    COLUMN_NAMES = INDEX_COLUMN_NAMES + [
        'site_trait_slug',
        'site_trait_schema',
        'site_trait_value',
        'site_trait_text_values',
        'plant_trait_slug',
        'plant_trait_type',
        'plant_trait_value',
        'plant_trait_text_values',
        'fitting_pre_transforms',
        'fitting_function_name',
        'fitting_function_input',
        'fitting_weight',
    ]

    def __init__(self, site_id: int, plant_id: int=None):
        self.sql = self.QUERY_TEMPLATE.format_map({
            'plant_filter_snippet': self.PLANT_FILTER_SNIPPET if plant_id else ""
        })
        self.params = [site_id]
        if plant_id:
            self.params.append(plant_id)

    def execute(self):
        with connection.cursor() as cursor:
            cursor.execute(self.sql, self.params)
            df = pd.DataFrame(cursor.fetchall(), columns=self.COLUMN_NAMES)

        return df.set_index(self.INDEX_COLUMN_NAMES)
