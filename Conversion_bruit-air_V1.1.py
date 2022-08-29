#-*- coding: utf-8 -*-#
#------------ Conversion ------------#
#--- Version : 0.1 ---#
#--- QGIS : 3.22.7 ---#

################################################################################################

#---------------DEBUT---------------#

#---------Import---------#

from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsProject, 
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterEnum 
                    )

from qgis import processing

################################################################################################

#---------Initialisation---------#

class conversion_bruit_air_v0_1(QgsProcessingAlgorithm):
    
    #------Définition des entrées, sorties et constantes------#

    INPUT_raster = 'INPUT_raster'
    choix = 'choix'
    
    #------Fonctions/Nomenclatures nécessaires au fonctionnement------#
    
    #---

    #def flags(self):
        #return super().flags() | QgsProcessingAlgorithm.FLagNoThreading

    #---Permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---Permet au script de se lancer dans QGIS---#

    def createInstance(self):
        return conversion_bruit_air_v0_1()

    #---Nom du script---# 

    def name(self):
        return 'conversion bruit-air v0.1'

    #---Nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('Conversion Bruit/Air V0.1')

    #---Nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---Description du script sur la droite de la fenetre initiale---#

    def shortHelpString(self):
        description='REF Documentation : Script 4 \n Ce script permet de passer de données raster représentant la nuisance sonore ou de la qualité de l’air pour en faire des données au format vecteur. \n Attention : Pas encore testé'
        return self.tr(description)

################################################################################################

    #------Création des éléments de la première fenêtre------#

    def initAlgorithm(self, config=None):

        #---Couche raster de la qualité de l'air ou du bruit---#

        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_raster,
            self.tr('Qualité de l\'air ou bruit')))

        #---Liste déroulante pour indiquer le type de la couche raster---#

        self.addParameter(QgsProcessingParameterEnum(
            self.choix,
            self.tr('Type du raster'),
            options=[
                self.tr('Bruit'),
                self.tr('Qualité de l\'air')
            ],
            allowMultiple = False,
            optional = False))

################################################################################################

    #------Actions du script------#

    def processAlgorithm(self, parameters, context, feedback):

        #------Fonctions------#

        #-Fonction pour gérer les annulations-#
        def annulation():
            feedback.pushInfo('Execution en cours ...')
            if feedback.isCanceled():
                return {}

################################################################################################

        #---Récupération des données en entrée---#

        raster = self.parameterAsRasterLayer(parameters,self.INPUT_raster,context)
        nom = raster.name()
        choix = self.parameterAsEnum(parameters, self.choix, context)

################################################################################################

        feedback.pushInfo('Execution en cours ...')

        #---Application de la formule au raster permettant de les classifier---#

        if choix == 0 :
            formule = '( "{0}@1" < 170 AND "{0}@1" >= 80  AND "{0}@2" < 90 AND "{0}@2" >= 0 AND "{0}@3" < 150 AND "{0}@3" >= 50 ) *1+ ( "{0}@1" < 254 AND "{0}@1" >= 170 AND "{0}@2" < 110 AND "{0}@2" >= 0 AND "{0}@3" < 215 AND "{0}@3" >= 100 ) *2+ ( "{0}@1" < 254 AND "{0}@1" >= 150 AND "{0}@2" < 100 AND "{0}@2" >= 0 AND "{0}@3" < 100 AND "{0}@3" >= 0 ) *3+ ( "{0}@1" < 254 AND "{0}@1" >= 155 AND "{0}@2" < 170 AND "{0}@2" >= 100 AND "{0}@3" < 100 AND "{0}@3" >= 0 ) *4+ ( "{0}@1" < 254 AND "{0}@1" >= 170 AND "{0}@2" < 254 AND "{0}@2" >= 170 AND "{0}@3" < 100 AND "{0}@3" >= 0 ) *5+ ( "{0}@1" < 170 AND "{0}@1" >= 100 AND "{0}@2" < 254 AND "{0}@2" >= 180 AND "{0}@3" < 160 AND "{0}@3" >= 70 ) *6+ ( "{0}@1" < 205 AND "{0}@1" >= 203 AND "{0}@2" < 256 AND "{0}@2" >= 254 AND "{0}@3" < 256 AND "{0}@3" >= 254 ) *7'.format(nom)

        else:
            formule='("{0}@1" > 0 AND "{0}@1" <= 8)*1+ ("{0}@1" > 8 AND "{0}@1" <= 10)*2+ ("{0}@1" > 10 AND "{0}@1" <= 12)*3+ ("{0}@1" > 12 AND "{0}@1" <= 14)*4+ ("{0}@1" > 14 AND "{0}@1" <= 16)*5+ ("{0}@1" > 16 AND "{0}@1" <= 18)*6+ ("{0}@1" > 18 AND "{0}@1" <= 20)*7+ ("{0}@1" > 20 AND "{0}@1" <= 22)*8+ ("{0}@1" > 22 AND "{0}@1" <= 24)*9+ ("{0}@1" > 24 AND "{0}@1" <= 26)*10+ ("{0}@1" > 26 AND "{0}@1" <= 28)*11+ ("{0}@1" > 28 AND "{0}@1" <= 30)*12+ ("{0}@1" > 30 AND "{0}@1" <= 32)*13+ ("{0}@1" > 32 AND "{0}@1" <= 34)*14+ ("{0}@1" > 34 AND "{0}@1" <= 36)*15+ ("{0}@1" > 36 AND "{0}@1" <= 38)*16+ ("{0}@1" > 38 AND "{0}@1" <= 40)*17+ ("{0}@1" > 40 AND "{0}@1" <= 80)*18 +("{0}@1" > 80) *19'.format(nom)
            
        calcul = processing.run("qgis:rastercalculator",{
                'EXPRESSION':formule,
                'LAYERS': raster,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Polygonisation de la classification---#

        poly = processing.run("gdal:polygonize",{
                'INPUT':calcul,
                'BAND':1,
                'FIELD':'Value',
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Réparation de la couche si nécessaire---#

        fix = processing.run("native:fixgeometries",{
            'INPUT':poly,
            'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']


        #-En cas d'annulation-#
        annulation()

        if (fix.crs().authid() != 'EPSG:2154'):
            reproj=processing.run("native:reprojectlayer",{
                'INPUT' : fix,
                'TARGET_CRS' : 'EPSG:2154',
                'OUTPUT'  :'TEMPORARY_OUTPUT'})['OUTPUT']
            fix=reproj

        #-En cas d'annulation-#
        annulation()

        #---On allège la couche en agrégeant les polygones d'une même classe---#
        
        agreg = processing.run("native:aggregate", {
                'INPUT':poly,
                'GROUP_BY':'"Value"',
                'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"Value"','length': 0,'name': 'Value','precision': 0,'type': 2}],
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---Affichage de la couche en sortie---#
            
        agreg.setName(nom+'_vec')   
        QgsProject.instance().addMapLayer(agreg)

        #-En cas d'annulation-#
        annulation()

        return{}

#---------------FIN---------------#