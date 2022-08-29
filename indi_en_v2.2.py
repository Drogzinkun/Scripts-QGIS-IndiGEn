#-*- coding: utf-8 -*-#
#------------ Indi_En_V2.2 ------------#
#--- Version : 2.2 ---#
#--- QGIS : 3.22.7 ---#

################################################################################################

#---------------DEBUT---------------#

#---------Import---------#

import psycopg2
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
                       QgsProcessingParameterField
                        )
from qgis import processing
from qgis.utils import iface

################################################################################################

#---------Initialisation---------#

class indi_en_v2_2(QgsProcessingAlgorithm):
    
    #------Définition des entrées, sorties et constantes------#

    INPUT_extend = 'INPUT_extend'
    INPUT_parcelle = 'INPUT_parcelle'
    INPUT_classif_ras = 'INPUT_classif_ras'
    INPUT_classif_vec = 'INPUT_classif_vec'
    INPUT_ilot = 'INPUT_ilot'
    INPUT_resolution = 'INPUT_resolution'
    INPUT_classes = 'INPUT_classes'
    INPUT_champ = 'INPUT_champ'
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
        return indi_en_v2_2()

    #---Nom du script---# 

    def name(self):
        return 'indi_en_v2.2'

    #---Nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('Indi_En_V2.2')

    #---Nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---Description du script sur la droite de la fenetre initiale---#

    def shortHelpString(self):
        description='REF Documentation : Script 1 \n Ce script permet de calculer les 3 coefficients suivants : rafraichiseement, ruissellement et biodiversité. \n Ce calcul s\'effectue sur la base d\'une classification qui peut se présenter sous 2 configurations possibles.\n Ainsi qu’une couche dites de découpage par exemple des parcelles ou des ilots. Pour Lyon (et Paris ?), il est possible de générer les ilots automatiquement. \nLa classification doit respecter les classes suivantes: \n Strate haute --> 1\n Strate basse --> 2\n Minéral foncé --> 3 \n Tuiles rouges --> 4\n Surface forte reflectance --> 5 \nTerre nue --> 6 \nOmbre --> 7 \nEau --> 8 \nStrate médiane --> 9 \nZone humide --> 10\n NO_DATA --> 0 \n'
        return self.tr(description)

