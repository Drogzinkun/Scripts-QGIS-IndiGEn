#-*- coding: utf-8 -*-#
#------------ Dispersion ------------#
#--- Version : 0.1 ---#
#--- QGIS : 3.22.7 ---#

################################################################################################

#---------------DEBUT---------------#

#---------Import---------#

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
                       QgsProperty
                    )

from qgis import processing

import operator

from PyQt5.QtWidgets import QInputDialog

################################################################################################

#---------Initialisation---------#

class dispersion(QgsProcessingAlgorithm):
    
    #------Définition des entrées, sorties et constantes------#

    INPUT_extend = 'INPUT_extend'
    INPUT_liste = 'INPUT_liste'
    INPUT_reserv = 'INPUT_reserv'
    
    #------Fonctions/Nomenclatures nécessaires au fonctionnement------#
    
    #---

    #def flags(self):
        #return super().flags() | QgsProcessingAlgorithm.FLagNoThreading

    #---Permet d'afficher les textes avec des caractères spéciaux---#

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    #---Permet au script de se lancer dans QGIS---#

    def createInstance(self):
        return dispersion()

    #---Nom du script---# 

    def name(self):
        return 'dispersion'

    #---Nom du script avec caractères spéciaux---#

    def displayName(self):
        return self.tr('Dispersion')

    #---Nom du groupe auquel appartient le script---#

    def group(self):
        return self.tr('INDIGEN_CB')

    #---ID du groupe auquel appartient le script---#

    def groupId(self):
        return 'INDIGEN_CB'

    #---Description du script sur la droite de la fenetre initiale---#

    def shortHelpString(self):
        description='REF Documentation : Script 6 \n Ce script permet de modéliser la dispersion de différentes espèces en fonction d’une occupation du sol. \n Il est possible de créer une carte de friction ou de cout. Les réservoirs servent de points de départs. Il est possible de modifier les coefficients selon les espèces ou les trames que l’on cherche à modéliser. \n Cela permet de mettre en évidence les couloirs de biodiversité sur un territoire.'
        return self.tr(description)

################################################################################################

    #------Création des éléments de la première fenêtre------#

    def initAlgorithm(self, config=None):

        #---Couche au format vecteur représentant les réservoirs de biodiversité---#

        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT_reserv,
            self.tr('Reservoir(s)'),
            [QgsProcessing.TypeVectorPolygon],
            optional=False))

        #---Liste des couches permettant de produire la carte de friction---#

        self.addParameter(
            QgsProcessingParameterMultipleLayers(self.INPUT_liste,
            self.tr('Couche(s) d\'occupation du sol')))

        #---Etendue de travail---#

        self.addParameter(QgsProcessingParameterExtent(self.INPUT_extend,
            self.tr('Zone de travail'),
            defaultValue=None))

