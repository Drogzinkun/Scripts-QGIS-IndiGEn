# -*- coding: utf-8 -*-#
#------------ TeleDispersion ------------#
#--- Version : 1 ---#
#--- QGIS : 3.22.7 ---#

##########################################################################################################

#------------DEBUT------------#

#---------Import---------#

import time
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject, 
                       QgsRasterLayer,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterMultipleLayers,
                       QgsProperty,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterNumber
                    )
from qgis import processing
from qgis.utils import iface

##########################################################################################################

#---------Initialisation------#

class Dispersion_Teledec(QgsProcessingAlgorithm):
    
    #------Définition des entrées, sorties et constantes---#

    #- Couches en entrée -#
    INPUT_teledec = 'INPUT_teledec'
    INPUT_reservoir = 'INPUT_reservoir'

    #- Coefficients de friction -#

    INPUT_1 = 'INPUT_1'
    INPUT_2 = 'INPUT_2'
    INPUT_3 = 'INPUT_3'
    INPUT_4 = 'INPUT_4'
    INPUT_5 = 'INPUT_5'
    INPUT_6 = 'INPUT_6'
    INPUT_7 = 'INPUT_7'
    INPUT_8 = 'INPUT_8'

    #- cout maximale-#

    INPUT_cout = 'INPUT_cout'
    
    #------Fonction/Nomenclature nécessaire au fonctionnement---#
    
    #---permet l'affichage des couches en sortie---#

    #def flags(self):
        #return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    #---permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---permet au script de se lancer dans QGIS---#

    def createInstance(self):
        return Dispersion_Teledec()

    #---nom du script---#

    def name(self):
        return 'TeleDispersion'

    #---nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('TeleDispersion')

    #---nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---description du script présente dans la fenetre initiale---#

    def shortHelpString(self):
        description='REF Documentation : Script 7 \n Ce script permet de modéliser la dispersion de différentes espèces en fonction d\'une télédetection en 8 classes et d\'une couche représentant les réservoirs de biodiversité'
        return self.tr(description)

    #------Création des éléments de la première fenêtre---#

    def initAlgorithm(self, config=None):

        #- Couches en entrée -#
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_reservoir,
            self.tr('Reservoir(s)'),
            [QgsProcessing.TypeVectorPolygon],
            optional=False))

        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_teledec,
            self.tr('Classification'),
            defaultValue=None,
            optional=False))

        #- Coefficients de friction -#

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_1,
            self.tr('Friction pour strate haute'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_2,
            self.tr('Friction pour strate basse'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_3,
            self.tr('Friction pour minéral foncé'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_4,
            self.tr('Friction pour tuiles rouges'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_5,
            self.tr('Friction pour surface forte réflectance'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_6,
            self.tr('Friction pour terre nue'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_7,
            self.tr('Friction pour ombres'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_8,
            self.tr('Friction pour eau'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional = False))

        #- cout maximale -#

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_cout,
            self.tr('Cout Maximal'),
            type = QgsProcessingParameterNumber.Double,
            defaultValue=1000,
            optional = False))

    #---------Actions du script---------#

    def processAlgorithm(self, parameters, context, feedback):

        #fonction pour gérer les annulations#
        def annulation():

            feedback.pushInfo('Execution en cours ...')
            if feedback.isCanceled():
                return {}

        #--- Récupération des variables en entrées ---#

        reservoir = self.parameterAsVectorLayer(parameters,self.INPUT_reservoir,context)
        teledec = self.parameterAsRasterLayer(parameters,self.INPUT_teledec,context)
        cout = self.parameterAsDouble(parameters,self.INPUT_cout,context)
        I1 = self.parameterAsDouble(parameters,self.INPUT_1,context)
        I2 = self.parameterAsDouble(parameters,self.INPUT_2,context)
        I3 = self.parameterAsDouble(parameters,self.INPUT_3,context)
        I4 = self.parameterAsDouble(parameters,self.INPUT_4,context)
        I5 = self.parameterAsDouble(parameters,self.INPUT_5,context)
        I6 = self.parameterAsDouble(parameters,self.INPUT_6,context)
        I7 = self.parameterAsDouble(parameters,self.INPUT_7,context)
        I8 = self.parameterAsDouble(parameters,self.INPUT_8,context)

        #--- Création d'une liste des coefficents ---#
        list = []
        list.append(I1)
        list.append(I2)
        list.append(I3)
        list.append(I4)
        list.append(I5)
        list.append(I6)
        list.append(I7)
        list.append(I8)
        annulation()

        #--- Génération de la Formule qui sera appliquée à la télédetection ---#

        nom = teledec.name()
        nom = '+("' + nom + '@1"'
        formule= ""

        for i in range(8):
            formule = formule + nom + " = " + str(i+1) + " )*" + str(list[i])
        
        formule  = "("+formule[1:]+")"

        #--- Application de la formule ---#

        calcul = processing.run("qgis:rastercalculator",{
            'EXPRESSION':formule,
            'LAYERS':teledec,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        annulation()

        #--- Impression des réservoirs sur le raster nouvellement créé ---#

        teledec = processing.run("gdal:rasterize_over_fixed_value",{
            'INPUT': reservoir,
            'INPUT_RASTER':calcul,
            'Burn':0,
            'ADD':False,
            'EXTRA':''})
        
        teledec = QgsRasterLayer(teledec['OUTPUT'])

        annulation()

        #--- Affichage de la couche de friction ---#

        teledec.setName('Friction')  
        QgsProject.instance().addMapLayer(teledec)

        annulation()

        #--- Génération des points de départs ---#

        depart = processing.run("native:centroids",{
            'INPUT':reservoir,
            'ALL_PARTS':False,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        annulation()

        #--- Lancement du calcul de la dispersion ---#

        final = processing.run("grass7:r.cost",{
            'input':teledec,
            'start_coordinates':None,
            'stop_coordinates':None,
            '-k':False,
            '-n':True,
            'start_points':depart,
            'stop_points':None,
            'start_raster':None,
            'max_cost':cout,
            'null_cost':None,
            'memory':1500,
            'output':'TEMPORARY_OUTPUT',
            'nearest':'TEMPORARY_OUTPUT',
            'outdir':'TEMPORARY_OUTPUT',
            'GRASS_REGION_PARAMETER':None,
            'GRASS_REGION_CELLSIZE_PARAMETER':0,
            'GRASS_RASTER_FORMAT_OPT':'',
            'GRASS_RASTER_FORMAT_META':'',
            'GRASS_SNAP_TOLERANCE_PARAMETER':-1,
            'GRASS_MIN_AREA_PARAMETER':0.0001})

        final = QgsRasterLayer(final['output'])

        annulation()

        #--- Affichage de la couche finale ---#

        final.setName('Dispersion')
        QgsProject.instance().addMapLayer(final)

        annulation()

        return{}