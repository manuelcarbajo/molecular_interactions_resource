# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models



class PredictionMethod(models.Model):
    prediction_method_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    parameters = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'prediction_method'


class Species(models.Model):
    species_id = models.AutoField(primary_key=True)
    ensembl_division = models.CharField(max_length=255)
    production_name = models.CharField(max_length=255, blank=True, null=True )
    scientific_name = models.CharField(max_length=255)
    taxon_id = models.IntegerField(unique=True)

    def __str__(self):
        return 'id: {}, division: {}, production_name: {}, scientific_name: {}, taxon_id: {}'.format(self.species_id,self.ensembl_division,str(self.production_name),self.scientific_name,self.taxon_id)

    class Meta:
        managed = True
        db_table = 'species'
        unique_together = (('scientific_name','production_name', 'taxon_id'),)


class EnsemblGene(models.Model):
    ensembl_gene_id = models.AutoField(primary_key=True)
    species = models.ForeignKey('Species', on_delete=models.DO_NOTHING)
    ensembl_stable_id = models.CharField(max_length=255, blank=True, null=True)
    import_timestamp = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'ensembl_gene'


class SourceDb(models.Model):
    source_db_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=255)
    external_db = models.CharField(max_length=255)
    original_curator_db = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'source_db'


class MetaKey(models.Model):
    meta_key_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    description = models.CharField(unique=True, max_length=255)

    def __str__(self):
        return 'id: {}, name: {}, description: {}'.format(str(self.meta_key_id),self.name,self.description)

    class Meta:
        managed = True
        db_table = 'meta_key'


class Ontology(models.Model):
    ontology_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    description = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = True
        db_table = 'ontology'


class OntologyTerm(models.Model):
    ontology_term_id = models.AutoField(primary_key=True)
    ontology = models.ForeignKey(Ontology, models.DO_NOTHING)
    accession = models.CharField(unique=True, max_length=255)
    description = models.CharField(unique=True, max_length=255)

    class Meta:
        managed = True
        db_table = 'ontology_term'


class CuratedInteractor(models.Model):

    InteractorType = models.TextChoices('InteractorType', 'protein gene mRNA synthetic')

    curated_interactor_id = models.AutoField(primary_key=True)
    interactor_type = models.CharField(max_length=9, choices=InteractorType.choices)
    curies = models.CharField(unique=True, max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    molecular_structure = models.CharField(max_length=10000, blank=True, null=True)
    import_timestamp = models.DateTimeField()
    ensembl_gene = models.ForeignKey('EnsemblGene', models.DO_NOTHING, null=True)

    class Meta:
        managed = True
        db_table = 'curated_interactor'


class PredictedInteractor(models.Model):
    predicted_interaction_id = models.AutoField(primary_key=True)
    curated_interactor = models.ForeignKey(CuratedInteractor, models.DO_NOTHING)
    interactor_type = models.CharField(max_length=9)
    prediction_method = models.ForeignKey('PredictionMethod', models.DO_NOTHING)
    curies = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    molecular_structure = models.CharField(max_length=10000, blank=True, null=True)
    predicted_timestamp = models.DateTimeField()
    ensembl_gene = models.ForeignKey(EnsemblGene, models.DO_NOTHING, null=True)

    class Meta:
        managed = True
        db_table = 'predicted_interactor'


class Interaction(models.Model):
    interaction_id = models.AutoField(primary_key=True)
    interactor_1 = models.ForeignKey('CuratedInteractor', models.DO_NOTHING, db_column='interactor_1', related_name='interaction_for_int1')
    interactor_2 = models.ForeignKey('CuratedInteractor', models.DO_NOTHING, db_column='interactor_2', related_name='interaction_for_int2')
    doi = models.CharField(max_length=255)
    source_db = models.ForeignKey('SourceDb', models.DO_NOTHING)
    import_timestamp = models.DateTimeField()

    def __str__(self):
        return 'id: {}, interactor_1: {}, interactor_2: {}, doi: {}, source_db:{}'.format(str(self.interaction_id),str(self.interactor_1),str(self.interactor_2),self.doi, str(self.source_db))

    class Meta:
        managed = True
        db_table = 'interaction'
        unique_together = (('interactor_1', 'interactor_2', 'doi', 'source_db'),)


class KeyValuePair(models.Model):
    key_value_id = models.AutoField(primary_key=True)
    interaction = models.ForeignKey(Interaction, models.DO_NOTHING)
    meta_key = models.ForeignKey('MetaKey', models.DO_NOTHING)
    value = models.CharField(max_length=255)
    ontology_term = models.ForeignKey('OntologyTerm', models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return 'id: {}, interaction: {}, meta_key: {}, value: {}, ontology_term: {}'.format(str(self.key_value_id),str(self.interaction),str(self.meta_key),self.value,str(self.ontology_term))

    class Meta:
        managed = True
        db_table = 'key_value_pair'
        unique_together = (('interaction', 'meta_key', 'value'),)


