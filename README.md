# Segmentation « Segmentation du foie et de la cavité abdominale pour l'appariement donneur / receveur en transplantation hépatique »

Laura Seimpere : laura.seimpere@etu.unistra.fr

# NOTICE D’UTILISATION DES MODULES PERSONNALISÉS CRÉÉS SOUS 3D SLICER
 
# UTILISATION DE 3D SLICER POUR LA

## A)	 SEGMENTATION DU FOIE


**1. OUVRIR** le logiciel "3D Slicer"


**2.** Dans le menu déroulant "Welcome to Slicer", **CHOISIR LE MODULE CRÉÉ** appelé "Pour le DONNEUR : Segmentation semi-automatique du foie" puis cliquer sur "Étapes de la segmentation du foie"


**3. CHOISIR LA MÉTHODE D'IMPORTATION DES IMAGES**

   - **3.1. A partir d'un dossier de l'ordinateur contenant des fichiers DICOM :**
	
      •	Cliquer sur la barre de recherche de répertoire à côté de l’option "Charger depuis DICOM" puis cliquer sur "Importer et charger"
	
   - **3.2. A partir d'images préalablement (ou non) chargées sous 3D Slicer :**
	
     • **Si les images ont été préalablement chargées sous 3D Slicer**
	
      - Cliquer sur "Charger depuis SLICER" pour sélectionner cette option

      - Ignorer la pop-up "Charger les images" qui apparaît en cliquant sur "Cancel"

      - Choisir dans le menu déroulant le volume à charger parmi ceux disponibles

      - Cliquer sur "Importer et charger" au bout de la ligne de l'option sélectionnée "Charger depuis SLICER"

     • **Si les images n’ont pas été préalablement chargées sous 3D Slicer**
	
      - Cliquer sur "Charger depuis SLICER" pour sélectionner cette option

      - Une pop-up "Charger les images" apparaît pour donner à l'utilisateur les consignes à suivre :
Cliquer sur "Ok" si toutes les informations sont comprises

      - Une autre pop-up appelée "DICOM" s'est affichée simultanément en arrière-plan de l'écran

      - Cliquer sur "Show DICOM Browser"

        o Soit choisir "Import" en haut à gauche puis suivre la démarche de recherche d'images DICOM dans les répertoires de l’ordinateur

        o Soit choisir parmi les volumes d'images déjà chargés dans 3D Slicer et qui s’affichent dans le premier tableau avec un classement par "PatientsName" :
	
         • Cliquer sur le volume désiré (par exemple : cd 11) puis sur la modalité d'imagerie à analyser, affichée dans le troisième tableau (par exemple : AP Artériel 3.0 l30f)
		
         • Cliquer sur "Load" en bas à gauche de la fenêtre
		
         • Fermer la petite fenêtre "DICOM" en cliquant sur la croix en haut à droite de la fenêtre

	 • De retour sur notre module, charger les images dans le module courant en cliquant sur "Importer et charger" au bout de la ligne de l'option sélectionnée "Charger depuis SLICER"


**4. ÉTAPE OPTIONNELLE : CALCUL DE SIGMA SUR UNE ZONE HOMOGÈNE**

•	Sélectionner "Create new annotationROI" dans le premier menu déroulant "Région d’intérêt à rogner"

•	Laisser coché "Rognage extérieur"

•	Sélectionner "Create new volume" dans le menu déroulant "Volume de sortie"

•	Si le carré de la région à sélectionner n’apparaît pas à l’écran dans un des plans anatomiques, dézoomer sur le rendu 3D en haut à droite du carré visuel puis tirer sur le rectangle avec les boules colorées en cliquant sur chaque boule pour positionner le cadre au niveau du foie : jouer avec les autres vues et les différentes coupes pour optimiser le cadrage d'un segment de foie afin de calculer son homogénéité

•	Une fois le cadre correctement placé, cliquer sur "Exécuter le rognage"

•	Les résultats apparaissent alors dans la box "Résultats", située sous "Exécuter le rognage"; il s’agit de la valeur de la moyenne et de la valeur de sigma, calculées sur la zone du foie sélectionnée par l’utilisateur

