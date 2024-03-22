#---------------------------------------------------------------------------------------
# leggi_GK2_v4.py
# Marzo 2024 - Mauro Bettella
# bettellam@gmail.com
#---------------------------------------------------------------------------------------
# Estrae dai file IGMI GK2 il modello di ondulazione del Geoide
# per eseguire la trasformazione di altezze Ellissoidiche GNSS
# in quote ortometriche geoidiche
# Estrazione da GK2 FOGLIO e GK2 PUNTO
#---------------------------------------------------------------------------------------
# Informazioni tecniche:
# Utility "Geoid Converter" - 
# https://www.eye4software.com/hydromagic/documentation/manual/utilities/geoid-file-conversion/
#
# Trimble Grid Factory – Geoid GGF format
# https://www.trimble.com/globalTRLTAB.aspx?Nav=Collection-37882
#
# MATTM - Geoportale Nazionale – Specifiche tecniche del servizio di trasformazione di coordinate 
# http://www.pcn.minambiente.it/mattm/wp-content/uploads/2016/12/MATTM-MU_SRC_PSCC_SPEC_TECNICHE-001-1_v01.pdf
#
# IGMI - 
# https://www.igmi.org/++theme++igm/pdf/nuova_nota_EPSG.pdf
#
# Ronci Ernesto - Dallo statico al Network RTK: l'evoluzione del rilievo satellitare. 
# http://amsdottorato.unibo.it/307/1/Ronci_PhD.pdf
#
# Virgilio Cima  - TRASFORMAZIONI DI COORDINATE – Il software ConveRgo 
# https://www.cisis.it/?page_id=3214
# https://www.youtube.com/watch?v=hzBF6DO2PJ4&t=5472s
#---------------------------------------------------------------------------------------

from osgeo import gdal, ogr, osr
from osgeo.gdalconst import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import os
import sys
import fileinput
import webbrowser

class MyDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle("Leggi GK2 ITALGEO2005 Model...")
        
        self.bar = QgsMessageBar()
        #self.bar.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed )

        # Create the label 
        self.lblPATH=QLabel('Cartella Grigliati GK2:') 
        self.lblPATH.setFont(QFont('Arial',10) )
        self.lePATH = QLineEdit()
        self.lePATH.setFont(QFont('Arial',10) )
        #self.lePATH.setText(MyRoot)
        self.lePATH.editingFinished.connect(self.EditPATH)
        
        self.PB_PATH = QPushButton ("...")
        self.PB_PATH.setFont(QFont('Arial',10) )
        self.PB_PATH.clicked.connect(self.StorePATH)
        self.PB_PATH.setToolTip("Seleziona Cartella... ")
        
        # Create the label 
        self.lblEPSG=QLabel('EPSG Output:') 
        self.lblEPSG.setFont(QFont('Arial',10) )
        self.cbEPSG = QComboBox()
        self.cbEPSG.addItem('4258 - ETRS89')#0
        self.cbEPSG.addItem('4326 - WGS84')#1
        self.cbEPSG.setCurrentIndex(0)
        #self.cbEPSG.setCurrentIndex(1)
        
        self.cbEPSG.setFont(QFont('Arial',10) )
        self.cbEPSG.currentIndexChanged.connect(self.StoreEPSG)
        
        # Create the label 
        self.lblMF=QLabel('Merge File:') 
        self.lblMF.setFont(QFont('Arial',10) )
        self.cbMF = QComboBox()
        self.cbMF.addItem('SI')#0
        self.cbMF.addItem('NO')#1
        self.cbMF.setCurrentIndex(0)
        #self.cbMF.setCurrentIndex(1)
        
        self.cbMF.setFont(QFont('Arial',10) )
        self.cbMF.currentIndexChanged.connect(self.StoreMF)

        # Create the label 
        self.lblME=QLabel('Nome File Merge :') 
        self.lblME.setFont(QFont('Arial',10) )
        self.leME = QLineEdit()
        self.leME.setFont(QFont('Arial',10) )
        self.leME.setText('ITALGEO2005_GK2_ETRS89')
        self.leME.editingFinished.connect(self.EditME)

        # Create the label 
        self.lblCO=QLabel('Contour step (>=0.10):') 
        self.lblCO.setFont(QFont('Arial',10) )
        self.leCO = QLineEdit()
        self.leCO.setFont(QFont('Arial',10) )
        self.leCO.setText('0.10')
        self.leCO.editingFinished.connect(self.EditCO)
        
        self.pulsante = QPushButton ("Crea Geoid Model GTX...")
        self.pulsante.clicked.connect(self.run)
        self.pulsante.setFont(QFont('Arial',10) )
        self.pulsante.setToolTip("Avvia Lettura File GK2 - Crea Geoid Model GTX... ")
        self.pulsante.setEnabled(False)

        self.help = QPushButton ("Info...")
        self.help.clicked.connect(self.runhelp)
        self.help.setFont(QFont('Arial',10) )
        
        self.setLayout(QGridLayout())
        self.resize(650,200)
       
        
        self.layout().addWidget(self.lblPATH, 0, 0)
        self.layout().addWidget(self.lePATH, 0, 1)
        self.layout().addWidget(self.PB_PATH, 0, 2)
        
        self.layout().addWidget(self.lblEPSG, 1, 0)
        self.layout().addWidget(self.cbEPSG, 1, 1)
        
        self.layout().addWidget(self.lblMF, 2, 0)
        self.layout().addWidget(self.cbMF, 2, 1)
        
        self.layout().addWidget(self.lblME, 3, 0)
        self.layout().addWidget(self.leME, 3, 1)
        
        self.layout().addWidget(self.lblCO, 4, 0)
        self.layout().addWidget(self.leCO, 4, 1)
        
        self.layout().addWidget(self.pulsante, 5, 1)
        self.layout().addWidget(self.help, 5, 2)
        self.layout().addWidget(self.bar, 6, 1)
        
    def EditPATH(self):
        if self.lePATH.isModified():
            # do interesting stuff ...
            #print ('Editing Finished')
            countGK2=0
            if  not (os.path.exists(self.lePATH.text())):
                self.bar.pushMessage("","PATH LOCALE NON ESISTE!!!", level=Qgis.Critical)
                #print(self.lePATH.text())
                self.pulsante.setEnabled(False)

            else:
                rootPath=(self.lePATH.text())
                space=rootPath.find(' ')
                if space==-1:
                    rootPath=rootPath.replace(chr(92),chr(47))
                    for root, dirs, files in os.walk(rootPath):
                        for filename in files:
                            if filename[-4:] == '.GK2':
                                countGK2=countGK2+1
                
                    #print (MyRoot)
                    #self.lePATH.setText(MyRoot)
                    if countGK2!=0:
                        self.pulsante.setEnabled(True)
                        self.bar.pushMessage("Nr GK2 ", str(countGK2), level=Qgis.Info)
                    else:
                        self.pulsante.setEnabled(False)
                        self.bar.pushMessage("ATTENZIONE","NO GK2 !!!", level=Qgis.Critical)
                else:
                    self.bar.pushMessage("","PATH NON VALIDO (spazi)!!!", level=Qgis.Critical)
                    #print(self.lePATH.text())
                    self.pulsante.setEnabled(False)
                    
            self.lePATH.setToolTip("Nr GK2 :  "+ str(countGK2))
        self.lePATH.setModified(False)

    def StorePATH(self):
        qfd = QFileDialog()
        path = self.lePATH.text()
        title="Seleziona Cartella Grigliati GK2..."
        rootPath = QFileDialog.getExistingDirectory(qfd, title, path)
        #print(os.path.dirname(os.path.realpath(filePath)))
        #print(MyRoot)
        countGK2=0
        if rootPath == "" :
            self.pulsante.setEnabled(False)
            return
        
        space=rootPath.find(' ')
        if space==-1:
            for root, dirs, files in os.walk(rootPath):
                for filename in files:
                    if filename[-4:] == '.GK2':
                        countGK2=countGK2+1
            if countGK2!=0:
                self.pulsante.setEnabled(True)
                self.bar.pushMessage("Nr GK2 ", str(countGK2), level=Qgis.Info)
                self.lePATH.setText(rootPath)
            else:
                self.pulsante.setEnabled(False)
                self.bar.pushMessage("ATTENZIONE","NO GK2 !!!", level=Qgis.Critical)
                #self.lePATH.setText('')
        else:
            self.bar.pushMessage("","PATH NON VALIDO (spazi)!!!", level=Qgis.Critical)
            #print(self.lePATH.text())
            self.pulsante.setEnabled(False)

        self.lePATH.setToolTip("Nr GK2 :  "+ str(countGK2))
        #self.bar.pushMessage("OK", "Variabile Aggiornata !", level=Qgis.Info)
           
    def StoreEPSG(self):
        #mergefile=self.cbRT.currentText()
        if self.cbEPSG.currentText()=='4258 - ETRS89':
            ME=self.leME.text().replace('_WGS84','_ETRS89')
            self.leME.setText(ME)
        else:
            ME=self.leME.text().replace('_ETRS89','_WGS84')
            self.leME.setText(ME)
           
        #self.bar.pushMessage("OK", "Variabile Aggiornata !", level=Qgis.Info)
           
    def StoreMF(self):
        #mergefile=self.cbRT.currentText()
        if self.cbMF.currentText()=='SI':
            self.lblME.setEnabled(True)
            self.leME.setEnabled(True)
        else:
            self.lblME.setEnabled(False)
            self.leME.setEnabled(False)
           
        #self.bar.pushMessage("OK", "Variabile Aggiornata !", level=Qgis.Info)

    def EditME(self):
        if self.leME.isModified():
            # do interesting stuff ...
            #print ('Editing Finished')
            #ME=self.leME.text()
            ME=self.leME.text().replace(' ','_')
            self.leME.setText(ME)
            #self.bar.pushMessage("OK", "Variabile Aggiornata !", level=Qgis.Info)
        self.leME.setModified(False)
        
    def EditCO(self):
        if self.leCO.isModified():
            # do interesting stuff ...
            #print ('Editing Finished')
            #ME=self.leME.text()
            try:
                CO=float(self.leCO.text())
            except:
                CO=0
            if CO<0.10:
                self.leCO.setText('0.10')
                self.pulsante.setEnabled(False)
                self.bar.pushMessage("","Inserire valore numerico!!!", level=Qgis.Critical)
           #self.bar.pushMessage("OK", "Variabile Aggiornata !", level=Qgis.Info)
        self.leCO.setModified(False)

    def runhelp(self):
        webbrowser.open('https://www.mabegis.it/gis/VDatum_GTX/ITALGEO2005_da_GK2_a_GTX_v3.pdf')
        
    def run(self):

        #Attenzione ai permessi di scrittura su disco C
        #rootPath = 'D:/Grigliati/'
        rootPath = self.lePATH.text()+'/'
        patternType = '.GK2'
        
        #contour_step=0.10
        contour_step=float(self.leCO.text())

        sFind = chr(34)+'2005'+chr(34)
        sGK2 = chr(34)+'FOGLIO'+chr(34)
        passo=2/60
        buff=passo/2
        pixelsize=passo
        dec=9
        #dec=13 
        x1m=9999
        y1m=9999
        x2m=-9999
        y2m=-9999
        countGK2=0

        mergefile=self.cbMF.currentText()
        #mergefile='NO'
        #mergefile='SI'

        # create the spatial reference, GCS_ETRS_1989
        srs = osr.SpatialReference()
        #srs.ImportFromEPSG(4258)
        if self.cbEPSG.currentText()=='4258 - ETRS89':
            srs.ImportFromEPSG(4258)
            strEPSG='_ETRS89'
        else:
            srs.ImportFromEPSG(4326)
            strEPSG='_WGS84'

        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")

        if mergefile=='SI':
            basename=self.leME.text()
            #basename='ITALGEO2005_GK2_ETRS89'
            fileshp=rootPath+basename+'.shp'
            filebound=rootPath+basename+'_bound.shp'
            dissolveshp=rootPath+basename+'_bound_dissolve.shp'
            # create the data source Point
            if os.path.exists(fileshp):
                driver.DeleteDataSource(fileshp)
            data_source_pt = driver.CreateDataSource(fileshp)

            # create the data source Polygon
            if os.path.exists(filebound):
                driver.DeleteDataSource(filebound)
            data_source_pg = driver.CreateDataSource(filebound)
            # create the layer
            #PointZ
            layer_PT = data_source_pt.CreateLayer(basename, srs, ogr.wkbPoint25D)
            #Point
            #layer_PT = data_source_pt.CreateLayer(basename, srs, ogr.wkbPoint)
            #Polygon
            layer_PG = data_source_pt.CreateLayer(basename+'_bound', srs, ogr.wkbPolygon)

            # Add the fields we're interested in
            layer_PT.CreateField(ogr.FieldDefn("LAT", ogr.OFTReal))
            layer_PT.CreateField(ogr.FieldDefn("LON", ogr.OFTReal))
            layer_PT.CreateField(ogr.FieldDefn("ZDELTA", ogr.OFTReal))
            layer_PT.CreateField(ogr.FieldDefn("invZDELTA", ogr.OFTReal))
            field_name = ogr.FieldDefn("FILE", ogr.OFTString)
            field_name.SetWidth(6)
            layer_PT.CreateField(field_name)

            # Add the fields we're interested in
            layer_PG.CreateField(field_name)

        for root, dirs, files in os.walk(rootPath):
            for filename in files:
                if filename[-4:] == patternType:
                    countGK2=countGK2+1
                    if mergefile=='NO':
                        basename=filename.replace(patternType,'')+strEPSG
                        print(basename)
                        fileshp=rootPath+basename+'.shp'
                        filebound=rootPath+basename+'_bound.shp'
                        # create the data source Point
                        if os.path.exists(fileshp):
                            driver.DeleteDataSource(fileshp)
                        data_source_pt = driver.CreateDataSource(fileshp)

                        # create the data source Polygon
                        if os.path.exists(filebound):
                            driver.DeleteDataSource(filebound)
                        data_source_pg = driver.CreateDataSource(filebound)
                        # create the layer
                        #PointZ
                        layer_PT = data_source_pt.CreateLayer(basename, srs, ogr.wkbPoint25D)
                        #Point
                        #layer_PT = data_source_pt.CreateLayer(basename, srs, ogr.wkbPoint)
                        #Polygon
                        layer_PG = data_source_pt.CreateLayer(basename+'_bound', srs, ogr.wkbPolygon)

                        # Add the fields we're interested in
                        layer_PT.CreateField(ogr.FieldDefn("LAT", ogr.OFTReal))
                        layer_PT.CreateField(ogr.FieldDefn("LON", ogr.OFTReal))
                        layer_PT.CreateField(ogr.FieldDefn("ZDELTA", ogr.OFTReal))
                        layer_PT.CreateField(ogr.FieldDefn("invZDELTA", ogr.OFTReal))
                        field_name = ogr.FieldDefn("FILE", ogr.OFTString)
                        field_name.SetWidth(6)
                        layer_PT.CreateField(field_name)

                        # Add the fields we're interested in
                        layer_PG.CreateField(field_name)

                    inFeature = ( os.path.join(root, filename))
                    lines = []
                    print(inFeature)
                    with open(inFeature,'r', encoding='utf8') as file:
                        lines = file.readlines()

                    
                    if lines[0].rstrip()==sGK2:
                         nr_righe=10
                         nr_colonne=14
                    else:
                         nr_righe=8
                         nr_colonne=10
                         
                    count=-1
                    for line in lines:
                        #print(line.rstrip())
                        count=count+1
                        if line.rstrip()==sFind:
                            #print(line)
                            rowdata=count
                            for riga in range(nr_righe):
                                for col in range(nr_colonne):
                                    count=count+1
                                    sValue=lines[count].rstrip()
                                    #print(sValue)

                            count=count+1
                            Latitudine=float(lines[count].rstrip())
                            #print(Latitudine)
                            count=count+1
                            Longitudine=float(lines[count].rstrip())
                            #print(Longitudine)

                    count= rowdata       
                    lat_start = Latitudine + passo * (nr_righe - 1)
                    for riga in range(nr_righe):
                        lat = lat_start - passo * riga
                        for col in range(nr_colonne):
                            lon = Longitudine + passo * col
                            count=count+1
                            y=round(float(lat),dec)
                            x=round(float(lon),dec)
                            zdelta=float(lines[count].rstrip())
                            #PointZ
                            WKT='POINT('+str(x)+' '+str(y)+' '+str(zdelta)+')'
                            #Point
                            #WKT='POINT('+str(x)+' '+str(y)+')'

                            #shp
                            # create the feature
                            feature_PT = ogr.Feature(layer_PT.GetLayerDefn())
                            # Set the attributes using the values
                            feature_PT.SetField("LAT", y)
                            feature_PT.SetField("LON", x)
                            feature_PT.SetField("ZDELTA", zdelta)
                            feature_PT.SetField("invZDELTA", zdelta*(-1))
                            feature_PT.SetField("FILE", filename)

                            # Create the geometry 
                            new_geom = ogr.CreateGeometryFromWkt(WKT)

                            # Set the feature geometry using the point
                            feature_PT.SetGeometry(new_geom)
                            # Create the feature in the layer (shapefile)
                            layer_PT.CreateFeature(feature_PT)
                            # Dereference the feature
                            feature_PT = None

                    #boundary
                    x1=round((Longitudine-buff),dec)
                    y1=round((Latitudine-buff),dec)
                    x2=round((Longitudine + passo * (nr_colonne - 1)+buff),dec)
                    y2=round((lat_start+buff),dec)
                    WKT='POLYGON(('+str(x1)+' '+str(y1)+','+str(x2)+' '+str(y1)+','+str(x2)+' '+str(y2)+','+str(x1)+' '+str(y2)+','+str(x1)+' '+str(y1)+'))'
                    #shp
                    # create the feature
                    feature_PG = ogr.Feature(layer_PG.GetLayerDefn())
                    # Set the attributes using the values
                    feature_PG.SetField("FILE", filename)

                    # Create the geometry
                    new_geom = ogr.CreateGeometryFromWkt(WKT)

                    # Set the feature geometry
                    feature_PG.SetGeometry(new_geom)
                    # Create the feature in the layer (shapefile)
                    layer_PG.CreateFeature(feature_PG)
                    # Dereference the feature
                    feature_PG = None

                    if mergefile=='SI':
                        #update extend
                        if x1<x1m:
                            x1m=x1
                        if y1<y1m:
                            y1m=y1
                        if x2>x2m:
                            x2m=x2
                        if y2>y2m:
                            y2m=y2
                    else:
                        # Save and close the data source
                        data_source_pt = None
                        data_source_pg = None
                        #create TIF
                        filetiff=rootPath+basename+'.tif'
                        Cmd='gdal_rasterize -l '+basename+' -a ZDELTA -tr '+str(pixelsize)+' '+str(pixelsize)+' -a_nodata -9999.0 -te '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2)+' -ot Float32 -of GTiff '+fileshp+' '+filetiff
                        #print(Cmd)
                        risp=os.system(Cmd)

                        #create GTX ---> SW Maps QFIELD
                        filegtx=rootPath+basename+'.gtx'
                        Cmd='gdal_rasterize -l '+basename+' -a ZDELTA -tr '+str(pixelsize)+' '+str(pixelsize)+' -a_nodata 0 -te '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2)+' -ot Float32 -of GTX '+fileshp+' '+filegtx
                        #print(Cmd)
                        risp=os.system(Cmd)

                        #create XYZ CSV  ---> estrazione valori per generazione GGF Trimble
                        filecsv=rootPath+basename+'_xyz.csv'
                        Cmd='gdal2xyz -band 1 -csv '+filegtx + ' '+ filecsv
                        #print(Cmd)
                        risp=os.system(Cmd)

                        #create da GEOIDICHE--->ELLISSOIDICHE
                        filegtx=rootPath+basename+'_INV.gtx'
                        Cmd='gdal_rasterize -l '+basename+' -a invZDELTA -tr '+str(pixelsize)+' '+str(pixelsize)+' -a_nodata 0 -te '+str(x1)+' '+str(y1)+' '+str(x2)+' '+str(y2)+' -ot Float32 -of GTX '+fileshp+' '+filegtx
                        #print(Cmd)
                        risp=os.system(Cmd)

                        # Create contour
                        filecontour=rootPath+basename+'_contour.shp'
                        Cmd='gdal_contour -b 1 -a ELEV -i '+ str(contour_step) +' -f '+chr(34)+'ESRI Shapefile'+chr(34)+' '+filetiff+' '+ filecontour
                        #print(Cmd)
                        risp=os.system(Cmd)

        if mergefile=='SI':
            # Save and close the data source
            data_source_pt = None
            data_source_pg = None

            #dissolve Polygon boundary
            if countGK2>1:
                Cmd='ogr2ogr -f '+chr(34)+'ESRI Shapefile'+chr(34)+' -overwrite '+dissolveshp+' '+filebound+' -nlt PROMOTE_TO_MULTI -dialect sqlite -sql '+chr(34)+'SELECT ST_Union(geometry) AS geometry FROM '+chr(34)+basename+'_bound'+chr(34)
                #print(Cmd)
                risp=os.system(Cmd)

            #create TIF
            filetiff=rootPath+basename+'.tif'
            Cmd='gdal_rasterize -l '+basename+' -a ZDELTA -tr '+str(pixelsize)+' '+str(pixelsize)+' -a_nodata -9999.0 -te '+str(x1m)+' '+str(y1m)+' '+str(x2m)+' '+str(y2m)+' -ot Float32 -of GTiff '+fileshp+' '+filetiff
            #print(Cmd)
            risp=os.system(Cmd)

            #create GTX ---> SW Maps QFIELD
            filegtx=rootPath+basename+'.gtx'
            Cmd='gdal_rasterize -l '+basename+' -a ZDELTA -tr '+str(pixelsize)+' '+str(pixelsize)+' -a_nodata 0 -te '+str(x1m)+' '+str(y1m)+' '+str(x2m)+' '+str(y2m)+' -ot Float32 -of GTX '+fileshp+' '+filegtx
            #print(Cmd)
            risp=os.system(Cmd)

            #create XYZ CSV  ---> estrazione valori per generazione GGF Trimble
            filecsv=rootPath+basename+'_xyz.csv'
            Cmd='gdal2xyz -band 1 -csv '+filegtx + ' '+ filecsv
            #print(Cmd)
            risp=os.system(Cmd)

            #create da GEOIDICHE--->ELLISSOIDICHE
            filegtx=rootPath+basename+'_INV.gtx'
            Cmd='gdal_rasterize -l '+basename+' -a invZDELTA -tr '+str(pixelsize)+' '+str(pixelsize)+' -a_nodata 0 -te '+str(x1m)+' '+str(y1m)+' '+str(x2m)+' '+str(y2m)+' -ot Float32 -of GTX '+fileshp+' '+filegtx
            #print(Cmd)
            risp=os.system(Cmd)

            # Create contour
            filecontour=rootPath+basename+'_contour.shp'
            Cmd='gdal_contour -b 1 -a ELEV -i '+ str(contour_step) +' -f '+chr(34)+'ESRI Shapefile'+chr(34)+' '+filetiff+' '+ filecontour
            #print(Cmd)
            risp=os.system(Cmd)
        self.bar.pushMessage("OK", "Lettura Completata !!!", level=Qgis.Info)
        print ("Completato !!!!!!!!!")
myDlg=MyDialog()
myDlg.show()
