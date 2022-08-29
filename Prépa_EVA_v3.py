#-*- coding: utf-8 -*-#
#------------ Prepa_EVA ------------#
#--- Version : 3.0 ---#
#--- QGIS : 3.22.7 ---#

################################################################################################

#---------------DEBUT---------------#

#---------Import---------#

from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterMultipleLayers,
                       QgsProject)

from qgis import processing

################################################################################################

#---------Initialisation---------#

class prepa_eva_v3(QgsProcessingAlgorithm):

    #------Définition des entrées, sorties et constantes------#

    INPUT = 'INPUT'
    INPUT_choix = 'INPUT_choix'

    #------Fonctions/Nomenclatures nécessaires au fonctionnement------#
    
    #---

    #def flags(self):
        #return super().flags() | QgsProcessingAlgorithm.FLagNoThreading

    #---Permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---Permet au script de se lancer dans QGIS---#

    def createInstance(self):

        return prepa_eva_v3()

    #---Nom du script---# 

    def name(self):
 
        return 'prepa_eva_v3'

    #---Nom du script avec caractères spéciaux---#

    def displayName(self):
 
        return self.tr('Prépa EVA V3')

    #---Nom du groupe auquel appartient le script---#

    def group(self):

        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):

        return 'INDIGEN_CB'

    #---Description du script sur la droite de la fenetre initiale---#

    def shortHelpString(self):

        return self.tr("REF Documentation : Script 2 \n Ce script permet de prendre une ou plusieurs couches EVA 2015 (Espaces Végétalisés et Artificialisés) provenant de data GrandLyon et de la/les rendre exploitable par Indi_En (Script 1). Il est possible de choisir parmi 2 configurations.\n Attention : il est nécessaire que ce soit une couche EVA 2015")