•	Pour continuer la segmentation du foie, il est préconisé de retourner à l’étape précédente, de recharger les images à analyser puis de passer à l’étape suivante de Filtrage


**5. FILTRAGE**

•	Choisir parmi les filtres "Filtre médian" ou "Filtre gaussien" (filtre sélectionné par défaut) en cliquant dessus pour le sélectionner

•	Choisir, dans le menu déroulant du filtre sélectionné, la taille du rayon désiré pour le filtre médian ou la valeur de l'écart-type sigma pour le filtre gaussien

•	Cliquer sur "Exécuter le filtrage"

•	Si le rendu visuel ne semble pas assez homogène, ne pas hésiter à changer les paramètres des filtres et cliquer de nouveau sur "Exécuter le filtrage"


**6. HISTOGRAMME ET SEUILLAGE**

•	Cliquer sur "Configurer l’histogramme" : la pop-up "Pic du foie" décrit à l'utilisateur ce qu'il doit faire :
 Cliquer sur "Ok" si toutes les informations sont comprises

•	La box "Résultats" affiche la valeur maximale de l'histogramme correspondant au pic du foie avec son numéro d'indice

•	Choisir alors la borne "Avant le pic du foie" et celle "Après le pic du foie" pour encadrer la valeur de cet indice de pic maximum à l’aide des curseurs manuels (des valeurs de ± 10 par rapport à l’indice affiché sont un minimum)

•	Cliquer sur "Exécuter l’histogramme et le seuillage" et visualiser le résultat dans les trois plans anatomiques et en parcourant les différentes coupes

**N.B. :** Si l’utilisateur veut visualiser l’histogramme :

    o Glisser sur l’épingle en haut à gauche de la fenêtre de visualisation 3D
    
    o Choisir "Bar" ou "Line" dans l’option "Plot type"
    
    o Sélectionner le mode d’interaction désiré : 
    
      •	"pan view" (si l’utilisateur clique sur l’histogramme, alors il peut le déplacer dans la fenêtre)
		
      •	"select points" ou "free-hand select points" (si l’utilisateur veut pouvoir sélectionner des points avec la souris)
		
      •	"move points" (si l’utilisateur veut déplacer des points sur la courbe)

•	La box "Résultats" affiche les valeurs des bornes encadrant le pic du foie, sélectionnées par l’utilisateur

•	Si le résultat escompté n'est pas obtenu (id est, si le foie est sur ou sous-sélectionné), changer autant de fois que nécessaire les bornes grâce aux curseurs et cliquer, à chaque changement, sur "Exécuter l’histogramme et le seuillage"


**7. OPÉRATIONS DE MORPHOLOGIE MATHÉMATIQUE**

•	Choisir le volume d'entrée parmi la liste de ceux préalablement créés; le dernier volume obtenu à l'étape précédente correspond au dernier volume apparaissant dans le menu déroulant : **"Volume apres Seuillage_i"** pour i étant un nombre variant en fonction du nombre d'essais effectués à l'étape précédente. Choisir le dernier volume du menu déroulant puisque l’on désire travailler sur le dernier volume prétraité

•	Choisir la "Taille de l’élément structurant" à appliquer à l’opération suivante (plus l’élément structurant est grand, plus l’opération s’applique sur une zone étendue)

•	Commencer par choisir "Ouverture" afin de déconnecter les pixels d'intensités différentes

•	Cliquer sur "Exécuter l’opération de morphologie mathématique"

•	Si le résultat obtenu ne correspond pas à l'effet recherché, jouer avec les autres options mises à disposition, sachant qu'il faut principalement s'assurer de déconnecter et espacer correctement les structures pour pouvoir ne sélectionner que le foie à l'étape suivante.
L’explication des opérations de morphologie mathématique applicables est fournie en **Annexe 1**


**8. EXTRACTION DES COMPOSANTES CONNEXES**

