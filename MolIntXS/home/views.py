from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from django.core.serializers import serialize
from rest_framework.mixins import (
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, status
import home.models as DBtables
from .models import Species, EnsemblGene, MetaKey, KeyValuePair
from home.serializers import SpeciesSerializer, InteractionSerializer, EnsemblGeneSerializer, CuratedInteractorSerializer, KeyValuePairSerializer
from .serializers import LazyEncoder
import json
from json import JSONEncoder
import numpy as np
import django_filters
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime
from django.db.models import Q, Prefetch


class KeyValuePairFilter(django_filters.FilterSet):
    meta_value_id = django_filters.NumberFilter(method='meta_value_id_filter', field_name="meta_value_id", label="meta-value id")
    meta_value = django_filters.CharFilter(method='meta_value_filter',field_name="meta_value", lookup_expr='icontains', label="meta-value")
    meta_key_id = django_filters.NumberFilter(method='meta_key_id_filter', field_name='meta_key_id', label="meta-key id")
    meta_key = django_filters.CharFilter(method='meta_key_filter', field_name='meta_key',lookup_expr='icontains', label="meta-key")
    interaction_id = django_filters.NumberFilter(method='interaction_id_filter',field_name='interaction_id')
    #source_db = django_filters.CharFilter(method='source_db_filter', field_name='source_db_id')
    #interactor_id = django_filters.NumberFilter(method='any_interactor_filter', field_name='interactor_id',label="interactor id")

    class Meta:
        model = DBtables.KeyValuePair
        fields = ['meta_key','meta_value','interaction_id','meta_key_id','meta_value_id']
        ordering = ['interaction_id']

    def meta_value_id_filter(self,queryset,key_value_id,value):
        return queryset.filter(key_value_id=value)

    def meta_value_filter(self,queryset,meta_value,value):
        return queryset.filter(value__icontains=value)
    
    def meta_key_id_filter(self,queryset,meta_key_id,value):
        return queryset.filter(meta_key_id=value)

    def meta_key_filter(self,queryset,meta_key,value):
        return queryset.filter(meta_key__name__icontains=value)

    def interaction_id_filter(self,queryset,interaction_id,value):
        return queryset.filter(interaction_id=value)

class KeyValuePairList(generics.ListAPIView):
    queryset = DBtables.KeyValuePair.objects.select_related('interaction','interaction__interactor_1','interaction__interactor_2','interaction__interactor_1__ensembl_gene','interaction__interactor_2__ensembl_gene','interaction__interactor_1__ensembl_gene__species','interaction__interactor_2__ensembl_gene__species').select_related('meta_key')
    filterset_class = KeyValuePairFilter
    serializer_class = KeyValuePairSerializer
    
    @swagger_auto_schema(operation_description="* \n\t\t\tReturns a list of metadata (key-value pairs) associated with their interactions.\n\t\t\tThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.\n\n\tOne or multiple additional parameters can be passed with the following format:  /metadata?param1={value1}&param2={value2}&param3={value3}" +
    "\n\n\t\t* ?meta_key={string} \n\t\t\tReturns a list of metadata associated to their interactions, and having a meta key that case insensitive matches the provided string \n\t\t\t(ie.- '/meta_data?meta_key=experimental evidence')." +
    "\n\n\t\t* ?meta_value={string} \n\t\t\tReturns a list of metadata associated to their interactions, and having a meta value, case insensitive matching the provided string \n\t\t\t(ie.- '/meta_data?meta_value=two hybrid)." +
    "\n\n\t\t* ?interaction_id={integer} \n\t\t\t Returns all metadata associated to a specific interaction identified  by an integer \n\t\t\t(ie.- '/meta_data?interaction_id=116').\n" + 
    "\n\n\t\t* ?meta_key_id={integer} \n\t\t\tReturns a list of metadata associated to their interactions, and having a meta_key identified by the integer passed as a parameter \n\t\t\t(ie.- '/meta_data?meta_key_id=15')." +
    "\n\n\t\t* ?meta_value_id={integer} \n\t\t\tReturns a list of metadata associated to their interactions, and having a meta_ identified by the integer passed as a parameter \n\t\t\t(ie.- '/meta_data?meta_value_id=106827')."
    )
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EnsemblGeneFilter(django_filters.FilterSet):
  
    ensembl_gene_id = django_filters.NumberFilter( field_name='ensembl_gene_id')
    ensembl_stable_id = django_filters.CharFilter(method='ensembl_gene_filter',label='ensembl stable id', lookup_expr='icontains')
    ensembl_production_name = django_filters.CharFilter(method='species_ensembl_name_filter', label='species ensembl production name', field_name='ensembl_production_name')
    scientific_name = django_filters.CharFilter(method='species_scientific_name_filter', field_name='scientific_name', label='species scientific name')
    
    class Meta:
        model = DBtables.EnsemblGene
        fields = ['ensembl_gene_id','ensembl_stable_id','ensembl_production_name','scientific_name']

    
    def ensembl_gene_filter(self,queryset,ensembl_stable_id,value):
        return queryset.filter(ensembl_stable_id__icontains=value)
    
    def species_ensembl_name_filter(self,queryset,ensembl_production_name,value):
        return queryset.filter(species__production_name__icontains=value)
    
    def species_scientific_name_filter(self,queryset,scientific_name,value):
        return queryset.filter(species__scientific_name__icontains=value)

    def interactor_id_filter(self,queryset,interactor_id,value):
        return queryset.filter(curated_interactor_id=value)

class EnsemblGeneList(generics.ListAPIView):
    queryset = DBtables.EnsemblGene.objects.select_related('species').all()
    filterset_class = EnsemblGeneFilter
    serializer_class = EnsemblGeneSerializer
    
    
    @swagger_auto_schema(operation_description="* /ensembl_gene \n\t\t\tReturns a list of ensembl_genes associated to interactions data.\n\t\t\tThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.\n\n\tOne or multiple additional parameters can be passed with the following format:  /ensembl_gene?param1={value1}&param2={value2}&param3={value3}" + 
            "\n\n\t\t* ?ensembl_production_name={string} \n\t\t\tReturns a list of all genes belonging to one or several  species genomes with the ensembl name (aka production name) that insensitive matches the provided string" + 
            "\n\t\t\t(ie.- '/ensembl_gene?ensembl_production_name=zymoseptoria_tritici')." + 
            "\n\n\t\t* ?scientific_name={string} \n\t\t\tReturns a list of all genes belonging to one or several species genomes with the scientific name that insensitive matches the provided string" + 
            " \n\t\t\t(ie.- '/ensembl_gene?scientific_name=zymoseptoria tritici')." + 
            "\n\n\t\t* ?ensembl_gene_id={integer} \n\t\t\tReturns the ensembl_gene corresponding to the integer identifier passed as a parameter" +
            " \n\t\t\t(ie.- '/ensembl_gene?ensembl_gene_id=24664')." + 
            " \n\n\t\t* ?ensembl_stable_id={string} \n\t\t\tReturns the ensembl_gene corresponding to the stable_id passed as a string parameter." + 
            "\n\t\t\t(ie.- '/ensembl_gene?ensembl_stable_id=Mycgr3G105487').  \n")
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



class CuratedInteractorFilter(django_filters.FilterSet):
  
    name = django_filters.CharFilter(method='name_filter', lookup_expr='icontains')
    ensembl_gene = django_filters.CharFilter(method='ensembl_gene_filter', lookup_expr='icontains',label='ensembl gene')
    interactor_id = django_filters.NumberFilter(method='interactor_id_filter',field_name='interactor_id', label='interactor id')
    production_name = django_filters.CharFilter(method='species_ensembl_name_filter', label='species ensembl name (production name)', field_name='production_name')
    scientific_name = django_filters.CharFilter(method='species_scientific_name_filter', field_name='scientific_name', label='species scientific name')
    
    class Meta:
        model = DBtables.CuratedInteractor
        fields = ['name','ensembl_gene','interactor_id','production_name','scientific_name']

    def name_filter(self,queryset,name,value):
        return queryset.filter(name__icontains=value)
    
    def ensembl_gene_filter(self,queryset,ensembl_gene,value):
        return queryset.filter(ensembl_gene__ensembl_stable_id__icontains=value)
    
    def species_ensembl_name_filter(self,queryset,production_name,value):
        return queryset.filter(ensembl_gene__species__production_name__icontains=value)
    
    def species_scientific_name_filter(self,queryset,scientific_name,value):
        return queryset.filter(ensembl_gene__species__scientific_name__icontains=value)

    def interactor_id_filter(self,queryset,interactor_id,value):
        return queryset.filter(curated_interactor_id=value)

class CuratedInteractorList(generics.ListAPIView):

    queryset = DBtables.CuratedInteractor.objects.select_related('ensembl_gene').select_related('ensembl_gene__species').all()
    filterset_class = CuratedInteractorFilter
    serializer_class = CuratedInteractorSerializer
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_description="* /interactor \n\t\t\tReturns a list of interactor objects involved in a molecular interaction.\n\t\t\tThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.\n\n\tOne or multiple additional parameters can be passed with the following format:  /interactor?param1={value1}&param2={value2}&param3={value3}\n\n\t\t* ?name={string} \n\t\t\tReturns a list of all interactors with case insensitive matches to the provided string (ie.- '/interactor?name=P51587').\n\n\t\t* ?ensembl_gene={string} \n\t\t\tReturns a list of all interactors annotated to the ensembl gene identifier provided as a string (ie.- '/interactors?ensembl_gene=ENSG00000139618).\n\n\t\t* ?production_name={string} \n\t\t Returns a list of all interactors annotated to a given species identified by its ensembl name (aka production_name) (ie.-/interactor?production_name=homo_sapiens) \n\n\t\t* ?scientific_name={string} \n\t\t Returns a list of all interactors annotated to a given species identified by its scientific name (ie.- '/interactor?scientific_name=Homo sapiens')\n\n\t\t* ?interactor_id={integer} \n\t\t\tReturns the interactor identified by the integer passed as a parameter(ie.- '/interactor?interactor_id=15').\n")
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class InteractionFilter(django_filters.FilterSet):
    meta_key = django_filters.CharFilter(method='meta_key_filter', lookup_expr='icontains', label="meta key")
    meta_value = django_filters.CharFilter(method='meta_value_filter', lookup_expr='icontains',label="meta value")
    interaction_id = django_filters.NumberFilter(method='interaction_id_filter',field_name='interaction_id')
    source_db = django_filters.CharFilter(method='source_db_filter', field_name='source_db_id')
    interactor_name = django_filters.CharFilter(method='any_interactor_filter', field_name='interactor_name',label="interactor name")
    ensembl_gene = django_filters.CharFilter(method='any_gene_filter', field_name='ensembl_stable_id',label="ensembl stable id")
    species_A = django_filters.CharFilter(method='any_species_filter', lookup_expr='icontains',field_name='species_A',label="species A")
    species_B = django_filters.CharFilter(method='any_species_filter', lookup_expr='icontains',field_name='species_B',label="species B")

    class Meta:
        model = DBtables.Interaction
        fields = ['interaction_id','interactor_name','ensembl_gene','species_A','species_B','source_db','meta_value','meta_key']

    def source_db_filter(self,queryset,source_db_id,value):
        return queryset.filter(source_db__label__icontains=value)
    
    def meta_value_filter(self,queryset,meta_value,value):
        return queryset.filter(keyvaluepair__value__icontains=value)
    
    def meta_key_filter(self,queryset,meta_key,value):
        return queryset.filter(keyvaluepair__meta_key__name__icontains=value)

    def interaction_id_filter(self,queryset,interaction_id,value):
        return queryset.filter(interaction_id=value)

    def any_interactor_filter(self,queryset,name,value):
        return queryset.filter(
                Q(interactor_1__name=value) |
                Q(interactor_2__name=value)
            )

    def any_gene_filter(self,queryset,ensembl_stable_id,value):
        return queryset.filter(
                Q(interactor_1__ensembl_gene__ensembl_stable_id=value) |
                Q(interactor_2__ensembl_gene__ensembl_stable_id=value) 
            )
    def any_species_filter(self,queryset,scientific_name,value):
        return queryset.filter(
                Q(interactor_1__ensembl_gene__species__scientific_name__icontains=value) |
                Q(interactor_2__ensembl_gene__species__scientific_name__icontains=value) 
            )

