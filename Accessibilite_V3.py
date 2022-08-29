#-*- coding: utf-8 -*-#
#------------ Accessibilité ------------#
#--- Version : 3.0 ---#
#--- QGIS : 3.22.7 ---#

################################################################################################

#---------------DEBUT---------------#

#---------Import---------#

from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingAlgorithm, 
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterField
                        )

from qgis import processing

################################################################################################

#---------Initialisation---------#

class accessibilite_v3(QgsProcessingAlgorithm):

    #------Définition des entrées, sorties et constantes------#

    INPUT_point = 'INPUT_point'
    INPUT_reso = 'INPUT_reso'
    INPUT_dist = 'INPUT_dist'
    INPUT_caro = 'INPUT_caro'
    INPUT_pop = 'INPUT_pop'
    INPUT_surf = 'INPUT_surf'
    INPUT_id = 'INPUT_id'

    #------Fonctions/Nomenclatures nécessaires au fonctionnement------#

    #---

    #def flags(self):
        #return super().flags() | QgsProcessingAlgorithm.FLagNoThreading

    #---Permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---Permet au script de se lancer dans QGIS---# 

    def createInstance(self):
        return accessibilite_v3()

    #---Nom du script---#   

    def name(self):
        return 'accessibilité_v3'

    #---Nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('Accessibilité_V3')

    #---Nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---Description du script sur la droite de la fenetre initiale---#

    def shortHelpString(self):
        description = 'REF Documentation : Script 3 \n Ce script permet d’obtenir les isochrones autour de différents espaces. On obtient aussi la surface accessible / habitant. \n A l’origine ce script sert à obtenir les isochrones autour des espaces verts et connaitre le nombre de m² d’espaces verts accessible / habitant.'
        return self.tr(description)

################################################################################################

    #------Création des éléments de la première fenêtre------#

    def initAlgorithm(self, config=None):

        #---Couche de type point représentant les accès aux zones---#

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_point,
            self.tr('Points d\'accès'),
            [QgsProcessing.TypeVectorPoint]))

        #--

        self.addParameter(QgsProcessingParameterField(
            self.INPUT_id,
            self.tr('Champ ID'),
            allowMultiple = False,
            parentLayerParameterName = self.INPUT_point))

        #--

        self.addParameter(QgsProcessingParameterField(
            self.INPUT_surf,
            self.tr('Champ contenant la surface'),
            allowMultiple = False,
            parentLayerParameterName = self.INPUT_point))

        #---Couche du réseau de voirie---#
    
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_reso,
            self.tr('Réseau de voirie'),
            [QgsProcessing.TypeVectorLine]))

        #---Couche de carreaux INSEE---#

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_caro,
            self.tr('Aires de calcul'),
            [QgsProcessing.TypeVectorPolygon]))

        #--

        self.addParameter(QgsProcessingParameterField(
            self.INPUT_pop,
            self.tr('Champ de population'),
            allowMultiple = False,
            parentLayerParameterName = self.INPUT_caro))

        #---Distance souhaitée pour l'isochrone---#
    
        self.addParameter(QgsProcessingParameterNumber(
            self.INPUT_dist,
            self.tr('Distance d\'isochrones souhaitée'),
            type=QgsProcessingParameterNumber.Double))