•	Choisir, comme précédemment, le volume d'entrée dont le dernier créé – issu de l'étape précédente – est "Volume apres Morphologie Mathematique_i"

•	Cliquer sur "Configurer l’extraction du foie" : une pop-up "Extraction du foie" explique à l’utilisateur l’action à réaliser Cliquer sur "Ok" si toutes les informations sont comprises

•	Cliquer sur le foie dans une des images du rendu visuel de droite : un point rose avec l'annotation "Foie-1" apparaît alors à l'écran

•	Cliquer sur "Exécuter l’extraction"

•	La box "Résultats" affiche le nombre de labels définis dans l'image et le numéro du label du foie


**9. OPÉRATIONS DE MORPHOLOGIE MATHÉMATIQUE POUR AFFINER LA SEGMENTATION**

•	Choisir le volume d'entrée comme précédemment : "Volume apres Extraction_i" étant le dernier

•	Choisir la "Taille de l’élément structurant" à appliquer à l’opération suivante (plus l’élément structurant est grand, plus l’opération s’applique sur une zone étendue)

•	Commencer par réaliser une "Fermeture"

•	Cliquer sur "Exécuter la segmentation finale"

•	Si le résultat affiché n'est pas un foie correspondant au foie originel, visible en transparence lorsque l'utilisateur parcourt les différentes coupes, il faut affiner la segmentation :

    o Sélectionner à nouveau le dernier volume d’entrée du menu déroulant (celui qui vient de subir la fermeture) puis choisir une opération de morphologie mathématique à appliquer à ce volume (qui peut être suivie par un retour à l'étape précédente pour sélectionner à nouveau le foie) :
    
      •	"Ouverture" pour déconnecter des composantes connexes d'intensités différentes

      •	"Dilatation" pour augmenter le nombre de pixels considérés comme appartenant au foie = visuellement, on constate une expansion du volume

      •	"Érosion" pour diminuer le nombre de pixels considérés comme appartenant au foie = visuellement, on constate une diminution du volume

      •	"Fermeture" pour combler les trous entre des pixels voisins d'intensités similaires, pour fermer le volume défini

      •	"Remplissage des trous" pour combler des trous dans la segmentation

    o Attention à bien choisir, en entrée, le dernier volume traité, puis cliquer sur "Exécuter la segmentation finale" à chaque sélection d'option pour afficher le résultat et l'affiner

•	Si le résultat affiché est convenable mais contient encore des erreurs (foie sur ou sous-segmenté), il faut l’affiner plus précisément et donc manuellement. Pour cela, une pop-up "Segmentation du foie" s’affiche pour préconiser à l’utilisateur d’affiner sa segmentation.
Cliquer sur "Ok" si toutes les informations sont comprises

•	Cliquer sur "Correction de la segmentation du foie" : une pop-up "Segmentation du foie" apparaît alors pour indiquer à l’utilisateur la démarche à suivre.
Cliquer sur "Ok" si toutes les informations sont comprises

•	Une pop-up "Segment Editor" s’est affichée simultanément en arrière-plan; cette fenêtre permet à l’utilisateur de corriger manuellement la segmentation grâce à, principalement, deux fonctions : "Paint" et "Erase"

**ASTUCE :** Laisser la fenêtre "Segment Editor" à gauche de l’écran et adapter la fenêtre de 3D Slicer à droite pour pouvoir alterner facilement entre "Paint" et "Erase" sans multiplier les manipulations d’écran. Fermer également le module de 3D Slicer par la petite croix en haut à droite du module pour ne voir à l’écran que les coupes dans les différents plans 
(Pour revenir au visuel du module : "View"  "Module Panel")

•	Dans "Segment Editor" :

    o Pour l’option "Master volume", choisir la dernière option du menu déroulant "Labelmap du foie"

    o Cliquer sur "Paint" ou "Erase" pour, respectivement, ajouter ou supprimer des voxels au foie segmenté – apparaissant en bleu  –. Pour cela, l’utilisateur peint ou supprime par brossage sur les coupes visualisées, dans les différents plans (cliquer de manière prolongée sans relâcher la souris pour des corrections sur une zone étendue ou cliquer ponctuellement pour des corrections précises)
    
Il est possible de changer le diamètre de la sphère permettant ces ajouts et suppressions en cliquant sur les chiffres ou en tapant un chiffre dans le module :

**ASTUCE :** S’il y a beaucoup de modifications à effectuer (beaucoup de structures et d’organes n’appartenant pas au foie apparaissent dans la vue 3D), il est conseillé de positionner correctement la visualisation dans la vue 3D pour faire apparaître le surplus à effacer puis cocher "Edit in 3D views" (en-dessous de la modification du diamètre de la sphère sur l’image précédente); enfin, cliquer en glissant sur la vue 3D : cela crée des boules vert kaki qui deviennent blanches quand les segments désirés sont effacés. 

**Attention** à décocher "Edit in 3D views" pour modifier le positionnement de l’image dans la visualisation 3D

    o Une fois ces modifications effectuées avec succès, fermer la fenêtre "Segment Editor" en cliquant sur la croix en haut à droite de la fenêtre

•	Cliquer sur "Résultat de la segmentation" afin de convertir les modifications effectuées en un nouveau volume qui est parallèlement sauvegardé au format NIFTI dans le répertoire courant "TroisDSlicer" sous le nom "FoieSegmenteDonneur.nii"

•	L’ensemble de la scène est également sauvegardé dans le dossier nommé "FoieSegmenteDonneurData" dans le même répertoire


**10. CALCUL DE LA DISTANCE ENTRE DEUX POINTS SUR LE FOIE**

   - **10. 1. Distances automatiques**
	
      •	Cliquer sur "Calculer les distances automatiques" et attendre

      •	Les résultats des distances caractéristiques en mm (longueur, largeur, profondeur du foie) s'affichent alors dans la box "Résultats" de l'option

   - **10. 2. Distances manuelles**
	
      •	Cliquer sur "Configurer les distances manuelles" : la pop-up "Distances du foie" explique alors à l'utilisateur ce qui est attendu de lui pour calculer correctement les distances désirées.
Cliquer sur "Ok" si toutes les informations sont comprises 

      •	Le menu "Choisir une distance" demande d'abord à l'utilisateur de sélectionner les deux points en "Profondeur (coupe axiale)" : sur la coupe axiale, cliquer sur deux points correspondant à la profondeur du foie; les points s'affichent alors en rose

      •	Choisir une autre distance dans le menu déroulant :

        o Hauteur dans la coupe sagittale : cliquer sur deux points correspondant à la hauteur du foie; les points s’affichent alors en rouge
    
        o Longueur horizontale dans la coupe coronale : cliquer sur deux points correspondant à la longueur horizontale du foie; les points s’affichent alors en vert

      •	Si un point a été mal positionné sur une coupe, il suffit de désélectionner le marqueur fiducial dans la barre d’outils, en haut de l’écran, puis de cliquer sur le point mal positionné et de le déplacer à la position voulue

      •	Si l’utilisateur souhaite supprimer un point placé dans le mauvais plan ou la mauvaise coupe, il suffit de sélectionner dans le menu déroulant la distance dans laquelle se trouve ce point (Profondeur, Hauteur, Longueur) puis de cliquer sur la poubelle       (avant-dernier icône de la ligne "Choisir une distance"), autant de fois que nécessaire (dépend du nombre de points cliqués par distance sélectionnée) 

      •	Si deux points mal placés appartiennent à deux options différentes, il suffit de supprimer les points un par un en sélectionnant la bonne distance pour chacun

      •	Pour sélectionner un nouveau point après une suppression, il suffit de cliquer sur le marqueur fiducial (à gauche de la poubelle, dans le module, ou dans la barre d’outils, en haut de l’écran)

      •	Cliquer sur "Calculer les distances manuelles" (dès que les 6 points sont sélectionnés et correctement placés)

      •	Les résultats des distances en mm s'affichent dans la box "Résultats" de l'option


**11. CALCUL DU VOLUME DU FOIE**

•	Choisir le "Volume en niveaux de gris" à considérer pour calculer le volume : correspond au dernier volume obtenu, id est "FoieSegmentApresCorrection"

•	Choisir dans le menu déroulant "Carte des labels" : "Create new LabelMap Volume"

•	Choisir dans le menu déroulant le volume créé "LabelMapVolume"

•	Cliquer sur "Exécuter la Volumétrie de la Segmentation"

•	Les résultats s'affichent dans un tableau où 

        o le label 0 noir correspond à {toute l'image moins le foie segmenté}
    
        o le label 1 bleu correspond au {foie segmenté} (visible quand on glisse le menu déroulant vers le bas)
    
•	Il est possible d'exporter le tableau pour l'afficher à droite de l'écran en cliquant sur "Exporter en tableau"
	

**12. VALIDATION QUANTITATIVE DES RÉSULTATS DE LA SEGMENTATION**

•	Sur la ligne "Charger le foie référent : Vérité Terrain" : cliquer sur la barre de recherche de répertoire pour trouver l’image de référence à comparer à la segmentation réalisée semi-automatiquement puis cliquer sur "Importer et charger"

•	Choisir le "Volume en niveaux de gris" à considérer pour calculer le volume : correspond au dernier volume obtenu, id est "Volume Foie Reference"

•	Choisir dans le menu déroulant "Carte des labels" : "Create new LabelMap Volume"

•	Choisir dans le menu déroulant le volume créé "LabelMapVolume_1"

•	Cliquer sur "Exécuter la Volumétrie de la Segmentation de Référence"

•	Les résultats s’affichent comme précédemment :

        o le label 0 noir correspond à {toute l'image moins le foie segmenté}
    
        o le label 1 vert correspond au {foie segmenté}
    
        o le label 2 jaune correspond à {l’ensemble extérieur}
    
•	Il est possible d'exporter le tableau pour l'afficher à droite de l'écran en cliquant sur "Exporter en tableau"

•	Cliquer sur "Configurer la volumétrie"

•	Les résultats s’affichent dans la box "Résultats" de l’option; il s’agit des valeurs :

        o du coefficient de similarité DICE (plus la valeur est proche de 1, plus la segmentation est fiable par rapport à la segmentation de référence considérée parfaite)
    
        o du volumetric overlap VO
    
        o de l’erreur du volumetric overlap VOE en pourcentage (0 % correspond à une segmentation parfaite mais 100 % est obtenu si la segmentation et la vérité terrain ne correspondent pas du tout)
    
        o du volume du foie segmenté par le module en cm³
    
        o du volume du foie segmenté de référence en cm³
    
        o de la différence relative de volume RVD en pourcentage pour comparer l’erreur entre les volumes du foie segmenté par le module et celui considéré comme vérité terrain
 
 
 
 
# UTILISATION DE 3D SLICER POUR LA
 
## B)	SEGMENTATION DE LA CAVITÉ ABDOMINALE

**1. OUVRIR** le logiciel "3D Slicer"


**2.** Dans le menu déroulant "Welcome to Slicer", **CHOISIR LE MODULE CRÉÉ** appelé "Pour le RECEVEUR : Volumétrie et distances dans la cavité abdominale" puis cliquer sur "Analyse de la cavité abdominale"


**3. CHOISIR LA MÉTHODE D'IMPORTATION DES IMAGES**

   - **3.1. A partir d'un dossier de l'ordinateur contenant des fichiers DICOM :**
	
      •	Cliquer sur la barre de recherche de répertoire à côté de l’option "Charger depuis DICOM" puis cliquer sur "Importer et charger"
	
   - **3.2. A partir d'images préalablement (ou non) chargées sous 3D Slicer :**
	
     • **Si les images ont été préalablement chargées sous 3D Slicer**
		
      - Cliquer sur "Charger depuis SLICER" pour sélectionner cette option
		
      - Ignorer la pop-up "Charger les images" qui apparaît en cliquant sur "Cancel"

      - Choisir dans le menu déroulant le volume à charger parmi ceux disponibles

      - Cliquer sur "Importer et charger" au bout de la ligne de l'option sélectionnée "Charger depuis SLICER"

     • **Si Si les images n’ont pas été préalablement chargées sous 3D Slicer**

      - Cliquer sur "Charger depuis SLICER" pour sélectionner cette option

      - Une pop-up "Charger les images" apparaît pour donner à l'utilisateur les consignes à suivre :.
Cliquer sur "Ok" si toutes les informations sont comprises

      - Une autre pop-up appelée "DICOM" s'est affichée simultanément en arrière-plan de l'écran

      - Cliquer sur "Show DICOM Browser"

        o Soit choisir "Import" en haut à gauche puis suivre la démarche de recherche d'images DICOM dans les répertoires de l’ordinateur

        o Soit choisir parmi les volumes d'images déjà chargés dans 3D Slicer et qui s’affichent dans le premier tableau avec un classement par "PatientsName" :

         • Cliquer sur le volume désiré (par exemple : cd 11) puis sur la modalité d'imagerie à analyser, affichée dans le troisième tableau (par exemple : AP Artériel 3.0 l30f)
	
         • Cliquer sur "Load" en bas à gauche de la fenêtre
	
         • Fermer la petite fenêtre "DICOM" en cliquant sur la croix en haut à droite de la fenêtre

•	De retour sur notre module, charger les images dans le module courant en cliquant sur "Importer et charger" au bout de la ligne de l'option sélectionnée "Charger depuis SLICER"


**4. SÉLECTION DU VOLUME À ANALYSER**

•	Le volume préalablement chargé s’affiche dans "Volume d’entrée"

•	Choisir "Create new Model" dans "Surface de rognage"

•	Choisir "Create new MarkupsFiducial" dans "Surface de rognage par marqueurs"

•	Une pop-up "Ajouter des points" apparaît pour expliquer à l’utilisateur ce qu’il doit faire : cliquer pour entourer la zone dont le volume est recherché dans les différents plans anatomiques et sur plusieurs coupes (pour vérifier la bonne propagation en 3D).
Cliquer sur "Ok" si toutes les informations sont comprises

•	Cliquer d’abord tout autour du volume maximal pouvant contenir un foie dans le plan anatomique axial (les points peuvent être assez espacés, seule la forme générale est prise en compte) puis cliquer sur ce même volume imaginaire dans le plan sagittal puis affiner le volume créé dans le plan coronal

•	Si la forme du volume n’est pas totalement satisfaisante :

        o Décocher le marqueur fiducial et cliquer sur les marqueurs "A-i" pour les déplacer et arranger la forme du volume, et ce, dans les différents plans anatomiques (il est même possible de modifier considérablement la forme du volume en cliquant sur ces marqueurs dans la visualisation 3D et en déplaçant ces points)

        o S’il est nécessaire de supprimer un ou plusieurs marqueurs pour pouvoir réajuster le modèle par de nouveaux marqueurs :
		
         • Cliquer sur le menu déroulant "Modules" dans la barre d’outils puis sur "Data"
		
         • Trouver la ligne correspondant aux marqueurs "A-i" :  
		
         • Cliquer (droit) sur la ligne et sélectionner "Edit properties"
		
         • Si le numéro de marqueur erroné est connu, cliquer sur sa ligne et choisir "Delete highlighted fiducial(s)" puis sur "Delete"
		
•	Laisser cochée la case "Rognage extérieur"

•	Choisir "Create new Volume" dans "Volume de sortie" et cliquer sur le volume créé "Volume" s’il n’est pas déjà présélectionné

•	Cliquer sur "Exécuter" afin de convertir les modifications effectuées en un nouveau volume qui est parallèlement sauvegardé au format NIFTI dans le répertoire courant "TroisDSlicer" sous le nom "CaviteAbdoReceveur.nii"

•	L’ensemble de la scène est également sauvegardé dans le dossier nommé "CaviteAbdoReceveurData" dans le même répertoire


**5. CALCUL DU VOLUME DE LA CAVITÉ ABDOMINALE SÉLECTIONNÉE**

•	Choisir le "Volume en niveaux de gris" à considérer pour calculer le volume : correspond au dernier volume obtenu, id est "VolumeFoie"

•	Choisir dans le menu déroulant "Carte des labels" : "Create new LabelMap Volume"

•	Choisir dans le menu déroulant le volume créé "LabelMapVolume", s’il n’est pas déjà présélectionné

•	Cliquer sur "Exécuter la Volumétrie de la Cavité"

•	Les résultats s'affichent dans un tableau où 

        o le label 0 noir correspond à {toute l'image moins le foie segmenté} 
    
        o le label 1 bleu correspond au {foie segmenté} (visible quand on glisse le menu déroulant vers le bas)
    
•	Il est possible d'exporter le tableau pour l'afficher à droite de l'écran en cliquant sur "Exporter en tableau"


**6. CALCUL DE LA DISTANCE CORONALE**

•	Cliquer sur "Configurer" : la pop-up "Calcul de distances" s’affiche pour expliquer la démarche à suivre par l’utilisateur (ici, l’exemple porte sur la coupe coronale mais la démarche est identique pour les coupes axiale et sagittale)
Cliquer sur "Ok" si toutes les informations sont comprises

•	Cliquer alors sur deux points comme indiqué dans la pop-up précédente

•	Cliquer sur "Calculer la distance" une fois les deux points sélectionnés correctement

•	Les résultats des distances calculées en mm s’affichent dans la box "Résultats"

•	Si un point a été mal positionné sur une coupe, il suffit de désélectionner le marqueur fiducial dans la barre d’outils, en haut de l’écran, puis de cliquer sur le point mal positionné et de le déplacer à la position voulue

•	Si l’utilisateur souhaite supprimer un point placé dans le mauvais plan ou la mauvaise coupe, il suffit de cliquer sur la poubelle (avant-dernier icône de la ligne "Choisir une distance") autant de fois que nécessaire (dépend du nombre de points cliqués)

•	Pour sélectionner un nouveau point après une suppression, il suffit de cliquer sur le marqueur fiducial (à gauche de la poubelle, dans le module, ou dans la barre d’outils, en haut de l’écran)


**7. CALCUL DE LA DISTANCE SAGITTALE**

Même étapes que précédemment


**8. CALCUL DE LA DISTANCE AXIALE**

Même étapes que précédemment
 


# UTILISATION DE 3D SLICER POUR LA
 
## C)	SUPERPOSITION DU FOIE SEGMENTÉ DU DONNEUR ET DE LA CAVITÉ ABDOMINALE SEGMENTÉE DU RECEVEUR

**1. OUVRIR** le logiciel "3D Slicer"


**2.** Dans le menu déroulant "Welcome to Slicer", **CHOISIR LE MODULE CRÉÉ** appelé "SUPERPOSITION donneur / receveur" puis cliquer sur "Superposition de la cavité abdominale avec le foie segmenté"


**3. IMPORTER LES IMAGES**

•	Cliquer sur "Charger la CAVITÉ"

•	Une fenêtre "Open" apparaît pour que l’utilisateur recherche le fichier correspondant à la segmentation de la cavité abdominale au format NIFTI (enregistrement effectué automatiquement après l’utilisation correcte du module "Pour le RECEVEUR : Volumétrie et distances dans la cavité abdominale")

        o Rechercher le fichier "CaviteAbdoReceveur.nii"
	
        o Cliquer sur le fichier
	
        o Cliquer sur "Open" en bas à droite de la fenêtre
	
        o Patienter le temps que le volume se charge dans la fenêtre de visualisation

•	Cliquer sur "Charger le FOIE SEGMENTÉ"

•	Une fenêtre "Open" apparaît pour que l’utilisateur recherche le fichier correspondant à la segmentation du foie au format NIFTI (enregistrement effectué automatiquement après l’utilisation correcte du module "Pour le DONNEUR : Segmentation semi-automatique du foie")

        o Rechercher le fichier "FoieSegmenteDonneur.nii"
    
        o Cliquer sur le fichier
	
        o Cliquer sur "Open" en bas à droite de la fenêtre
	
        o Patienter le temps que le volume se charge dans la fenêtre de visualisation


**4. SUPERPOSER LES IMAGES CHARGÉES**

•	Cliquer sur "Exécuter" : une pop-up "General Registration (Elastix)" apparaît ; cette fenêtre
va permettre d’effectuer un recalage rigide 3D entre les segmentations du foie et de la
cavité abdominale

•	Dans "General Registration (Elastix)" :

        o Pour l’option "Fixed volume", choisir le volume de la cavité abdominale segmentée qui vient d’être chargé

        o Pour l’option "Moving volume", choisir le volume du foie segmenté qui vient d’être chargé

        o Pour l’option "Preset", choisir "generic rigid (all)"
	
        o Choisir "Create new Volume" dans l’option "Output volume" et cliquer sur le volume créé "Volume" s’il n’est pas déjà présélectionné

        o Cliquer sur "Apply" puis attendre la fin du recalage
	
        o Dès qu’apparaît "Registration is completed", dans la box sous "Apply", fermer la fenêtre "General Registration (Elastix)" en cliquant sur la croix en haut à droite de la fenêtre

•	Choisir le "Volume d’entrée de la cavité" correspondant au volume préalablement chargé de la cavité abdominale segmentée au format NIFTI

•	Choisir le "Volume du foie segmenté après recalage" correspondant au volume créé après
application de la fonction de recalage 3D : "Volume_i" (la valeur de i apparaît si l’opération
de recalage est effectuée plusieurs fois)

•	Cliquer sur "Superposer les segmentations" : l’utilisateur peut visualiser les deux volumes
superposés, en transparence, coupe par coupe, et dans n’importe quel plan anatomique



# UTILISATION DE 3D SLICER POUR LA
 
## D)	SAUVEGARDE ET RÉINITIALISATION

Une fois la segmentation terminée et satisfaisante, il est possible de SAUVEGARDER SON TRAVAIL indépendamment de ce que les modules créés permettent déjà de sauvegarder automatiquement au cours de leur utilisation

•	Cliquer sur l'icône "Save" dans la barre d’outils, en haut à gauche de l'écran

•	Cocher les nœuds / scènes / volumes voulant être sauvegardés et décocher ceux non désirés

•	Choisir leur format d'exportation dans "File format" (colonne du milieu)

•	Choisir le répertoire de destination de la sauvegarde :

        o dans "Directory" (colonne de droite) pour chaque élément sauvegarder
    
        o dans "Change directory for selected files" en bas de la fenêtre pour changer le répertoire pour tous les fichiers sauvegardés
    
•	Cliquer sur "Save"


**POUR RÉINITIALISER L'INTERFACE DU MODULE**

•	Cliquer sur "Reload and Test" en haut de la fenêtre du module


 
## ANNEXE : DESCRIPTION DES DIFFÉRENTES OPÉRATIONS DE MORPHOLOGIE MATHÉMATIQUE

•	**Ouverture :**

        o Déconnecte des composantes connexes d'intensités différentes

        o Préserve la forme des objets

        o Ôte des détails ou des petits objets

        o Peut diviser les objets

        o Ne préserve pas la connexité

•	**Fermeture :**

        o Remplit des petites cavités

        o Connecte les composants connectés proches, comble les trous entre des pixels voisins d’intensités similaires

        o Ne préserve pas la continuité

•	**Dilatation :**

        o Correspond à une "addition"

        o Augmente la taille des objets = expansion du volume

        o Peut boucher les trous et les concavités

        o Peut connecter les objets voisins 

        o Fait disparaître des petits détails

•	**Érosion :**

        o Correspond à une "soustraction"

        o Fait décroître la taille des objets = diminution du volume

        o Peut diviser un objet avec des concavités ou des trous en plusieurs objets

        o Fait disparaître les petits objets et les détails

•	**Remplissage des trous :**

        o Remplit les trous dans les objets