class InteractionList(generics.ListAPIView):
    queryset = DBtables.Interaction.objects.select_related('source_db').select_related('interactor_1','interactor_1__ensembl_gene__species').select_related('interactor_2','interactor_2__ensembl_gene__species').prefetch_related(
            Prefetch('keyvaluepair_set', queryset=KeyValuePair.objects.select_related('meta_key'))
        )
    filterset_class = InteractionFilter
    serializer_class = InteractionSerializer
    
    @swagger_auto_schema(operation_description="* /interaction\n\t\t\tReturns a list of interaction objects annotated with molecular interaction metadata.\n\t\t\tThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.\n\n\tOne or multiple additional parameters can be passed with the following format:  /interaction?param1={value1}&param2={value2}&param3={value3}" + 
            "\n\n\t\t* ?interaction_id={integer} \n\t\t\tReturns a list of interactions annotated with key value pairs with the provided integer interaction identifier." + 
            "\n\t\t\t(ie.- '/interaction?interaction_id=15') " + 
            "\n\n\t\t* ?meta_key={string} \n\t\t\tReturns a list of all interactions having a meta key that case insensitive matches the provided string. " + 
            "\n\t\t\t(ie.- '/interaction?meta_key=experimental evidence')" + 
            "\n\n\t\t* ?meta_value={string} \n\t\t\tReturns a list of all interactions having a meta value, case insensitive matching the provided string." + 
            "\n\t\t\t(ie.- '/interaction?meta_value=two hybrid)." + 
            "\n\n\t\t* ?interactor_name={string} \n\t\t\t Returns a list of interactions involving a specific interactor name passed as a string parameter." + 
            "\n\t\t\t(ie.- '/interaction?interactor_name=O42773') " + 
            "\n\n\t\t* ?ensembl_gene={string} \n\t\t\t Returns a list of interactions involving a specific ensembl stable id passed as a string parameter." + 
            "\n\t\t\t(ie.- '/interaction?ensembl_gene=CNJ02230') " + 
            "\n\n\t\t* ?species_A={string} \n\t\t\t Returns a list of interactions involving species having a scientific name matching the string passed as a parameter." + 
            "\n\t\t\t(ie.- '/interaction?species_A=Oryctolagus cuniculus') " + 
            "\n\n\t\t* ?species_B={string} \n\t\t\t Returns a list of interactions involving a second species having a scientific name matching the string passed as a parameter." + 
            "\n\t\t\t(ie.- '/interaction?species_B=Cryptococcus neoformans') " + 
            "\n\n\t\t* ?source_db={string} \n\t\t\t Returns a list of interactions having been sourced from a specific string described by the string passed as a parameter." + 
            "\n\t\t\t(ie.- '/interaction?source_db=PHI-base')\n" 
            )
    
    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class SpeciesFilter(django_filters.FilterSet):
    
    scientific_name = django_filters.CharFilter(method='sc_name_filter',lookup_expr='icontains')
    ensembl_production_name = django_filters.CharFilter(method='prod_name_filter',field_name='ensembl_production_name',lookup_expr='icontains',label='species_production_name')
    species_id = django_filters.CharFilter(method='sp_id_filter')


    class Meta:
        model = Species
        fields = ['species_id','scientific_name','ensembl_production_name']
    
    def sc_name_filter(self,queryset,scientific_name,value):
        return queryset.filter(scientific_name__icontains=value)
    
    def prod_name_filter(self,queryset,ensembl_production_name,value):
        return queryset.filter(production_name__icontains=value)
    
    def sp_id_filter(self,queryset,species_id,value):
        return queryset.filter(species_id=value)

