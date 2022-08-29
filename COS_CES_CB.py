#-*- coding: utf-8 -*-#
#------------ COS_CES_CB ------------#
#--- Version : 1.0 ---#
#--- QGIS : 3.22.7 ---#

################################################################################################

#---------------DEBUT---------------#

#---------Import---------#

from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsProject,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterExtent,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessing,
                       QgsProcessingParameterField,
                        )

from qgis import processing

################################################################################################

#---------Initialisation---------#

class COS_CES_CB(QgsProcessingAlgorithm):
    
    #------Définition des entrées, sorties et constantes------#

    INPUT_bati = 'INPUT_bati'
    INPUT_parcelle  = 'INPUT_parcelle'
    INPUT_extend = 'INPUT_extent'
    INPUT_id = 'INPUT_id'
    INPUT_etages = 'INPUT_etages'
    
    #------Fonctions/Nomenclatures nécessaires au fonctionnement------#
    
    #---

    #def flags(self):
        #return super().flags() | QgsProcessingAlgorithm.FLagNoThreading

    #---Permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---Permet au script de se lancer dans QGIS---#

    def createInstance(self):
        return COS_CES_CB()

    #---Nom du script---# 

    def name(self):
        return 'COS_CES_CB'

    #---Nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('COS_CES_CB')

    #---Nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---Description du script sur la droite de la fenetre initiale---#

    def shortHelpString(self):
        description='REF Documentation : Script 5 \n Ce script permet de calculer le COS (Coefficient d Occupation du Sol) et le CES (Coefficient d Occupation du Sol) a partir d une couche de batiment et d\'une couche de découpage'
        return self.tr(description)

################################################################################################

    #------Création des éléments de la première fenêtre------#

    def initAlgorithm(self, config=None):

        #---Couche vecteur des polygones où s'effectuent les calculs---#

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_parcelle,
            self.tr('Aires de calcul'),
            [QgsProcessing.TypeVectorPolygon],
            optional=False))

        #--

        self.addParameter(QgsProcessingParameterField(self.INPUT_id,
            self.tr('Champ ID'),
            allowMultiple= False,
            optional= True,
            parentLayerParameterName = self.INPUT_parcelle))

        #---Couche vecteur des polygones représentant les batiments---#

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_bati,
            self.tr('Bâtiments'),
            [QgsProcessing.TypeVectorPolygon],
            optional=False))

        #--

        self.addParameter(QgsProcessingParameterField(self.INPUT_etages,
            self.tr('Champ contenant les étages'),
            allowMultiple = False,
            optional = True,
            parentLayerParameterName = self.INPUT_bati))

        #---Etendue de travail---#

        self.addParameter(QgsProcessingParameterExtent(self.INPUT_extend,
            self.tr('Zone de travail'),
            defaultValue=None))