################################################################################################

    #------Création des éléments de la première fenêtre------#

    def initAlgorithm(self, config=None):
        
        #---Etendue de travail---#

        self.addParameter(QgsProcessingParameterExtent(self.INPUT_extend,
            self.tr('Zone de travail'),
            defaultValue=None))

        #---Choix du type de classification de en entrée---#

        self.addParameter(QgsProcessingParameterEnum(
            self.INPUT_classes,
            self.tr('Configuration de la classification en entrée'),
            options = [
                self.tr('Classes comprises entre 1 et 8 (ex: LandSat)'),
                self.tr('Classes comprises entre 1 et 10 classes (ex: EVA)')
            ],
            allowMultiple = False,
            optional = False))

        #---Choix du type de la couche de classification en entrée---#

        self.addParameter(QgsProcessingParameterEnum(
                self.choix,
                self.tr('Format de la classification en entrée'),
                options=[
                    self.tr('Vecteur'),
                    self.tr('Raster')
                    ],
                defaultValue='Vecteur',
                allowMultiple = False,
                optional=False))        

        #---Classification au format Raster---#

        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT_classif_ras,
            self.tr('Classification raster'),
            defaultValue=None,
            optional=True))

        #---Paramètre de la classification au format Vecteur---#

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_classif_vec,
            self.tr('Classification vecteur'),
            [QgsProcessing.TypeVectorPolygon],
            optional=True))

        self.addParameter(QgsProcessingParameterField(self.INPUT_champ,
            self.tr('Champ contenant les valeurs de classification'),
            allowMultiple= False,
            optional= True,
            parentLayerParameterName = self.INPUT_classif_vec))

        #---Défintion de la résolution souhaitée pour la classification---#

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_resolution,
            self.tr('Résolution de la classification en m / pixel'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1,
            optional=True))

        #---Choix du Calcul par ilots ou par parcelles---#

        self.addParameter(QgsProcessingParameterBoolean(self.INPUT_ilot,
            self.tr('Indicateurs calculés par îlot ?'),
            defaultValue=False))

        #---Couche des zones de calcul---#

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_parcelle,
            self.tr('Aires de calcul'),
            [QgsProcessing.TypeVectorPolygon],
            optional=True))

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

        #---Récupération de l'étendue de travail---#

        extend= self.parameterAsExtent(parameters,self.INPUT_extend, context)

        #---récupération du système de coordonnées de l'étendue---#

        crs= self.parameterAsExtentCrs(parameters,self.INPUT_extend, context)

        champ = self.parameterAsString(parameters,self.INPUT_champ, context)

        #---si l'étendue n'est pas en Lambert 93 [2154]---#

        if (crs.authid != 'EPSG:2154'):
            
            #---Reprojection de l'étendue---#

            destCrs = QgsCoordinateReferenceSystem('EPSG:2154')
            coordinateTransformer2154 = QgsCoordinateTransform(crs, destCrs, QgsProject.instance())
            extend= coordinateTransformer2154.transform(extend)  

            feedback.pushInfo('\n la reprojection en EPSG:2154 est valide: {}'.format(coordinateTransformer2154.isValid()))

        #---Récupération de la couche parcelles---#

        parcelle = parameters['INPUT_parcelle']

        #---Récupération du système de coordonnées de la couche parcelles---#

        crs = self.parameterAsCrs(parameters,'INPUT_parcelle',context)

        #---si la couche parcelles n'est pas en Lambert 93---#

        if (crs.authid != 'EPSG:2154'):

            feedback.pushInfo('\n reprojection en cous...')

            trans=processing.run("native:reprojectlayer", {
                'INPUT' : parcelle,
                'TARGET_CRS' : 'EPSG:2154',
                'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
            parcelle = trans

        #---réparation des géométries---#

        feedback.pushInfo('\n Vérification des géométries...')

        fix = processing.run("native:fixgeometries",{
            'INPUT':parcelle,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        parcelle = fix

        #---selection/extraction des parcelles dans la zone de travail---#

        parcelle.selectByRect(extend)

        feedback.pushInfo('\n extraction des parcelles...')

        select = processing.run("native:saveselectedfeatures",{
            'INPUT':parcelle,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        parcelle = select
        parcelle.removeSelection()
        decoupage = parcelle

        #---récupération du choix de calcul ilot/parcelles---#

        ilot = self.parameterAsBool(parameters,self.INPUT_ilot, context)

################################################################################################

        #---connection a la base de données PostGIS---#

        try:
            conn = psycopg2.connect(dbname='Indigen_db', port='5432', user='postgres', host='10.47.52.20', password='Tribu/21')
        except:
            feedback.pushInfo('\n I am unable to connect to the database \n')
        cur = conn.cursor()

        #---si le choix est le calcul par ilot---#

        if ilot is True:
            
            #---calcul des ilots---#

            #---creation des tables contenant les entités permettant de calculer les ilots---#

            feedback.pushInfo('\n calcul des ilots...')

            sql='DROP TABLE IF EXISTS surf_hydro_temp;'
            cur.execute(sql)
            
            sql='CREATE TABLE surf_hydro_temp AS SELECT id,geom from surface_hydrographique WHERE ST_Intersects(ST_MakeEnvelope('+str(extend.xMinimum())+','+str(extend.yMinimum())+','+str(extend.xMaximum())+','+str(extend.yMaximum())+',2154),geom);'
            cur.execute(sql)
            conn.commit()
            
            sql='DROP TABLE IF EXISTS voies_fer_temp;'
            cur.execute(sql)
 
            sql='CREATE TABLE voies_fer_temp AS SELECT id,geom from troncon_de_voie_ferree WHERE (nature=\'Voie ferrée principale\' or nature=\'LGV\') and ST_Intersects(ST_MakeEnvelope('+str(extend.xMinimum())+','+str(extend.yMinimum())+','+str(extend.xMaximum())+','+str(extend.yMaximum())+',2154),geom);'
            cur.execute(sql)
            conn.commit()           

            sql='DROP TABLE IF EXISTS cours_eau_temp;'
            cur.execute(sql)
           
            sql='CREATE TABLE cours_eau_temp AS SELECT  gid,code_hydro,geom  from cours_d_eau WHERE ST_Intersects(ST_MakeEnvelope('+str(extend.xMinimum())+','+str(extend.yMinimum())+','+str(extend.xMaximum())+','+str(extend.yMaximum())+',2154),geom);'
            cur.execute(sql)
            conn.commit()
            
            sql='DROP table IF EXISTS routes_temp;'
            cur.execute(sql)

            sql='CREATE Table routes_temp AS SELECT id,geom,importance from troncon_de_route WHERE ST_Intersects(ST_MakeEnvelope('+str(extend.xMinimum())+','+str(extend.yMinimum())+','+str(extend.xMaximum())+','+str(extend.yMaximum())+',2154),geom) '
            sql=sql+'AND nature in (\'Type autoroutier\',\'Route à 2 chaussées\', \'Route à 1 chaussée\' , \'Rond-point\') AND (nom_1_g NOT LIKE \'TUNNEL%\' OR nom_1_g IS NULL) ;'     
             
            cur.execute(sql)
            conn.commit()

            uri = QgsDataSourceUri()

            #---set host name, port, database name, username and password---#

            uri.setConnection('10.47.52.20', "5432", "Indigen_db", "postgres", "Tribu/21")

            #---creation d'une liste pour stocker les éléments des tables précédemment construites---#

            fusion_layer=[]

            #---

            uri.setDataSource('public', 'cours_eau_temp', 'geom', '', 'gid')
            cours_eau_db = QgsVectorLayer(uri.uri(), 'cours_eau', 'postgres')

            if cours_eau_db.featureCount() == 0 :
                feedback.pushInfo('il n\'y a pas de cours d\'eau sur cette zone')
            else:
                fusion_layer.append(cours_eau_db)
                feedback.pushInfo('Ajout des cours d\'eau')

            #--- 

            #-En cas d'annulation-#           
            annulation()

            #---

            uri.setDataSource('public', 'voies_fer_temp', 'geom', '', 'id')
            voies_fer_db = QgsVectorLayer(uri.uri(), 'voie_fer_db', 'postgres')

            if voies_fer_db.featureCount() == 0 :
                feedback.pushInfo('il n\'y a pas de voies ferrées sur cette zone')
            else:
                fusion_layer.append(voies_fer_db)   
                feedback.pushInfo('Ajout des voies ferrées')

            #---
                
            #-En cas d'annulation-#
            annulation()

            #---

            uri.setDataSource('public', 'routes_temp', 'geom', '', 'id')
            routes_temp = QgsVectorLayer(uri.uri(False), 'routes_db', 'postgres')
            
            if routes_temp.featureCount() == 0 :
                feedback.pushInfo('il n\'y a pas de routes sur cette zone, CREATION DES ILOTS IMPOSSIBLE')
                iface.messageBar().pushMessage("il n\'y a pas de routes dans la base de données sur cette zone, CREATION DES ILOTS IMPOSSIBLE", level=2, duration=10)
                return{}
            else:
                fusion_layer.append(routes_temp)   
                feedback.pushInfo('Ajout des routes')

            #---  
                
            #-En cas d'annulation-#
            annulation() 

            #---    
                
            uri.setDataSource('public', 'surf_hydro_temp', 'geom', '', 'id')    
            surf_eau_db = QgsVectorLayer(uri.uri(), 'surf_hydro_temp', 'postgres')
            
            if surf_eau_db.featureCount() == 0 :
                feedback.pushInfo('il n\'y a pas d\'eau sur cette zone')
            else:
                surf_hydro_temp=processing.run("qgis:polygonstolines", {
                    'INPUT':surf_eau_db,
                    'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
                fusion_layer.append(surf_hydro_temp)   
                feedback.pushInfo('Ajout des plans d\'eau')     

            #--- 

            #-En cas d'annulation-#  
            annulation()      

            #---fusion des éléments de la liste pour former une couche---#
            
            ilot_vec=processing.run("qgis:mergevectorlayers", {
                'LAYERS':fusion_layer,
                'CRS':QgsCoordinateReferenceSystem('EPSG:2154'),
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
            
            #-En cas d'annulation-#
            annulation() 
            
            #---définition d'un cadre autour de la couche précédentes pour la fermer---#

            ilot_vec.startEditing()
            
            cadre = QgsFeature(ilot_vec.fields())
            cadre.setAttribute('id',0)
    
            line_corner1= QgsPoint(extend.xMinimum(), extend.yMinimum())
            line_corner2= QgsPoint(extend.xMaximum(), extend.yMinimum())
            line_corner3= QgsPoint(extend.xMaximum(), extend.yMaximum())
            line_corner4= QgsPoint(extend.xMinimum(), extend.yMaximum())
            cadre.setGeometry(QgsGeometry.fromPolyline([line_corner1,line_corner2,line_corner3,line_corner4,line_corner1]))  
            
            feedback.pushInfo('\n ajout du cadre pour fermer les polygone: {}'.format( ilot_vec.dataProvider().addFeature(cadre)))
            ilot_vec.commitChanges()
            
            #-En cas d'annulation-#
            annulation()
            
            feedback.pushInfo('creation des polygones avec domaine public')

            ilot_vec=processing.run("qgis:polygonize", {
                'INPUT':ilot_vec,
                'KEEP_FIELDS':False,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
                
            #-En cas d'annulation-#
            annulation() 
            
            #---extraction des ilots de la base---#

            extend.grow(-0.00001)
            ilot_vec.selectByRect(extend)
                        
            ilot_vec = processing.run("qgis:saveselectedfeatures", {
                'INPUT': ilot_vec, 
                'OUTPUT':'memory:'})['OUTPUT']
            ilot_vec.removeSelection()

            ilot_vec =processing.run("native:difference", 
                {'INPUT':ilot_vec,
                'OVERLAY':surf_eau_db,
                'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)['OUTPUT']

            decoupage = ilot_vec

################################################################################################

        #---récupération du choix du type de classification---#

        choix= self.parameterAsEnum(parameters, self.choix, context)

        #---récupération de la résolution---#

        resolution = self.parameterAsDouble(parameters, self.INPUT_resolution,context)

        #---Si la classification source est en vecteur---#

        if choix == 0 :

            #---récupération de la classification au format vecteur---#

            vec = parameters['INPUT_classif_vec']

            #---récupération du système de coordonnées de la classification au format vecteur---#

            crs = self.parameterAsCrs(parameters,'INPUT_classif_vec',context)

            #---Si le système de coordonnées n'est pas en 2154---#

            if (crs.authid != 'EPSG:2154'):
                
                feedback.pushInfo('\n Reprojection en cours...')

                trans=processing.run("native:reprojectlayer", {
                    'INPUT' : vec,
                    'TARGET_CRS' : 'EPSG:2154',
                    'OUTPUT' : 'TEMPORARY_OUTPUT'})['OUTPUT']
                vec = trans
            
            #---réparations des géométries---#

            feedback.pushInfo('\n Vérification des géométries...')

            fix = processing.run("native:fixgeometries",{
                'INPUT':vec,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

            vec = fix

            #---selection/extraction des entités dans la zone de travail---#

            vec.selectByRect(extend)

            feedback.pushInfo('\n Extraction des entités...')

            select = processing.run("native:saveselectedfeatures",{
                'INPUT':vec,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
            vec = select
            vec.removeSelection()

            #---creation d'un raster vierge pour la reception des éléments de la classification---#

            feedback.pushInfo('\n Créationde du raster d impression...')

            reception =processing.run("native:createconstantrasterlayer", {
                'EXTENT': extend,
                'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2154'),
                'PIXEL_SIZE':resolution,                                         
                'NUMBER':0,
                'OUTPUT_TYPE':5,
                'OUTPUT':'TEMPORARY_OUTPUT'})

            raster = QgsRasterLayer(reception['OUTPUT'])
            
            #---impression de la classification vecteur sur le raster vierge---#

            feedback.pushInfo('\n Rasterisation de la classification...')

            ras = processing.run("gdal:rasterize_over",{
                'INPUT':vec,
                'INPUT_RASTER':raster,
                'FIELD':champ,
                'ADD':False,
                'EXTRA':''})['OUTPUT']

        else :
            
            #---récupération de la classification au format raster---#

            ras = self.parameterAsRasterLayer(parameters,self.INPUT_classif_ras,context)
        
        #---Récupération du choix de classification classique ou EVA---#

        classes = self.parameterAsEnum(parameters,self.INPUT_classes,context)

################################################################################################

        #------Calcul/création des champs/couche finales------#
          
        #---Compte du nombre de pixel de chaque classe dans chaque parcelle/ilot---# 
           
        feedback.pushInfo('\n histogramme zonal ... \n')

        stat_layer = processing.run("qgis:zonalhistogram",{
            'INPUT_RASTER': ras,
            'RASTER_BAND':1,
            'INPUT_VECTOR': decoupage,
            'COLUMN_PREFIX':'Nb_Pix_',
            'OUTPUT' : 'TEMPORARY_OUTPUT'
            },context=context,feedback=feedback)

        #-En cas d'annulation-#
        annulation()
            
        feedback.pushInfo('\n histogramme zonal créé\n')

        #---Création de la couche en sortie---#

        nb_fields=0
        formule=''
        
        #---somme des pixels par parcelle/ilot---#

        #---création de la formule---#

        for field in stat_layer['OUTPUT'].fields():
            if field.name().startswith("Nb_Pix")== True and field.name()!="Nb_Pix_7":
                nb_fields=nb_fields+1
                formule=formule+'+"'+field.name()+'"'
    
        formule=formule[1:]        
        
        feedback.pushInfo('formule : {}'.format(formule))

        #-En cas d'annulation-#
        annulation()    

        #---calcul du champ---# 

        stat_layer = processing.run("qgis:fieldcalculator", {
            'INPUT': stat_layer['OUTPUT'],
            'FIELD_NAME':'sumPIX',
            'FIELD_TYPE':1,
            'FIELD_LENGTH':20,
            'FIELD_PRECISION':0,
            'FORMULA': formule,
            'NEW_FIELD': True,
            'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)
            
        #-En cas d'annulation-#       
        annulation()
        
        #---calcul sur les classes---#

        for field in stat_layer['OUTPUT'].fields():
            
            if(field.name().startswith("Nb_Pix")== True and field.name()!="Nb_Pix_7"):

                #---calcul du pourcentage occupé par chaque classe dans chaque parcelle/ilot---#

                formule= 'if("sumPIX" = 0,0,"{}"/"sumPIX")'.format(field.name())
                stat_layer = processing.run("qgis:fieldcalculator", {
                    'INPUT': stat_layer['OUTPUT'],
                    'FIELD_NAME': 'pc_'+field.name(),
                    'FIELD_TYPE':0,
                    'FIELD_LENGTH':20,
                    'FIELD_PRECISION':5,
                    'NEW_FIELD': True,
                    'FORMULA': formule,
                    'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)

                #---calcul de la surface occupée par chaque classe dans chaque parcelle/ilot---#

                nom = ''
                if field.name().endswith('1') == True:
                    nom = 'StrHaute'
                elif field.name().endswith('2') == True:
                    nom = 'StrBasse'
                elif field.name().endswith('3') == True:
                    if classes == 1:
                        nom = 'Minéral'
                    else :
                        nom = 'Minéral foncé'
                elif field.name().endswith('4') == True:
                    nom = 'TuilesRouges'
                elif field.name().endswith('5') == True:
                    nom = 'ForteReflectance'
                elif field.name().endswith('6') == True:
                    nom = 'TerreNue'
                elif field.name().endswith('8') == True:
                    nom = 'Eau'
                elif field.name().endswith('9') == True:
                    nom = 'StrMédiane'
                elif field.name().endswith('10') == True:
                    nom = 'ZoneHumide'
                else :
                    nom = 'Null'
                
                stat_layer = processing.run("qgis:fieldcalculator", {
                    'INPUT': stat_layer['OUTPUT'],
                    'FIELD_NAME': 'Surf_' + nom,
                    'FIELD_TYPE':0,
                    'FIELD_LENGTH':20,
                    'FIELD_PRECISION':1,
                    'NEW_FIELD': True,
                    'FORMULA': '$area*pc_'+field.name(),
                    'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback) 

        #---suppression des colonnes de calcul---# 
                   
        for i in range (11):
            stat_layer = processing.run("qgis:deletecolumn", {
                'INPUT':stat_layer['OUTPUT'],
                'COLUMN':'Nb_Pix_'+str(i),
                'OUTPUT':'TEMPORARY_OUTPUT'})

            feedback.pushInfo("Suppression") #ne pas enlever sinon Qgis plante
        
        stat_layer = processing.run("qgis:deletecolumn", {
                'INPUT':stat_layer['OUTPUT'],
                'COLUMN':'sumPIX',
                'OUTPUT':'TEMPORARY_OUTPUT'})
        
        stat_layer = processing.run("qgis:deletecolumn", {
                'INPUT':stat_layer['OUTPUT'],
                'COLUMN':'pc_Nb_Pix_NODATA',
                'OUTPUT':'TEMPORARY_OUTPUT'})
        
        #-En cas d'annulation-#
        annulation()
            
        #---coefficient de biodiversité pour chaque classe---#

        coef_de_rafraichissement = {
      
        "pc_Nb_Pix_0": 0,
    
        "pc_Nb_Pix_1": 1,
    
        "pc_Nb_Pix_2": 0.5,
     
        "pc_Nb_Pix_3": 0.0,
       
        "pc_Nb_Pix_4": 0.1,
        
        "pc_Nb_Pix_5": 0.3,
        
        "pc_Nb_Pix_6": 0.3,
        
        "pc_Nb_Pix_7": 0,
    
        "pc_Nb_Pix_8": 0.8,

        "pc_Nb_Pix_9": 0.7,

        "pc_Nb_Pix_10": 0.8
        }

        feedback.pushInfo("...")

        #-cas particulier du coeff de rafraichissement pour une couche EVA-#

        if classes == 1 :
            coef_de_rafraichissement["pc_Nb_Pix_3"] = 0.1

        #---création de la formule---#

        formule=''
        
        for field in stat_layer['OUTPUT'].fields():
            if(field.name().startswith("pc_Nb_Pix")== True):
                formule=formule+'+"'+field.name()+'"*'+str(coef_de_rafraichissement.get(field.name(),''))
        
        formule=formule[1:]
        
        feedback.pushInfo('\n la formule du coef rafraichissement est  {} \n'.format(formule))

        #---calcul de coefficient de rafraichissement---#

        stat_layer = processing.run("qgis:fieldcalculator", {
                    'INPUT': stat_layer['OUTPUT'],
                    'FIELD_NAME': 'coef_raf',
                    'FIELD_TYPE':0, 
                    'FIELD_LENGTH':20,
                    'FIELD_PRECISION':2,
                    'NEW_FIELD': True,
                    'FORMULA': formule,
                    'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)
        
        #-En cas d'annulation-#
        annulation()
    
        #---coefficient de biodiversité pour chaque classe---#

        coef_de_biodiversite = {

        "pc_Nb_Pix_0": 0,
        
        "pc_Nb_Pix_1": 1,
        
        "pc_Nb_Pix_2": 0.6,
    
        "pc_Nb_Pix_3": 0,

        "pc_Nb_Pix_4": 0,

        "pc_Nb_Pix_5": 0,
    
        "pc_Nb_Pix_6": 0.2,
    
        "pc_Nb_Pix_7": 0,

        "pc_Nb_Pix_8": 1,

        "pc_Nb_Pix_9": 1,

        "pc_Nb_Pix_10": 1
        }

        #---création de la formule---#

        formule=''
        
        for field in stat_layer['OUTPUT'].fields():
            if(field.name().startswith("pc_Nb_Pix")== True):
                formule=formule+'+"'+field.name()+'"*'+str(coef_de_biodiversite.get(field.name(),''))
        
        formule=formule[1:]
        
        feedback.pushInfo('\n la formule du coef biodiversité est  {} \n'.format(formule))

        #---calcul de coefficient de biodiversité---#

        stat_layer = processing.run("qgis:fieldcalculator", {
                    'INPUT': stat_layer['OUTPUT'],
                    'FIELD_NAME': 'coef_bio',
                    'FIELD_TYPE':0,
                    'FIELD_LENGTH':20,
                    'FIELD_PRECISION':2,
                    'NEW_FIELD': True,
                    'FORMULA': formule,
                    'OUTPUT':'TEMPORARY_OUTPUT'},context=context,feedback=feedback)
        
        #-En cas d'annulation-#
        annulation()
        
        #---coefficient de ruissellement pour chaque classe---#

        coef_de_ruissellement = {
    
        "pc_Nb_Pix_0": 0,
    
        "pc_Nb_Pix_1": 0.2,
        
        "pc_Nb_Pix_2": 0.2,
   
        "pc_Nb_Pix_3": 0.9,
        
        "pc_Nb_Pix_4": 0.9,
        
        "pc_Nb_Pix_5": 0.9,
        
        "pc_Nb_Pix_6": 0.6,
        
        "pc_Nb_Pix_7": 0,
        
        "pc_Nb_Pix_8": 0.2,

        "pc_Nb_Pix_9": 0.2,

        "pc_Nb_Pix_10": 0.2
        }

        #---création de la formule---#

        formule=''

        for field in stat_layer['OUTPUT'].fields():
            if(field.name().startswith("pc_Nb_Pix")== True):
                formule=formule+'+"'+field.name()+'"*'+str(coef_de_ruissellement.get(field.name(),''))
        
        formule=formule[1:]
        
        feedback.pushInfo('\n la formule du coef de ruissellement est  {} \n'.format(formule))

        #---calcul de coefficient de ruissellement---#

        stat_layer = processing.run("qgis:fieldcalculator", {
                    'INPUT': stat_layer['OUTPUT'],
                    'FIELD_NAME': 'coef_rui',
                    'FIELD_TYPE':0,
                    'FIELD_LENGTH':20,
                    'FIELD_PRECISION':2,
                    'NEW_FIELD': True,
                    'FORMULA': formule,
                    'OUTPUT':'TEMPORARY_OUTPUT'},
                    context=context,feedback=feedback)

        #-En cas d'annulation-#
        annulation()      

################################################################################################
        
        #---suppression des colonnes de calcul---#

        for i in range (11):
            stat_layer = processing.run("qgis:deletecolumn", {
                'INPUT':stat_layer['OUTPUT'],
                'COLUMN':'pc_Nb_Pix_'+str(i),
                'OUTPUT':'TEMPORARY_OUTPUT'})

            feedback.pushInfo("Suppression") #ne pas enlever sinon Qgis plante

        #---Affichage de la couche ainsi créée---#

        sortie = 'Indi_En_V2.2'

        if choix == 0:
            a = '_vec'
        else:
            a = '_ras'

        sortie += a

        if classes == 0:
            a = '_8'
        else:
            a = '_10'

        sortie += a

        if ilot == True:
            a = '_ilot'
        else:
            a= '_parcelle'
        
        sortie += a

        stat_layer['OUTPUT'].setName(sortie)   
        QgsProject.instance().addMapLayer(stat_layer['OUTPUT'])
        
        #-En cas d'annulation-#
        annulation()

################################################################################################

        #------Nettoyage------#

        #---suppression des tables de calcul---#

        sql='DROP table IF EXISTS parcelles_temp'
        cur.execute(sql)
        conn.commit()

        sql='DROP table IF EXISTS  classif_temp'
        cur.execute(sql)
        conn.commit()

        sql='DROP table IF EXISTS routes_temp'
        cur.execute(sql)
        conn.commit()

        sql='DROP table IF EXISTS voies_fer_temp'
        cur.execute(sql)
        conn.commit()

        sql='DROP table IF EXISTS  cours_eau_temp'
        cur.execute(sql)
        conn.commit()

        sql='DROP table IF EXISTS surf_hydro_temp'
        cur.execute(sql)
        conn.commit()

        #---fermeture de la connexion à la base de donnée---#

        conn.close()
        
        return{}

#---------------FIN---------------#