class SpeciesList(generics.ListAPIView):
    queryset = DBtables.Species.objects.all()
    filterset_class = SpeciesFilter
    serializer_class = SpeciesSerializer

    @swagger_auto_schema(operation_description="* /species \n\t\t\tReturns a list of species objects annotated with a molecular interaction.\n\t\t\tThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.\n\n\tOne or multiple additional parameters can be passed with the following format:/species?param1={value1}&param2={value2}&param3={value3}\n\n\t\t" + 
            "* ?species_id={integer} \n\t\t\tReturns all the information available for the species with the provided integer identifier" + 
            "\n\t\t\t(ie.- '/species?species_id=15').\n\n\t\t" + 
            "* ?scientific_name={string}\n\t\t\tReturns a list of species loosely matching a specific scientific name passed as a parameter using the case non sensitive format: genus species" + 
            "\n\t\t\t(ie.- '/species?scientific_name=homo sapiens')\n\n\t\t" + 
            " * ?species_production_name={string} \n\t\t\tReturns a list of species matching a specific Ensembl species name (also known as production name) passed as a parameter using the case non sensitive format: genus_species" + 
            "\n\t\t\t(ie.- '/species?ensembl_production_name=homo_sapiens')\n")
    def get(self,request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        response = serializer.data
        return Response(response) 

@swagger_auto_schema(method='get',operation_description="Returns a list of species objects annotated with a molecular interaction.\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def species(request):
    species_query_set = DBtables.Species.objects.all()
    species_dict = {}

    for s in species_query_set:
        species_dict[s.species_id] = {"species_id":s.species_id,
                                      "ensembl_production_name":s.production_name,
                                      "scientific_name":s.scientific_name,
                                      "ensembl_division":s.ensembl_division,
                                      "taxon_id":s.taxon_id}
    json_species = json.dumps(species_dict)
    return HttpResponse(json_species)


@swagger_auto_schema(method='get',operation_description="Returns a species object containing all the information available for the species with the provided identifier (int).")
@api_view(['GET'])
def species_id(request, species_id):
    species_list = DBtables.Species.objects.filter(species_id=species_id)
    json_species = serialize('jsonl', species_list, cls=LazyEncoder)  

    return HttpResponse(json_species)

@swagger_auto_schema(method='get',operation_description="Returns a list of species objects containing all the information available for a specific Ensembl species name (also known as production name) passed as a parameter using the case non sensitive format: genus_species (ie.- 'homo sapiens')")
@api_view(['GET'])
def species_by_ensembl_name(request, species_production_name):
    species_query_set = DBtables.Species.objects.filter(production_name__icontains=species_production_name)
    species_dict = {}

    for s in species_query_set:
        species_dict[s.species_id] = {"species_id":s.species_id,
                                      "ensembl_production_name":s.production_name,
                                      "scientific_name":s.scientific_name,
                                      "ensembl_division":s.ensembl_division,
                                      "taxon_id":s.taxon_id}
    json_species = json.dumps(species_dict)
    return HttpResponse(json_species)

@swagger_auto_schema(method='get',operation_description="Returns a list of species objects with all the information available for a specific species scientific name passed as a parameter using the case non sensitive format: genus species (ie.- 'homo sapiens')")
@api_view(['GET'])
def species_by_scientific_name(request, species_scientific_name):
    species_query_set = DBtables.Species.objects.filter(scientific_name__icontains=species_scientific_name) 
    species_dict = {}

    for s in species_query_set:
        species_dict[s.species_id] = {"species_id":s.species_id,
                                      "ensembl_production_name":s.production_name,
                                      "scientific_name":s.scientific_name,
                                      "ensembl_division":s.ensembl_division,
                                      "taxon_id":s.taxon_id}
    json_species = json.dumps(species_dict)
    return HttpResponse(json_species)


@swagger_auto_schema(method='get',operation_description="Returns a list of all meta_value objects available.\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def meta_values(request):
    metaval_query_set = DBtables.KeyValuePair.objects.select_related('meta_key').select_related('ontology_term').all()
    
    metaval_dict = {}

    for mv in metaval_query_set:
        metaval_dict[mv.key_value_id] = {"meta_value_id":mv.key_value_id,
                                         "interaction_id":mv.interaction_id,
                                         "meta_key_id":mv.meta_key_id,
                                         "meta_key_name":mv.meta_key.name,
                                         "meta_value":mv.value,
                                         "ontology_term_id":mv.ontology_term_id}
        if mv.ontology_term_id:
            metaval_dict[mv.key_value_id].update({"ontology_term": mv.ontology_term.description})
    json_metavals = json.dumps(metaval_dict)
    return HttpResponse(json_metavals)



@swagger_auto_schema(method='get',operation_description="Returns a list of all meta_key objects available.\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def meta_keys(request):
    metakey_query_set = DBtables.MetaKey.objects.all()
    metakey_dict = {}

    for mk in metakey_query_set:
        metakey_dict[mk.meta_key_id] = {"meta_key_id":mk.meta_key_id,
                                        "name":mk.name,
                                        "description":mk.description}
    json_metakeys = json.dumps(metakey_dict)
    return HttpResponse(json_metakeys)


@swagger_auto_schema(method='get',operation_description="Returns a list of all Ensembl gene objects annotated with a molecular interaction.\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def ensembl_gene(request):
    gene_query_set = DBtables.EnsemblGene.objects.select_related('species').all() 
    gene_dict = {}

    for g in gene_query_set:
        gene_dict[g.ensembl_gene_id] = {"ensembl_gene_id":g.ensembl_gene_id,
                                         "species_id":g.species_id,
                                         "species_scientific_name":g.species.scientific_name,
                                         "ensembl_stable_id":g.ensembl_stable_id }
    json_genes = json.dumps(gene_dict)
    return HttpResponse(json_genes)

@swagger_auto_schema(method='get',operation_description="Returns all molecular interactors (listed by their Ensembl species name, also known as production name).\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def ensembl_gene_by_prodname(request):
    
    species_genes_List = []
    ensembl_gene_query_set = DBtables.EnsemblGene.objects.select_related('species')

    species_gene_dict = {}
    for eg in ensembl_gene_query_set:
        if 'UNDETERMINED' not in eg.ensembl_stable_id:
            prod_name = eg.species.production_name
            if prod_name in species_gene_dict:
                genes_list = species_gene_dict[prod_name]
                genes_list.append(eg.ensembl_stable_id)
                species_gene_dict[prod_name] = genes_list
            else:
                species_gene_dict[prod_name] = [eg.ensembl_stable_id]
    json_species_genes = json.dumps(species_gene_dict)
    return HttpResponse(json_species_genes)

@swagger_auto_schema(method='get',operation_description="+Returns a list of all external databases from which we have imported molecular interaction.")
@api_view(['GET'])
def source_dbs(request):
    source_db_query_set = DBtables.SourceDb.objects.all()
    
    db_dict = {}

    for db in source_db_query_set:
        db_dict[db.source_db_id] = {"source_db_id":db.source_db_id,
                                    "label":db.label,
                                    "external_db":db.external_db,
                                    "original_curator_db":db.original_curator_db}
    json_dbs = json.dumps(db_dict)
    return HttpResponse(json_dbs)

@swagger_auto_schema(method='get',operation_description="Returns all interactor objects (uniquely identified by their curies).\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def interactors(request):
    interactors_query_set = DBtables.CuratedInteractor.objects.all()
    interactors_dict = {}

    for ci in interactors_query_set:
        interactors_dict[ci.curated_interactor_id] = {"curated_interactor_id":ci.curated_interactor_id,
                                                      "curies":ci.curies,
                                                      "interactor_type":ci.interactor_type,
                                                      "name":ci.name,
                                                      "ensembl_gene_id":ci.ensembl_gene_id}
    json_interactors = json.dumps(interactors_dict)
    return HttpResponse(json_interactors)

@swagger_auto_schema(method='get',operation_description="Returns the interactors identified by the integer passed as a parameter")
@api_view(['GET'])
def interactor_id(request, curated_interactor_id):
    
    interactors_query_set = DBtables.CuratedInteractor.objects.filter(curated_interactor_id=curated_interactor_id)
    interactors_dict = {}
    
    for i in interactors_query_set:
        interactors_dict[i.curated_interactor_id] = {"curated_interactor_id":i.curated_interactor_id,
                                                     "interactor_type":i.interactor_type,
                                                     "curies":i.curies,
                                                     "name":i.name,
                                                     "ensembl_gene_id":i.ensembl_gene_id}
    json_interactors = json.dumps(interactors_dict)
    return HttpResponse(json_interactors)

@swagger_auto_schema(method='get',operation_description="Returns the interactor with a curies name matching the string passed as a parameter. A normal name can also be passed (ie.- 'uniprot:Q6KC79' or 'Q6KC79' will return the same result)  ")
@api_view(['GET'])
def interactor_name(request, interactor_name):
    
    interactors_query_set = DBtables.CuratedInteractor.objects.filter(curies__icontains=interactor_name)
    interactors_dict = {}
    
    for i in interactors_query_set:
        interactors_dict[i.curated_interactor_id] = {"curated_interactor_id":i.curated_interactor_id,
                                                     "interactor_type":i.interactor_type,
                                                     "curies":i.curies,
                                                     "name":i.name,
                                                     "ensembl_gene_id":i.ensembl_gene_id}
    json_interactors = json.dumps(interactors_dict)
    return HttpResponse(json_interactors)


@swagger_auto_schema(method='get',operation_description="Returns the interactors associated to a specific ensembl_gene passed as a string parameter")
@api_view(['GET'])
def interactor_ensembl_gene(request, ensembl_gene):
    
    interactors_query_set = DBtables.CuratedInteractor.objects.filter(ensembl_gene__ensembl_stable_id=ensembl_gene)
    interactors_dict = {}
    
    for i in interactors_query_set:
        interactors_dict[i.curated_interactor_id] = {"curated_interactor_id":i.curated_interactor_id,
                                                     "interactor_type":i.interactor_type,
                                                     "curies":i.curies,
                                                     "name":i.name,
                                                     "ensembl_gene_id":i.ensembl_gene_id}
    json_interactors = json.dumps(interactors_dict)
    return HttpResponse(json_interactors)

@swagger_auto_schema(method='get',operation_description="Returns all the interactors tha belong to a specific species identified by its Ensembl name (also known as production name) passed as a parameter using the case non sensitive format: genus_species (ie.- 'homo_sapiens')")
@api_view(['GET'])
def interactor_by_specific_prodname(request, production_name):
    
    interactors_query_set = DBtables.CuratedInteractor.objects.filter(ensembl_gene__species__production_name__icontains=production_name)
    interactors_dict = {}
    
    for i in interactors_query_set:
        interactors_dict[i.curated_interactor_id] = {"curated_interactor_id":i.curated_interactor_id,
                                                     "interactor_type":i.interactor_type,
                                                     "curies":i.curies,
                                                     "name":i.name,
                                                     "ensembl_gene_id":i.ensembl_gene_id}
    json_interactors = json.dumps(interactors_dict)
    return HttpResponse(json_interactors)

@swagger_auto_schema(method='get',operation_description="Returns all the interactors tha belong to a specific species identified by its scientific name, passed as a parameter using the case non sensitive format: genus species (ie.- 'homo sapiens')")
@api_view(['GET'])
def interactor_by_scientific_name(request, scientific_name):
    
    interactors_query_set = DBtables.CuratedInteractor.objects.filter(ensembl_gene__species__scientific_name__icontains=scientific_name)
    interactors_dict = {}
    
    for i in interactors_query_set:
        interactors_dict[i.curated_interactor_id] = {"curated_interactor_id":i.curated_interactor_id,
                                                     "interactor_type":i.interactor_type,
                                                     "curies":i.curies,
                                                     "name":i.name,
                                                     "ensembl_gene_id":i.ensembl_gene_id}
    json_interactors = json.dumps(interactors_dict)
    return HttpResponse(json_interactors)


@swagger_auto_schema(method='get',operation_description="Returns all interactions listed by their primary_key (uniquely identified by a combination of interactor_1,interactor_2, DOI publication, and source_db).\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def interaction(request):
    interactions_query_set = DBtables.Interaction.objects.select_related('interactor_1').select_related('interactor_2').select_related('source_db').all()
    interactions_dict = {}
    for i in interactions_query_set:
        interactions_dict[i.interaction_id] = {"interaction_id":i.interaction_id,
                                               "interactor_1":i.interactor_1.curies,
                                               "interactor_2":i.interactor_2.curies,
                                               "doi":i.doi,
                                               "source_db":i.source_db.label}
    json_interactions = json.dumps(interactions_dict)
    return HttpResponse(json_interactions)


@swagger_auto_schema(method='get',operation_description="Returns all molecular interactions (listed by Ensembl species).\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
@api_view(['GET'])
def interactions_by_prodname(request):
    
    species_genes_List = []
    ensembl_gene_query_set = DBtables.EnsemblGene.objects.select_related('species')

    species_gene_dict = {}
    for eg in ensembl_gene_query_set:
        if 'UNDETERMINED' not in eg.ensembl_stable_id:
            prod_name = eg.species.production_name
            if prod_name in species_gene_dict:
                genes_list = species_gene_dict[prod_name]
                genes_list.append(eg.ensembl_stable_id)
                species_gene_dict[prod_name] = genes_list
            else:
                species_gene_dict[prod_name] = [eg.ensembl_stable_id]
    json_species_genes = json.dumps(species_gene_dict)
    return HttpResponse(json_species_genes)


@swagger_auto_schema(method='get',operation_description="Returns all molecular interactions (listed by their identifier) involving an interactor (on either side of the interaction) identified by the integer as a parameter (ie.- '116' will return interactions having the protein Q44643 as either interactor_1 or interactor_2).")
@api_view(['GET'])
def interactions_by_interactor_id(request, interactor_id):
    keyval_query_set = DBtables.KeyValuePair.objects.select_related('interaction__interactor_1','interaction__interactor_2','interaction__source_db').filter(Q (interaction__interactor_1=interactor_id)|Q(interaction__interactor_2=interactor_id))
    interactions_dict = {}
    for kv in keyval_query_set:
        interactions_dict[kv.interaction.interaction_id] = {"interaction_id":kv.interaction.interaction_id,
                                                            "interactor_1":kv.interaction.interactor_1.curies,
                                                            "interactor_2":kv.interaction.interactor_2.curies,
                                                            "doi":kv.interaction.doi,
                                                            "source_db":kv.interaction.source_db.label,
                                                            }
    json_interactions = json.dumps(interactions_dict)
    return HttpResponse(json_interactions)


@swagger_auto_schema(method='get',operation_description="Returns all molecular interactions (listed by their identifier) having the string passed as a parameter, contained in their meta_data as a key (ie.- 'disease').\nThe interactions returned will contain keys in their metadata that contain the specified string either in their name or their description. For instance, a search for 'disease' will match the meta_key name 'Disease name' but also the meta_key name 'Interaction phenotype' since its corresponding description 'Interaction phenotype/disease outcome' matches the query")
@api_view(['GET'])
def interactions_by_meta_key(request, meta_key):
    keyval_query_set = DBtables.KeyValuePair.objects.select_related('interaction__interactor_1','interaction__interactor_2','interaction__source_db').select_related('meta_key').filter(Q(meta_key__name__icontains=meta_key)|Q(meta_key__description__icontains=meta_key))
    interactions_dict = {}
    for kv in keyval_query_set:
        interactions_dict[kv.interaction.interaction_id] = {"interaction_id":kv.interaction.interaction_id,
                                                            "interactor_1":kv.interaction.interactor_1.curies,
                                                            "interactor_2":kv.interaction.interactor_2.curies,
                                                            "doi":kv.interaction.doi,
                                                            "source_db":kv.interaction.source_db.label,
                                                            "meta_key_name":kv.meta_key.name,
                                                            "meta_key_description":kv.meta_key.description,
                                                            "meta_value":kv.value,
                                                            }
    json_interactions = json.dumps(interactions_dict)
    return HttpResponse(json_interactions)


@swagger_auto_schema(method='get',operation_description="Returns all molecular interactions (listed by their identifier) having the string passed as a parameter, contained in their meta_data as a value (ie.- 'PHIPO:0000010', which is the corresponding ontology id for alternaria leaf blotch).")
@api_view(['GET'])
def interactions_by_meta_value(request, meta_value):
    keyval_query_set = DBtables.KeyValuePair.objects.select_related('interaction__interactor_1','interaction__interactor_2','interaction__source_db').select_related('meta_key').filter(value__icontains=meta_value)
    interactions_dict = {}
    for kv in keyval_query_set:
        interactions_dict[kv.interaction.interaction_id] = {"interaction_id":kv.interaction.interaction_id,
                                                            "interactor_1":kv.interaction.interactor_1.curies,
                                                            "interactor_2":kv.interaction.interactor_2.curies,
                                                            "doi":kv.interaction.doi,
                                                            "source_db":kv.interaction.source_db.label,
                                                            "meta_key_name":kv.meta_key.name,
                                                            "meta_key_description":kv.meta_key.description,
                                                            "meta_key_value":kv.value
                                                            }
    json_interactions = json.dumps(interactions_dict)
    return HttpResponse(json_interactions)



@swagger_auto_schema(method='get',operation_description="Returns all molecular interactions (listed by their identifier) having the first string passed as a parameter, contained in their meta_data as a key AND the second string passed as a parameter in their meta_data as a value (ie- key='disease' AND value='PHIPO:0000010').\nThe interactions returned will contain keys and values in their metadata that contain the specified strings either in their name or their description. For instance, a search for 'disease' will match the meta_key name 'Disease name' but also the meta_key name 'Interaction phenotype' since its corresponding description 'Interaction phenotype/disease outcome' matches the query")
@api_view(['GET'])
def interactions_by_meta_key_meta_value(request, meta_key,meta_value):
    keyval_query_set = DBtables.KeyValuePair.objects.select_related('interaction__interactor_1','interaction__interactor_2','interaction__source_db').select_related('meta_key').filter(Q(meta_key__name__icontains=meta_key)|Q(meta_key__description__icontains=meta_key)).filter(value__icontains=meta_value)
    interactions_dict = {};
    for kv in keyval_query_set:
        interactions_dict[kv.interaction.interaction_id] = {"interaction_id":kv.interaction.interaction_id,
                                                            "interactor_1":kv.interaction.interactor_1.curies,
                                                            "interactor_2":kv.interaction.interactor_2.curies,
                                                            "doi":kv.interaction.doi,
                                                            "source_db":kv.interaction.source_db.label,
                                                            "meta_key_name":kv.meta_key.name,
                                                            "meta_key_description":kv.meta_key.description,
                                                            "meta_value":kv.value,
                                                            }
    json_interactions = json.dumps(interactions_dict)
    return HttpResponse(json_interactions)

#USED BY ENSEMBL WEB!
@swagger_auto_schema(method='get',operation_description="Returns a list of all the interactions and metadata available (as displayed by the Ensembl browser) for a particular Ensembl gene (defined by its Ensembl stable identifier)")
@api_view(['GET'])
def display_by_gene(request,ens_stbl_id):
    
    interactions_by_queried_gene = DBtables.Interaction.objects.filter(Q(interactor_1__ensembl_gene_id__ensembl_stable_id=ens_stbl_id) | Q(interactor_2__ensembl_gene_id__ensembl_stable_id=ens_stbl_id))
    interactions_results_dict = {"interactor_1":{},"interactors_2":[]}
    interactor1_dict = {}
    interactor2_dict = {}

    interactors2_list = [] 
    
    for intrctn in interactions_by_queried_gene:
        
        source_db = get_displayable_source_db(intrctn.source_db.label)
        source_db_link = get_source_db_link(intrctn.interactor_1.curies, source_db)

        #First, sort the order of the two interactors to display always the queried gene as interactor_1
        if intrctn.interactor_1.ensembl_gene.ensembl_stable_id==ens_stbl_id:
            interactor1_type = intrctn.interactor_1.interactor_type
            species1_name = intrctn.interactor_1.ensembl_gene.species.scientific_name 
            identifier1 = intrctn.interactor_1.curies
            division1 = intrctn.interactor_1.ensembl_gene.species.ensembl_division
            ens_stbl_id_1 = intrctn.interactor_1.ensembl_gene.ensembl_stable_id
        
            interactor2_type = intrctn.interactor_2.interactor_type
            identifier2 = intrctn.interactor_2.curies
            interactor2_name = intrctn.interactor_2.name
            if interactor2_type != 'synthetic':
                species2_name = intrctn.interactor_2.ensembl_gene.species.scientific_name 
                division2 = intrctn.interactor_2.ensembl_gene.species.ensembl_division
                ens_stbl_id_2 = intrctn.interactor_2.ensembl_gene.ensembl_stable_id 
        elif intrctn.interactor_2.ensembl_gene.ensembl_stable_id==ens_stbl_id:
            interactor1_type = intrctn.interactor_2.interactor_type
            species1_name = intrctn.interactor_2.ensembl_gene.species.scientific_name 
            identifier1 = intrctn.interactor_2.curies
            division1 = intrctn.interactor_2.ensembl_gene.species.ensembl_division 
            ens_stbl_id_1 = intrctn.interactor_2.ensembl_gene.ensembl_stable_id
 
            interactor2_type = intrctn.interactor_1.interactor_type
            identifier2 = intrctn.interactor_1.curies
            interactor2_name = intrctn.interactor_1.name
            if interactor2_type != 'synthetic':
                species2_name = intrctn.interactor_1.ensembl_gene.species.scientific_name
                division2 = intrctn.interactor_1.ensembl_gene.species.ensembl_division
                ens_stbl_id_2 = intrctn.interactor_1.ensembl_gene.ensembl_stable_id 

        #build interactor_1 dictionary
        if not interactions_results_dict["interactor_1"]:
            InteractionsByGeneList = []
            ensembl_gene_link_1 = get_gene_link(ens_stbl_id_1,division1)
            identifier1_url = get_identifier_link(identifier1)

            interactor1_dict = {"type":"species","name": species1_name,"gene": {"name":ens_stbl_id_1,"url":ensembl_gene_link_1},"interactor":interactor1_type,"identifier": {"name":identifier1,"url":identifier1_url}}
            interactions_results_dict["interactor_1"] = interactor1_dict
      
        #build interactor_2 dictionary
        if 'UNDETERMINED' in identifier2:
            identifier2 = 'UNDETERMINED';
        identifier2_url = get_identifier_link(identifier2)
        #source_db = intrctn.source_db.label
        #source_db_link = get_source_db_link(identifier1, source_db)
        interactor2_dict = {}
        if interactor2_type == 'synthetic':
            interactor2_dict = {"type":"other", "name": interactor2_name,"interactor": interactor2_type,"identifier":{"name":identifier2,"url":identifier2_url},"source_DB": {"name":source_db,"url":source_db_link}}
        else:
            if 'UNDETERMINED' in ens_stbl_id_2:
                ens_stbl_id_2 = 'UNDETERMINED'
            ensembl_gene_link_2 = get_gene_link(ens_stbl_id_2,division2)
            interactor2_dict = {"type":"species", "name": species2_name,"gene": {"name":ens_stbl_id_2,"url":ensembl_gene_link_2},"interactor":interactor2_type,"identifier":{"name":identifier2,"url":identifier2_url},"source_DB":{"name":source_db,"url":source_db_link}}
        
        #build associated metadata
        metadata_list = get_metadata_list(intrctn.interaction_id,source_db_link)
        interactor2_dict["metadata"] = metadata_list
        interactors2_list.append(interactor2_dict)

    #wrap up
    if interactor1_dict != {}:
        interactions_results_dict = {"interactor_1":interactor1_dict, "interactor_2":interactors2_list}
    else:
        interactions_results_dict = {}

    json_response = json.dumps(interactions_results_dict)
    return HttpResponse(json_response)

#USED BY ENSEMBL-WEB!
#@swagger_auto_schema(method='get',operation_description="Returns all molecular interactors (listed by their Ensembl species name, also known as production name).\nThe 'Try it out' button might return an error if the response is too big but the endpoint will still work if tried on a browser.")
#@api_view(['GET'])
def interactors_by_prodname(request):
    
    species_genes_List = []
    ensembl_gene_query_set = DBtables.EnsemblGene.objects.select_related('species')

    species_gene_dict = {}
    for eg in ensembl_gene_query_set:
        if 'UNDETERMINED' not in eg.ensembl_stable_id:
            prod_name = eg.species.production_name
            if prod_name in species_gene_dict:
                genes_list = species_gene_dict[prod_name]
                genes_list.append(eg.ensembl_stable_id)
                species_gene_dict[prod_name] = genes_list
            else:
                species_gene_dict[prod_name] = [eg.ensembl_stable_id]
    json_species_genes = json.dumps(species_gene_dict)
    return HttpResponse(json_species_genes)

@swagger_auto_schema(method='get',operation_description="Returns all the ensembl_gene_identifiers from each molecular interactors for a specific Ensembl species name (also known as production name) passed as a parameter using the case non sensitive format: genus_species (ie.- 'homo_sapiens')")
@api_view(['GET'])
def ensembl_gene_by_specific_prodname(request, species_production_name):
    
    species_genes_List = []
    ensembl_gene_query_set = DBtables.EnsemblGene.objects.select_related('species').filter(species__production_name__icontains=species_production_name).exclude(ensembl_stable_id__icontains='UNDETERMINED')

    species_gene_dict = {}
    for eg in ensembl_gene_query_set:
        prod_name = eg.species.production_name
        if prod_name in species_gene_dict:
            genes_list = species_gene_dict[prod_name]
            genes_list.append(eg.ensembl_stable_id)
            species_gene_dict[prod_name] = genes_list
        else:
            species_gene_dict[prod_name] = [eg.ensembl_stable_id]
    json_species_genes = json.dumps(species_gene_dict)
    return HttpResponse(json_species_genes)

@swagger_auto_schema(method='get',operation_description="Returns all the ensembl_gene_identifiers from each molecular interactors for a specific species scientific name passed as a parameter using the case non sensitive format: genus species (ie.- 'homo sapiens')")
@api_view(['GET'])
def ensembl_gene_by_specific_scientific_name(request, species_scientific_name):
    
    species_genes_List = []
    ensembl_gene_query_set = DBtables.EnsemblGene.objects.select_related('species').filter(species__scientific_name__icontains=species_scientific_name).exclude(ensembl_stable_id__icontains='UNDETERMINED')
    
    species_gene_dict = {}
    for eg in ensembl_gene_query_set:
        science_name = eg.species.scientific_name
        if science_name in species_gene_dict:
            genes_list = species_gene_dict[science_name]
            genes_list.append(eg.ensembl_stable_id)
            species_gene_dict[science_name] = genes_list
        else:
            species_gene_dict[science_name] = [eg.ensembl_stable_id]
    json_species_genes = json.dumps(species_gene_dict)
    return HttpResponse(json_species_genes)

def get_metadata_list(interaction_id, source_db_link):
    MetadataByInteraction = DBtables.KeyValuePair.objects.filter(interaction_id=interaction_id)
    metadata_list = []
    
    for mo in MetadataByInteraction:
        metadata_dict = {}
        metadata_dict['label'] = mo.meta_key.name
        metadata_dict['value'] = mo.value
        if any(mo.meta_key.name in d.values() for d in metadata_list):
            metadata_list = [
                    {
                        'value':'Several experiments exist for this interaction. Please click  <a href=' + source_db_link + " target='_blank'>here</a>" + ' for more information'
                    }
                ]
            return metadata_list
        else:
            metadata_list.append(metadata_dict)
    return metadata_list

def get_displayable_source_db(source_db):
    if source_db == "PHI-baseAMR":
        return "PHI-base5.0"
    return source_db


def get_source_db_link(identifier, source_db):
    url = ''
    if source_db == "PHI-base":
        url = "http://www.phi-base.org/searchFacet.htm?queryTerm=" + clean_identifier(identifier)
    elif "HPIDB" in source_db:
        url = "https://hpidb.igbb.msstate.edu/keyword.html"
    elif (source_db == "PHI-base5.0") or (source_db == "PHI-baseAMR"):
        url = "https://phi5.phi-base.org/#/search-list-page?keyword=" + clean_identifier(identifier) + "&start=0"
    elif source_db == "PlasticDB":
        url = "https://plasticdb.org/proteins"
    return url

def clean_identifier(raw_id):
    if ":" in raw_id:
        clean_id = raw_id.partition (":") [2]
        return clean_id
    else:
        return raw_id

def get_identifier_link(identifier):
    url_link = None
    if "UNDETERMINED" not in identifier:
        url_link = "https://identifiers.org/" + identifier
    return url_link

def get_gene_link(ensembl_gene, division):
    url_link = None
    if 'UNDETERMINED' not in ensembl_gene:
        if division == 'vertebrates':
            url_link = "https://www.ensembl.org/id/" + ensembl_gene 
        else:
            url_link = "https://ensemblgenomes.org/id/" + ensembl_gene
    return url_link

@api_view(['GET'])
class EnsemblGeneViewSet(GenericViewSet,  # generic view functionality
                     CreateModelMixin,  # handles POSTs
                     RetrieveModelMixin,  # handles GETs for 1 EnsemblGene
                     UpdateModelMixin,  # handles PUTs and PATCHes
                     ListModelMixin):  # handles GETs for many EnsemblGene

      serializer_class = EnsemblGeneSerializer
      queryset = DBtables.EnsemblGene.objects.all()