################################################################################################

    #------Actions du script------#

    def processAlgorithm(self, parameters, context, feedback):

        #------Fonctions------#

        #---INPUT---#

        def entree(titre, message): ################################################################################################

            answer = QInputDialog.getText(None, titre, message)
            if answer[1]:
                print(answer[0])
                return answer[0]
            else:
                return None

        #---Permet à un utilisateur de sélectionner un champ dans une couche---#

        def champs(couche, texte) : ################################################################################################

            c = 0
            question = "Champ à utiliser pour catégoriser : tapez 0 si pas d'importance \n "
            for field in couche.fields():
                c += 1
                question += field.name().upper() + " tapez : " + str(c) + "\n"
            verif = True
            while verif :
                try :
                    num_champ = int(entree(texte, question))
                    verif = False
                except:
                    feedback.pushInfo("erreur de saisie")

            return num_champ

        #---Permet à un utilisateur d'associer un coefficient à chaque valeur unique d'un champ---#

        def formule(couche,numero,texte): ################################################################################################
            liste = []
            lim = couche.featureCount()

            if numero == 0 :

                verif = True
                while verif :
                    try:

                        form = int(entree("Valeur de " + texte, texte + " pour :" + couche.name()))
                        verif=False
                    except:
                        feedback.pushInfo("erreur de saisie")
            else:

                rep = "0"

                if couche.fields()[numero -1].typeName() == "Integer64" or couche.fields()[numero-1].typeName() == "Real":
                    verif = True
                    while verif :
                        try:
                            rep = int(entree("Choix","Champ numérique : Faire des intervalles ? \n 1 - OUI // 2 - NON"))
                            verif = False
                        except:
                            feedback.pushInfo("erreur de saisie")

                if rep == 1:

                    verif = True
                    while verif :
                        try:
                            boucle = int(entree("intervalles","Combien d\' intervalles souhaitées ?"))
                            verif = False
                        except:
                            feedback.pushInfo("erreur de saisie")
                    formule = "CASE"
                    borne_bas = "0"
                    borne_haut = "0"
                    v = False

                    for i in range (0,boucle):
                        formule += " WHEN "
                        formule += couche.fields()[numero-1].name() + " > " + borne_bas
                        formule += " AND "
                        while (v == False):
                            borne_haut = str(entree("Choix en cours","Borne ?"))
                            if (borne_haut) <= (borne_bas):
                                feedback.pushInfo("erreur de saisie")
                            else:
                                v = True
                        v = False
                        formule += couche.fields()[numero-1].name() + " <= " + borne_haut
                        friction = str(entree("friction","Friction pour l'intervalle : "+ borne_bas + " - " + borne_haut + "?"))
                        formule += " THEN " + friction
                        feedback.pushInfo(str(friction)+ "   friction")
                        feedback.pushInfo(str(borne_bas)+ "   borne bas")
                        feedback.pushInfo(str(borne_haut)+ "    borne haute")
                        borne_bas = borne_haut

                    formule += " ELSE 1 END"

                    form = formule

                else :

                    for id in range(0, lim):
                        ligne = couche.getFeature(id)
                        val = ligne[numero-1]
                        if val not in liste:

                            liste.append(val)

                    dic = {}
                    for indiv in liste:
                        verif = True
                        while verif:
                            try:
                                coeff_friction = int(entree("Valeur de " + texte,texte + " pour : " + str(indiv)))
                                verif = False
                            except:
                                feedback.pushInfo("erreur de saisie")

                        dic[str(indiv)] = coeff_friction
    
                    form = "CASE "
                    for cle,valeur in dic.items():
                        form += " WHEN "
                        if couche.fields()[numero-1].typeName() == "String":

                            form += couche.fields()[numero-1].name() + " = " + "'" + str(cle) + "'" + " THEN " + str(valeur)

                        else:

                            form += couche.fields()[numero - 1].name() + " = " + str(cle) + " THEN " + str(valeur)

                    form += " ELSE 1 END"

            feedback.pushInfo(str(form))
            return(form)

        #---permet d'obtenir le minimum et la maximum d'une liste de valeur---#

        def minmax(formulax): ################################################################################################
            liste = []
            chiffre = ["0","1","2","3","4","5","6","7","8","9"]
            res = ""
            mini = 0
            maxi = 0
            formulax=str(formulax)
    
            for i in formulax:
                if i in chiffre:
                    res += i
        
                if i == " " and res != "":
                    liste.append(int(res))
                    res = ""

            if res != "":
                liste.append(int(res))

            else:
                fin = len(liste)
                del liste[fin-1]
                feedback.pushInfo(str(fin))
            
            for j in liste:
                if j< mini or mini == 0:
                    mini = j
                if j> maxi or maxi == 0:
                    maxi = j
    
            return mini,maxi

        #---Permet à un utilisateur d'ordonner une liste de couches---#

        def ordre(liste): ################################################################################################
            dic = {}
            res = []
            question = "Dans quel ordre on affiche les couches ?"
            verification = False
            lim = len(liste)
            somme = 0
            sum_verif = 0
            c = 0

            while lim > 0:
                somme += lim
                lim = lim - 1

            for i in liste :
                dic[c] = i
                c += 1
                question += "\n" + i.name() + "   " + str(c)

            while (verification == False):
                reponse = str(entree("Ordre des couches",question +" \n ordre ? Exemple: 2143"))
                for veri in reponse:
                    f = int(veri)
                    sum_verif += f
        
                if (sum_verif) == (somme):
                    verification = True
                sum_verif = 0

            for j in reponse :
                b = int(j)-1
                res.append(dic.get(b))

            return(res)

        #-Fonction pour gérer les annulations-#
        def annulation():
            feedback.pushInfo("Execution en cours ...")
            if feedback.isCanceled():
                return {}

################################################################################################

        #---Récupération des données en entrée---#

        extent = self.parameterAsExtent(parameters, self.INPUT_extend, context)

        list = self.parameterAsLayerList(parameters, self.INPUT_liste, context)

        vecteur = self.parameterAsVectorLayer(parameters, self.INPUT_reserv, context)

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Création du raster qui servira de base à la carte de friction---#

        raster = processing.run("native:createconstantrasterlayer", {
            'EXTENT': extent,
            'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2154'),
            'PIXEL_SIZE':1,
            'NUMBER':1,
            'OUTPUT_TYPE':5,
            'OUTPUT':'TEMPORARY_OUTPUT'})

        raster = QgsRasterLayer(raster['OUTPUT'])

        #-En cas d'annulation-#
        annulation()

        #---On ordonne la liste des couches en entrée---#

        liste = ordre(list)

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---Pour chaque couche de la liste---#

        for i in liste:

            #---On selectionne le champ qui va permettre de définir la friction---#
            
            num_champ_friction = champs(i,"champ de friction pour " + i.name())

            #-En cas d'annulation-#
            annulation()

            #---On génère la formule selon le champ choisi---#

            formula = formule(i, num_champ_friction,"friction")

            #-En cas d'annulation-#
            annulation()

