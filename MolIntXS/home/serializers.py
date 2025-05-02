from rest_framework import serializers
from django.core.serializers.json import DjangoJSONEncoder
import home.models as DBtables 


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, DBtables.Species):
            return str(obj)
        if isinstance(obj, DBtables.EnsemblGene):
            return str(obj)
        return super().default(obj)

class KeyValuePairSerializer(serializers.Serializer):
    interaction_id = serializers.IntegerField()
    meta_key_id = serializers.IntegerField()
    meta_value_id = serializers.IntegerField(source='key_value_id')
    key = serializers.CharField(source='meta_key.name')
    value = serializers.CharField()
    interactor_1 = serializers.CharField(source='interaction.interactor_1.curies')
    interactor_2 = serializers.CharField(source='interaction.interactor_2.curies')
    ensembl_gene_1 = serializers.CharField(source='interaction.interactor_1.ensembl_gene.ensembl_stable_id')
    ensembl_gene_2 = serializers.CharField(allow_null=True,source='interaction.interactor_2.ensembl_gene.ensembl_stable_id')
    species_1 = serializers.CharField(source='interaction.interactor_1.ensembl_gene.species.scientific_name')
    species_2 = serializers.CharField(allow_null=True,source='interaction.interactor_2.ensembl_gene.species.scientific_name')

    class Meta:
        model = DBtables.KeyValuePair

class CuratedInteractorSerializer(serializers.Serializer):
    curated_interactor_id = serializers.IntegerField()
    prod_name = serializers.CharField(allow_null=True,source='ensembl_gene.species.production_name')
    division = serializers.CharField(allow_null=True,source='ensembl_gene.species.ensembl_division')
    ens_gene = serializers.CharField(allow_null=True,source='ensembl_gene.ensembl_stable_id')
    curies = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    interactor_type = serializers.CharField()

    class Meta:
        model = DBtables.CuratedInteractor

class InteractionSerializer(serializers.Serializer):
    interaction_id = serializers.IntegerField()
    interactor_1 = serializers.CharField(source='interactor_1.curies')
    interactor_2 = serializers.CharField(source='interactor_2.curies')
    ensembl_gene_1 = serializers.CharField(allow_null=True,source='interactor_1.ensembl_gene.ensembl_stable_id')
    ensembl_gene_2 = serializers.CharField(allow_null=True,source='interactor_2.ensembl_gene.ensembl_stable_id')
    species_1 = serializers.CharField(allow_null=True,source='interactor_1.ensembl_gene.species.scientific_name')
    species_2 = serializers.CharField(allow_null=True,source='interactor_2.ensembl_gene.species.scientific_name')
    doi = serializers.CharField(style={'base_template': 'textarea.html'})
    source_db = serializers.CharField(source='source_db.label')
    
    class Meta:
        model = DBtables.Interaction

class SpeciesSerializer(serializers.Serializer):
    species_id = serializers.IntegerField()
    ensembl_division = serializers.CharField(required=True, allow_blank=False, max_length=255)
    ensembl_production_name = serializers.CharField(source='production_name',style={'base_template': 'textarea.html'})
    scientific_name = serializers.CharField(style={'base_template': 'textarea.html'})
    taxon_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DBtables.Species


class EnsemblGeneSerializer(serializers.Serializer):
    ensembl_gene_id = serializers.IntegerField(read_only=True)
    species_id = serializers.IntegerField(read_only=True)
    ensembl_stable_id = serializers.CharField(style={'base_template': 'textarea.html'})
    scientific_name = serializers.CharField(allow_null=True, source='species.scientific_name')
    production_name = serializers.CharField(allow_null=True, source='species.production_name')

    class Meta:
        model = DBtables.EnsemblGene
