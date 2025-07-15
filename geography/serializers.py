from rest_framework.serializers import ModelSerializer, CharField, SlugRelatedField
from geography.models import Country, Municipality, State

class CountrySerializer(ModelSerializer):
    name = SlugRelatedField(read_only=True, source='name_text', slug_field='pt_br')

    class Meta:
        model = Country
        fields = [
            'id',
            'name',
        ]
    
class StateSerializer(ModelSerializer):
    name = CharField()
    code = CharField()
    country = CountrySerializer(read_only=True)

    class Meta:
        model = State
        fields = [
            'id',
            'name',
            'code',
            'country',
        ]

class MunicipalitySerializer(ModelSerializer):
    name = CharField()
    state = StateSerializer(read_only=True)
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Municipality
        fields = [
            'id',
            'name',
            'state',
            'country',
        ]
