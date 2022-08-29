# -*- coding: utf-8 -*-#
#------------ Ilots_CB ------------#
#--- Version : 1 ---#
#--- QGIS : 3.22.7 ---#

#------------DEBUT------------#

#---------Import---------#

import time
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject, 
                       QgsVectorLayer,
                       QgsRasterLayer,
                       QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsFeatureRequest,
                       QgsFeature,
                       QgsMapLayerStyle,
                       QgsProcessingParameterNumber,
                       QgsDataSourceUri,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransformContext,
                       QgsProcessingParameterBoolean,
                       QgsPoint,
                       QgsGeometry,
                       QgsProcessingParameterExtent,
                       QgsProviderRegistry,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField)
from qgis import processing
from qgis.utils import iface

##########################################################################################################
#---------Initialisation------#

class ilots_CB(QgsProcessingAlgorithm):
    
    #------Définition des entrées, sorties et constantes---#

    INPUT_extent = 'INPUT_extent'
    INPUT_fer = 'INPUT_fer'
    INPUT_route = 'INPUT_route'
    INPUT_parcelles = 'INPUT_parcelles'
    INPUT_eau = 'INPUT_eau'
    INPUT_choix = 'INPUT_choix'
    
    #------Fonction/Nomenclature nécessaire au fonctionnement---#
    
    #---permet l'affichage des couches en sortie---#

    def flags(self):
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    #---permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---permet au script de se lancer dans QGIS---#

    def createInstance(self):
        return ilots_CB()

    #---nom du script---#

    def name(self):
        return 'ilots_CB'

    #---nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('Ilots_CB')

    #---nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---description du script présente dans la fenetre initiale---#

    def shortHelpString(self):
        description='REF Documentation : Script 7 \n Ce script permet de générer les ilots urbains. Il est possible de choisir entre intégrer les espaces publics dans les ilots ou non. Ne pas les intégrer peut permettre de les générer et de les ajouter ultérieurement. \n Attention : Ce script fonctionne uniquement avec les couches IGN.'
        return self.tr(description)

    #------Création des éléments de la première fenêtre---#

    def initAlgorithm(self, config=None):

        self.addParameter(QgsProcessingParameterExtent(self.INPUT_extent,
            self.tr('Zone de travail'),
            defaultValue=None))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_fer,
            self.tr('Tronçon de voie ferrée'),
            [QgsProcessing.TypeVectorLine],
            optional=False))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_route,
            self.tr('Tronçon de route'),
            [QgsProcessing.TypeVectorLine],
            optional=False))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_eau,
            self.tr('Cours d\'eau'),
            [QgsProcessing.TypeVectorLine],
            optional = True))

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_parcelles,
            self.tr('Parcelles'),
            [QgsProcessing.TypeVectorPolygon],
            optional=True))

        self.addParameter(QgsProcessingParameterBoolean(self.INPUT_choix,
            self.tr('Ilots avec espaces publics'),
            defaultValue=False))

    #---------Actions du script---------#

    def processAlgorithm(self, parameters, context, feedback):

        #-fonction pour gérer les annulations-#
        def annulation():
            feedback.pushInfo('Execution en cours ...')
            if feedback.isCanceled():
                return {}

        #-fonction pour ne pas avoir à réutiliser l'outil save selected features-#

        def selection(vecteur):

            feedback.pushInfo('selection...')
            select = processing.run("native:saveselectedfeatures",{
                'INPUT':vecteur,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            vecteur.removeSelection()
            return(select)

        #---Récupérations des données en entrée---#

        fer = self.parameterAsVectorLayer(parameters,self.INPUT_fer,context)
        route = self.parameterAsVectorLayer(parameters,self.INPUT_route,context)
        parcelles = self.parameterAsVectorLayer(parameters,self.INPUT_parcelles,context)
        eau = self.parameterAsVectorLayer(parameters,self.INPUT_eau,context)
        choix = self.parameterAsBool(parameters,self.INPUT_choix,context)
        extent = self.parameterAsExtent(parameters,self.INPUT_extent,context)
        liste = []

        #---Selection des données selon l'emprise et des formules---#

        #-Voie ferree-#

        fer.selectByRect(extent)

        fer_r = selection(fer)

        annulation()

        fer_r.selectByExpression("\"nature\" = \'Voie ferrée principale\'")

        fer_e = selection(fer_r)

        liste.append(fer_e)

        annulation()

        #-Route-#

        route.selectByRect(extent)

        route_r = selection(route)

        annulation()

        if choix == True : #-Si l'on souhaite les ilots avec ou sans espaces publics-#

            route_r.selectByExpression(" \"nature\" in ( \'Type autoroutier\' , \'Route à 1 chaussée\' , \'Route à 2 chaussées\' , \'Rond-point\' ) AND  \"nom_1_gauche\" NOT LIKE \'TUNNEL%\' OR  \"nom_1_gauche\" IS NULL")

        else :

            route_r.selectByExpression("\"nature\" = \'Route à 2 chaussées\' or \"nature\" = \'Type autoroutier\'")

        route_e = selection(route_r)

        liste.append(route_e)

        annulation()

        #-Parcelles-#

        parcelles.selectByRect(extent)

        parcelles_r = selection(parcelles)

        annulation()

        if choix == True: #-Si l'utilisateur souhaite les ilots sans espaces publics on ajoute les cours d'eau

            #-Eau-#

            eau.selectByRect(extent)

            eau_r = selection(eau)

            liste.append(eau_r)

            #-On ajoute aussi un cadre-#

            cadre = processing.run("native:extenttolayer",{
                'INPUT':extent,
                'OUTPUT':'TEMPORARY_OUTPUT'    
            })['OUTPUT']

            cadre_l = processing.run("native:polygonstolines",{
                'INPUT':cadre,
                'OUTPUT':'TEMPORARY_OUTPUT'
            })['OUTPUT']

            liste.append(cadre_l)

        #---On fusionne les différents réseaux pour obtenir nos limites de polygones---#

        fusion = processing.run("native:mergevectorlayers",{
            'LAYERS':liste,
            'CRS':QgsCoordinateReferenceSystem('EPSG:2154'),
            'OUTPUT':'TEMPORARY_OUTPUT'
        })['OUTPUT']

        annulation()

        #---La méthode pour obtenir la couche finale change drastiquement selon le choix de l'utilisateur---#

        if choix == True:

            #-On utilise le réseau précédemment créer comme limite de polygones qui seront nos ilots-#

            ilot = processing.run("native:polygonize",{ #-Outil mise en polygone-#
                'INPUT':fusion,
                'KEEP_FIELDS':False,
                'OUTPUT':'TEMPORARY_OUTPUT'
            })['OUTPUT']

        else:

            #-On selectionne et supprime les parcelles faisant un effet de "pont" entre les ilots-#

            new_parcelles = processing.run("native:selectbylocation",{
                'INPUT':parcelles_r,
                'PREDICATE':[0],
                'INTERSECT':fusion,
                'METHOD':0
            })['OUTPUT']

            new_parcelles.invertSelection()

            annulation()

            new_parcelles = processing.run("native:saveselectedfeatures",{
                'INPUT':new_parcelles,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            annulation()

            #-On regroupe la couche de parcelle nouvellement crée pour donner les ilots-#

            ilot = processing.run("native:dissolve",{
                'INPUT':new_parcelles,
                'FIELD':[],
                'OUTPUT':'TEMPORARY_OUTPUT'
            })['OUTPUT']

            annulation()

            ilot = processing.run("native:multiparttosingleparts",{
                'INPUT':ilot,
                'OUTPUT':'TEMPORARY_OUTPUT'
            })['OUTPUT']

            annulation()

        #-On affiche la couche en sortie-#

        if choix == True :

            nom = "Ilots_espaces_publics"

        else:

            nom = "Ilots"

        ilot.setName(nom)
        QgsProject.instance().addMapLayer(ilot)

        return{}