################################################################################################

    #------Actions du script------#
    
    def processAlgorithm(self, parameters, context, feedback):

        #------Fonctions------#

        #-Fonction pour gérer les annulations-#
        def annulation():
            feedback.pushInfo('Execution en cours ...')
            if feedback.isCanceled():
                return {}

        #---Fonction pour les vecteurs corrigeant si besoin les géometries et la projection---#

        def verif(vecteur):

            vec=parameters[vecteur]
            crs = self.parameterAsCrs(parameters,vecteur,context)

            #-Si le système de coordonnées n'est pas en 2154-#

            if (crs.authid != 'EPSG:2154'):
                
                feedback.pushInfo('\n Reprojection en cours...')

                trans=processing.run("native:reprojectlayer", {
                    'INPUT' : vec,
                    'TARGET_CRS' : 'EPSG:2154',
                    'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
                vec = trans
            
            #-Réparations des géométries-#

            feedback.pushInfo('\n Vérification des géométries...')

            fix = processing.run("native:fixgeometries",{
                'INPUT':vec,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

            return fix

################################################################################################

        #---Récupération des données en entrée---#

        population = self.parameterAsString(parameters,self.INPUT_pop,context)

        surf_veg = self.parameterAsString(parameters,self.INPUT_surf,context)

        id = self.parameterAsString(parameters,self.INPUT_id,context)

        distance = self.parameterAsDouble(parameters,self.INPUT_dist,context)

        #---Réparation au besoin des couches---#

        reso = verif('INPUT_reso')
        caro = verif('INPUT_caro')
        point = verif('INPUT_point')

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Création d'un réseau associé à chaque point d'accès---#

        iso = processing.run("native:serviceareafromlayer", {
            'INPUT':reso,
            'STRATEGY':0,
            'DIRECTION_FIELD':'',
            'VALUE_FORWARD':'',
            'VALUE_BACKWARD':'',
            'VALUE_BOTH':'',
            'DEFAULT_DIRECTION':2,
            'SPEED_FIELD':'',
            'DEFAULT_SPEED':50,
            'TOLERANCE':0,
            'START_POINTS':point,
            'TRAVEL_COST2':distance,
            'INCLUDE_BOUNDS':False,
            'OUTPUT_LINES':'TEMPORARY_OUTPUT'})['OUTPUT_LINES']

        #-En cas d'annulation-#
        annulation()

        #---Agrégation des réseaux appartenant à une même zone de départ---#

        agreg = processing.run("native:aggregate",{
            'INPUT':iso,
            'GROUP_BY':id,
            'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': surf_veg,'length': 10,'name': surf_veg,'precision': 0,'type': 4},{'aggregate': 'first_value','delimiter': ',','input': id,'length': 10,'name': id,'precision': 0,'type': 4}],
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Création des isochrones sous forme de polygone---#

        zone = processing.run("native:convexhull", {
            'INPUT':iso,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#

        annulation()

        #---Affichage de la couche des isochrones---#

        zone.setName('Isochrones')
        QgsProject.instance().addMapLayer(zone)

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Association de la surface des zones atteignables par chaque carreau---#

        joint = processing.run("qgis:joinbylocationsummary", {
            'INPUT':caro,
            'JOIN':agreg,
            'PREDICATE':[0],
            'JOIN_FIELDS':[surf_veg],
            'SUMMARIES':[5],
            'DISCARD_NONMATCHING':False,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()  

        #---Calcul du ratio : (m²) / (habitant)---#

        final = processing.run("qgis:fieldcalculator",{
            'INPUT':joint,
            'FIELD_NAME':'ratio',
            'FIELD_TYPE':1,
            'FIELD_LENGTH':10,
            'FIELD_PRECISION':2,
            'FORMULA': surf_veg + '_sum / ' + population,
            'NEW_FIELD': True,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Remplacement des valeurs NULL par 0---#

        final = processing.run("qgis:fieldcalculator",{
            'INPUT':final,
            'FIELD_NAME':'ratio',
            'FIELD_TYPE':0,
            'FIELD_LENGTH':10,
            'FIELD_PRECISION':2,
            'FORMULA':'CASE WHEN ratio IS NULL THEN 0 WHEN ratio IS NOT NULL THEN ratio END',
            'NEW_FIELD':False,
            'OUTPUT':'TEMPORARY_OUTPUT' })['OUTPUT']

        #-En cas d'annulation-#
        annulation() 

        #---nommage et affichage de la couche en sortie---#

        final.setName('Accessibilité')   
        QgsProject.instance().addMapLayer(final)

        return{}

#---------------FIN---------------#