################################################################################################

            #---Si c'est une couche de type ligne ou polyligne---#

            feedback.pushInfo(str(i.wkbType()))

            if str(i.wkbType()) == "5" or str(i.wkbType()) == "1005" or str(i.wkbType()) == "2":

                #---On selectionne le champ qui va permettre de définir le buffer---#

                num_champ_buffer = champs(i , "champ de tampon")

                #-En cas d'annulation-#
                annulation()

                #---On génère la formule selon le champ choisi---#

                formula_buff = formule(i, num_champ_buffer,"buffer")

                #-En cas d'annulation-#
                annulation()

                #---On ajoute le champ qui va permettre de faire des buffers de différentes tailles---#

                i = processing.run ("qgis:fieldcalculator",{
                'INPUT': i,
                'FIELD_NAME': 'buff',
                'FIELD_TYPE': 1,
                'FIELD_LENGTH':10,
                'NEW_FIELD':True,
                'FORMULA':formula_buff,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

                #-En cas d'annulation-#
                annulation()

                #---On récupère le minimum et maximum de la valeur de buffer---#

                mini,maxi = minmax(formula_buff)
                feedback.pushInfo(str(mini) +"  "+ str(maxi))

                #-En cas d'annulation-#
                annulation()

                #---Si le minimum et le maximum sont égaux---#

                if mini == maxi :

                    #-On utilise un buffer classqiue-#

                    feedback.pushInfo("buffer normal")
                    i = processing.run("native:buffer",{
                        'INPUT': i,
                        'DISTANCE': maxi,
                        'SEGMENTS':5,
                        'END_CAP_STYLE':0,
                        'JOIN_STYLE':0,
                        'MITER_LIMIT':2,
                        'DISSOLVE':False,
                        'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

                    #-En cas d'annulation-#
                    annulation()

                else:

                    #-On utilise un buffer avec une taille variable-# 
                     
                    feedback.pushInfo("buffer condition")
                    i = processing.run("native:buffer", {
                        'INPUT': i,
                        'DISTANCE': QgsProperty.fromExpression('coalesce(scale_linear("buff",%s,%s,%s,%s), 0)' % (mini,maxi,mini,maxi) ),
                        'SEGMENTS':5,
                        'END_CAP_STYLE':0,
                        'JOIN_STYLE':0,
                        'MITER_LIMIT':2,
                        'DISSOLVE':False,
                        'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

                    #-En cas d'annulation-#
                    annulation()

            #---On ajoute le champ correspondant à la friction---#
            
            i = processing.run ("qgis:fieldcalculator",{
                'INPUT': i,
                'FIELD_NAME': 'friction',
                'FIELD_TYPE': 1,
                'FIELD_LENGTH':10,
                'NEW_FIELD':True,
                'FORMULA':formula,
                'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

            #-En cas d'annulation-#
            annulation()

            #---On imprime la couche en utilisant les valeurs du champ de friction---#

            raster = processing.run("gdal:rasterize_over", {
                'INPUT': i,
                'INPUT_RASTER':raster,
                'FIELD':'friction', 
                'ADD':False,
                'EXTRA':''})

            raster = QgsRasterLayer(raster['OUTPUT'])

            #-En cas d'annulation-#
            annulation()

################################################################################################

        feedback.pushInfo("Fin de la liste")

        #---On imprime les réservoirs de biodiversité---#

        raster = processing.run("gdal:rasterize_over_fixed_value", {
            'INPUT':vecteur,
            'INPUT_RASTER':raster,
            'BURN':0,
            'ADD':False,
            'EXTRA':''})

        raster = QgsRasterLayer(raster['OUTPUT'])

        #-En cas d'annulation-#
        annulation()

        #---On affiche la carte de Friction---#

        raster.setName('Friction')
        QgsProject.instance().addMapLayer(raster)

        #-En cas d'annulation-#
        annulation()

        #---On utilise les centroides des réservoirs comme des points de départ---#

        départ = processing.run("native:centroids", {
            'INPUT':vecteur,
            'ALL_PARTS':False,
            'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']

        #-En cas d'annulation-#
        annulation()

        #---L'utilisateur determine le coup alloué pour la dispersion---#
        verif = True
        while verif:
            try:
                coutmax = int(entree("cout", "quel est le cout maximale ?"))
                verif = False
            except:
                feedback.pushInfo("erreur de saisie")

        #-En cas d'annulation-#
        annulation()

        #---On lance le calcul de la dispersion---#

        final = processing.run("grass7:r.cost", {
            'input':raster,
            'start_coordinates':None,
            'stop_coordinates':None,
            '-k':False,
            '-n':True,
            'start_points':départ,
            'stop_points':None,
            'start_raster':None,
            'max_cost':coutmax,
            'null_cost':None,
            'memory':600,
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

        #-En cas d'annulation-#
        annulation()

################################################################################################

        #---On affiche la carte de dispersion---#

        final.setName('Dispersion')
        QgsProject.instance().addMapLayer(final)

        #-En cas d'annulation-#
        annulation()

        return{}

#---------------FIN---------------#