################################################################################################

    #------Création des éléments de la première fenêtre------#

    def initAlgorithm(self, config=None):

        #---Liste des couches EVA---#

        self.addParameter(
            QgsProcessingParameterMultipleLayers(self.INPUT,
            self.tr('Couche(s) EVA')
            ))

        #---Choix par l'utilisateur du type de classification---#

        self.addParameter(
            QgsProcessingParameterEnum(self.INPUT_choix,
            self.tr('Choix de la configuration'),
            options=[
                self.tr('Classes entre 1 et 8'),
                self.tr('Classes entre 1 et 10')
            ],
            allowMultiple = False,
            optional = False
            )
        )

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

        feedback.pushInfo('Récupération de la liste de vecteurs')
        
        EVA = self.parameterAsLayerList(parameters,'INPUT',context)

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Fusion des couches---#

        feedback.pushInfo('Fusion des couches')

        if len(EVA) > 1 :
            
            total = processing.run('native:mergevectorlayers',{
                'LAYERS' : EVA,
                'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
            EVA = total
        
        else: 
            EVA = parameters['INPUT']
            EVA = EVA[0]

        #-En cas d'annulation-#
        annulation()

        #---Agrégation des polygones d'une même classe---#

        feedback.pushInfo('Agrégation des polygones d\'une même classe')

        agreg = processing.run("native:aggregate", {
            'INPUT':EVA,
            'GROUP_BY':'"libelles"',
            'AGGREGATES':[{'aggregate': 'first_value','delimiter': ',','input': '"libelles"','length': 254,'name': 'libelles','precision': 0,'type': 10}],
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        
        EVA = agreg

        #-En cas d'annulation-#
        annulation()

        #---Attribution des valeurs Indi_En à chaque classe---#

        feedback.pushInfo('Attribution d\'une Value à chaque classes')

        choix = self.parameterAsEnum(parameters,'INPUT_choix',context)

        if choix==0:

            calcul = processing.run("native:fieldcalculator",{
            'INPUT':EVA,
            'FIELD_NAME': 'Classification',
            'FIELD_TYPE':1,
            'FIELD_LENGHT':1,
            'FIELD_PRECISION':2,
            'NEW_FIELD':True,
            'FORMULA' : 'CASE WHEN libelles = \'Autres milieux herbeux à usage non agricole\' THEN 2 WHEN libelles = \'Autres plantations\' THEN 2 WHEN libelles = \'Bassins portuaires\' THEN 8 WHEN libelles = \'Bassins techniques\' THEN 8 WHEN libelles = \'Bâtis routes et surfaces impermeabilisee\' THEN 3 WHEN libelles = \'Bois et Forêts de coniferes fermees\' THEN 1 WHEN libelles = \'Bosquets  Bois et Forêts de feuillus seches fermees\' THEN 1 WHEN libelles = \'Cours d eau\' THEN 8 WHEN libelles = \'Cultures cerealieres et de proteagineux\' THEN 2 WHEN libelles = \'Cultures permanentes  legumieres ou horticoles de plein champs\' THEN 2 WHEN libelles = \'Cultures sous serres tunnels et hors sol\' THEN 2 WHEN libelles = \'Espaces en mutation et fourres en cours de fermeture\' THEN 2 WHEN libelles = \'Forêts melangees\' THEN 1 WHEN libelles = \'Fourrees humides \' THEN 2 WHEN libelles = \'Fourres  fruticees ou landes\' THEN 2 WHEN libelles = \'Friches agricoles\' THEN 2 WHEN libelles = \'Friches en zone urbaine\' THEN 2 WHEN libelles = \'Haies arbustives et arborees en contexte agricole\' THEN 1 WHEN libelles = \'Jardins collectifs\' THEN 2 WHEN libelles = \'Mares  etangs  plans d eau\' THEN 8 WHEN libelles = \'Milieux aquatiques des espaces verts et de loisirs\' THEN 8 WHEN libelles = \'Plages  Dunes et sables\' THEN 6 WHEN libelles = \'Prairies permanentes humides fauchees\' THEN 2 WHEN libelles = \'Prairies permanentes humides pâturees\' THEN 2 WHEN libelles = \'Prairies permanentes mesophiles fauchees\' THEN 2 WHEN libelles = \'Prairies permanentes mesophiles pâturees \' THEN 2 WHEN libelles = \'Prairies temporaires\' THEN 2 WHEN libelles = \'Ripisylves et forêts humides\' THEN 1 WHEN libelles = \'Roches nues  falaises\' THEN 3 WHEN libelles = \'Sols nus\' THEN 6 WHEN libelles = \'Strate arboree\' THEN 1 WHEN libelles = \'Strate arbustive\' THEN 2 WHEN libelles = \'Strate herbacee \' THEN 2 WHEN libelles = \'Vegetations herbacees hautes des ceintures des plans d eau et des cours d eau \' THEN 2 WHEN libelles = \'Vergers et petits fruits\' THEN 1 WHEN libelles = \'Vignobles\' THEN 6 WHEN libelles = \'Plantations de peupliers\' THEN 1 WHEN libelles = \'Bosquets  Bois et Forêts de feuillus seches ouvertes\' THEN 1 WHEN libelles = \'Pelouses naturelles\' THEN 2 WHEN libelles = \'Plans d’eau de gravieres en activite\' THEN 8 WHEN libelles = \'Autres plans d’eau\' THEN 8 WHEN libelles = \'Grands herbiers aquatiques \' THEN 2 WHEN libelles = \'Bassins de lagunage\' THEN 8 WHEN libelles = \'Retenues collinaires\' THEN 8 ELSE 0 END',
            'OUTPUT' : 'TEMPORARY_OUTPUT'}) ['OUTPUT']

            EVA=calcul

            #-En cas d'annulation-#
            annulation()

            #---Affichage de la couche en sortie---#

            feedback.pushInfo('Affichage de la couche en sortie')

            EVA.setName('EVA_Indi_En_8')

        else:

            calcul = processing.run("native:fieldcalculator",{
            'INPUT':EVA,
            'FIELD_NAME': 'Value',
            'FIELD_TYPE':1,
            'FIELD_LENGHT':1,
            'FIELD_PRECISION':2,
            'NEW_FIELD':True,
            'FORMULA' : 'CASE WHEN libelles = \'Autres milieux herbeux à usage non agricole\' THEN 2 WHEN libelles = \'Autres plantations\' THEN 2 WHEN libelles = \'Bassins portuaires\' THEN 8 WHEN libelles = \'Bassins techniques\' THEN 8 WHEN libelles = \'Bâtis routes et surfaces impermeabilisee\' THEN 3 WHEN libelles = \'Bois et Forêts de coniferes fermees\' THEN 1 WHEN libelles = \'Bosquets  Bois et Forêts de feuillus seches fermees\' THEN 1 WHEN libelles = \'Cours d eau\' THEN 8 WHEN libelles = \'Cultures cerealieres et de proteagineux\' THEN 2 WHEN libelles = \'Cultures permanentes  legumieres ou horticoles de plein champs\' THEN 9 WHEN libelles = \'Cultures sous serres tunnels et hors sol\' THEN 2 WHEN libelles = \'Espaces en mutation et fourres en cours de fermeture\' THEN 9 WHEN libelles = \'Forêts melangees\' THEN 1 WHEN libelles = \'Fourrees humides \' THEN 10 WHEN libelles = \'Fourres  fruticees ou landes\' THEN 9 WHEN libelles = \'Friches agricoles\' THEN 2 WHEN libelles = \'Friches en zone urbaine\' THEN 2 WHEN libelles = \'Haies arbustives et arborees en contexte agricole\' THEN 9 WHEN libelles = \'Jardins collectifs\' THEN 9 WHEN libelles = \'Mares  etangs  plans d eau\' THEN 8 WHEN libelles = \'Milieux aquatiques des espaces verts et de loisirs\' THEN 8 WHEN libelles = \'Plages  Dunes et sables\' THEN 6 WHEN libelles = \'Prairies permanentes humides fauchees\' THEN 10 WHEN libelles = \'Prairies permanentes humides pâturees\' THEN 10 WHEN libelles = \'Prairies permanentes mesophiles fauchees\' THEN 2 WHEN libelles = \'Prairies permanentes mesophiles pâturees \' THEN 2 WHEN libelles = \'Prairies temporaires\' THEN 2 WHEN libelles = \'Ripisylves et forêts humides\' THEN 1 WHEN libelles = \'Roches nues  falaises\' THEN 3 WHEN libelles = \'Sols nus\' THEN 6 WHEN libelles = \'Strate arboree\' THEN 1 WHEN libelles = \'Strate arbustive\' THEN 9 WHEN libelles = \'Strate herbacee \' THEN 2 WHEN libelles = \'Vegetations herbacees hautes des ceintures des plans d eau et des cours d eau \' THEN 10 WHEN libelles = \'Vergers et petits fruits\' THEN 1 WHEN libelles = \'Vignobles\' THEN 6 WHEN libelles = \'Plantations de peupliers\' THEN 1 WHEN libelles = \'Bosquets  Bois et Forêts de feuillus seches ouvertes\' THEN 1 WHEN libelles = \'Pelouses naturelles\' THEN 2 WHEN libelles = \'Plans d’eau de gravieres en activite\' THEN 8 WHEN libelles = \'Autres plans d’eau\' THEN 8 WHEN libelles = \'Grands herbiers aquatiques \' THEN 10 WHEN libelles = \'Bassins de lagunage\' THEN 10 WHEN libelles = \'Retenues collinaires\' THEN 8 ELSE 0 END',
            'OUTPUT' : 'TEMPORARY_OUTPUT'}) ['OUTPUT']

            EVA=calcul

            #-En cas d'annulation-#
            annulation()

            #---Affichage de la couche en sortie---#

            feedback.pushInfo('Affichage de la couche en sortie')

            EVA.setName('EVA_Indi_En_10')

        QgsProject.instance().addMapLayer(EVA)
        return{}

#---------------FIN---------------#