"""
/***************************************************************************
 Ricava da un Geoid Model (raster) il valore di ondulazione calcolato con interpolazione bilineare in un punto lon,lat
                              -------------------
        copyright            : (C) 2022 by Mauro Bettella
        email                : bettellam@gmail.com
 ***************************************************************************/
"""
#-------------------------------------------------------------

import math

@qgsfunction(args='auto', group='Rasters',usesgeometry=True)
def rBilinear_Value(rlayer_name, feature, parent):
    #Returns Bilinear value to Geodetic Model.
    """
    <h1>Ricava da un Geoid Model (raster) il valore di ondulazione calcolato con interpolazione bilineare in un punto lon,lat</h1><br>    
    La funzione, si applica ad un campo calcolato e restituisce il valore di ondulazione del Geid Model caricato nel progetto QGis.
    <hr>Personalizzare lo script indicando il nome del campo che contiene il valore di <b>altezza h Ellissoidica/GNSS. <br>[Z nel mio esempio].</b>
    <hr>Se il campo altezza Ellissoidica Esite, il valore restituito corrisponde alla <b>Quota Ortometrica/Geoidica</B>.
    <hr>Se il campo altezza Ellissoidica NON Esite, il valore restituito corrisponde al valore di ondulazione del Geoid Model caricato (a).<hr>
    
    <h2>Esempio:</h2>
    <ul>
      <li>rBilinear_Value( 'ITALGEO2005_GK2_ETRS89.tif') </li>
      <li>rBilinear_Value( 'EGM2008_47_44_10_14.tif')</li>
    </ul>
    <h2>NB: il file raster deve essere caricato nel progetto QGis.</h2>
    """
    rlayer = QgsProject.instance().mapLayersByName(rlayer_name)[0]
    
    extent =rlayer.extent()
    xmin = extent.xMinimum()
    #xmax = extent.xMaximum()
    ymin = extent.yMinimum()
    #ymax = extent.yMaximum()
    
    pixelSizeX = rlayer.rasterUnitsPerPixelX()
    pixelSizeY = rlayer.rasterUnitsPerPixelY()
    
    #cols = rlayer.width()
    #rows = rlayer.height()
    #bands = rlayer.bandCount()
    

    geom = feature.geometry()
    point=geom.asPoint()
    x=point.x()
    y=point.y()
    
    #bilinear=False
    bilinear=True
    if bilinear==True:
        xL=pixelSizeX/2
        yL=pixelSizeY/2
    
        rX1 = x-xL
        rY1 = y-yL
        rX2 = x-xL
        rY2 = y+yL
        rX3 = x+xL
        rY3 = y-yL
        rX4 = x+xL
        rY4 = y+yL
        #
        #   2.-----------.4
        #   |            |
        #   |            |
        #   |            |
        #   1.-----------.3
        #
        value1, res = rlayer.dataProvider().sample(QgsPointXY(rX1,rY1), 1)
        value2, res = rlayer.dataProvider().sample(QgsPointXY(rX2,rY2), 1)
        value3, res = rlayer.dataProvider().sample(QgsPointXY(rX3,rY3), 1)
        value4, res = rlayer.dataProvider().sample(QgsPointXY(rX4,rY4), 1)
        dX, intX = math.modf ((x-xmin)/pixelSizeX)
        dY, intY = math.modf ((y-ymin)/pixelSizeY)
        if dX<0.5:
            dX=0.5+dX
        else:
            dX=dX-0.5
        if dY<0.5:
            dY=0.5+dY
        else:
            dY=dY-0.5
    
        Value = value1*(1-dX)*(1-dY) + value3*dX*(1-dY) +  value2*(1-dX)*dY + value4*dX*dY
       
    
        # Calcola GeoidValue H Geoidica/Ortometrica
        # Indicare il nome del campo che contiene: h Ellissoidica / GNSS
        idx = feature.fieldNameIndex('z')
        if idx!=-1:
            EllissValue=feature.attributes()[idx]
            GeoidValue=EllissValue-Value
            return round(GeoidValue,3)
        else:
            return round(Value,3)
    else:
        value, res = rlayer.dataProvider().sample(QgsPointXY(x,y), 1)
        return round(Value,3)