################################################################################################

    #------Actions du script------#

    def processAlgorithm(self, parameters, context, feedback):

        #------Fonctions------#

        #-Fonction pour gérer les annulations-#
        def annulation():
            feedback.pushInfo('Execution en cours ...')
            if feedback.isCanceled():
                return {}

        #---Fonction pour réparer les couches au besoin---#
        def verif(couche):
            couche = processing.run("native:fixgeometries",{
                'INPUT': couche,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

            couche = processing.run("native:reprojectlayer",{
                'INPUT':couche,
                'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2154'),
                'OUTPUT':'TEMPORARY_OUTPUT'})
            return(couche)

################################################################################################

        #---Récupération des données en entrée---#

        parcelle = self.parameterAsVectorLayer(parameters,self.INPUT_parcelle,context)
        batiment = self.parameterAsVectorLayer(parameters,self.INPUT_bati,context)
        extend = self.parameterAsExtent(parameters,self.INPUT_extend,context)
        id = self.parameterAsString(parameters,self.INPUT_id,context)
        etages = self.parameterAsString(parameters,self.INPUT_etages,context)

        #-En cas d'annulation-#
        annulation()

        feedback.pushInfo('réparation...')
        verif(parcelle)

################################################################################################

        #---Selection des parcelles dans la zone de travail---#

        parcelle.selectByRect(extend)

        parcelle= processing.run("native:saveselectedfeatures",{
            'INPUT':parcelle,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        self.parameterAsVectorLayer(parameters,self.INPUT_parcelle,context).removeSelection()

        #-En cas d'annulation-#
        annulation()

        #---Selection des batiments dans la zone de travail---#

        feedback.pushInfo('réparation...')
        verif(batiment)

        batiment.selectByRect(extend)

        batiment = processing.run("native:saveselectedfeatures",{
            'INPUT':batiment,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        self.parameterAsVectorLayer(parameters,self.INPUT_bati,context).removeSelection()

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Calcul de la surface des parcelles---#

        parcelle = processing.run("qgis:fieldcalculator",{
            'INPUT':parcelle,
            'FIELD_NAME':'surf_totale',
            'FIELD_TYPE':1,
            'FIELD_LENGHT':10,
            'FIELD_PRECISION':3,
            'FORMULA':'$area',
            'NEW_FIELD': True,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Isolement des batiment dans des parcelles---#

        intersect = processing.run("native:intersection",{
            'INPUT':parcelle,
            'OVERLAY':batiment,
            'INPUT_FIELDS':[id],
            'OVERLAY_FIELDS':[etages,id],
            'OVERLAY_FIELDS_PREFIX':'',
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Calcul de l'emprise au sol du bati---#

        intersect = processing.run("qgis:fieldcalculator",{
            'INPUT':intersect,
            'FIELD_NAME':'emprise_sol_bati',
            'FIELD_TYPE':1,
            'FIELDS_LENGHT':10,
            'FIELD_PRECISION':3,
            'FORMULA': '$area',
            'NEW_FIELD':True,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Calcul de la surface de plancher---#

        intersect = processing.run("qgis:fieldcalculator", {
            'INPUT': intersect,
            'FIELD_NAME':'surface_plancher',
            'FIELD_TYPE':1,
            'FIELD_LENGTH':10,
            'FIELD_PRECISION':3,
            'FORMULA': 'if('+ etages +' is null or '+ etages +'=0,$area,$area* '+ etages +')',
            'NEW_FIELD': True,
            'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Agregation des propriétés des batiments dans une même parcelle---#

        intersect = processing.run("native:aggregate", {
                'INPUT':intersect,
                'GROUP_BY':id,
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': id,'length': 10,'name': id,'precision': 0,'type': 4},
                            {'aggregate': 'sum','delimiter': ',','input': '"emprise_sol_bati"','length': 0,'name': 'emprise_sol_bati','precision': 3,'type': 2},
                            {'aggregate': 'sum','delimiter': ',','input': '"surface_plancher"','length': 10,'name': 'surface_plancher','precision': 3,'type': 2}],
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Jointure des couches parcelle et batiment---#

        jointure = processing.run("native:joinattributestable", {
                'INPUT':parcelle,
                'FIELD':id,
                'INPUT_2':intersect,
                'FIELD_2':id,
                'FIELDS_TO_COPY':['emprise_sol_bati','surface_plancher'],
                'METHOD':1,
                'DISCARD_NONMATCHING':False,
                'PREFIX':'',
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Calcul du CES---#

        CES = processing.run("qgis:fieldcalculator", {
            'INPUT':jointure,
            'FIELD_NAME':'_ces',
            'FIELD_TYPE':0,
            'FIELD_LENGTH':6,
            'FIELD_PRECISION':6,
            'FORMULA':'emprise_sol_bati/surf_totale',
            'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Calcul du COS---#

        COS = processing.run("qgis:fieldcalculator", {
            'INPUT':jointure,
            'FIELD_NAME':'_cos',
            'FIELD_TYPE':0,
            'FIELD_LENGTH':6,
            'FIELD_PRECISION':6,
            'FORMULA':'surface_plancher/surf_totale',
            'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Affichage de la couche du CES---#

        CES.setName('CES')
        QgsProject.instance().addMapLayer(CES)

        #-En cas d'annulation-#
        annulation()

        #---Affichage de la couche du COS---#

        COS.setName('COS')   
        QgsProject.instance().addMapLayer(COS)

        return{}

#---------------FIN---------------#