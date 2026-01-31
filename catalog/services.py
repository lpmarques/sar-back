from rest_framework.exceptions import NotFound
from catalog.models import Plant

def get_plant(plant_id: int):
    try:
        plant = Plant.objects.get(id=plant_id)
    except Plant.DoesNotExist:
        raise NotFound('Planta não encontrada.')
  
    return plant