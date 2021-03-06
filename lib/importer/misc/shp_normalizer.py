from chardet.universaldetector import UniversalDetector
import os.path
import sys
import dbfUtils
import sys
from osgeo import osr
from urllib import urlencode
from urllib2 import urlopen
import json
import subprocess

shp_file = sys.argv[1]
name = sys.argv[2]

dbf_file = shp_file[0:-4] + '.dbf'
prj_file = shp_file[0:-4] + '.prj'

srid = 4326

def get_spatial_reference(shapefile):
    srs = osr.SpatialReference()
    shape_name = os.path.splitext(shapefile)[0]
    shpfile = os.path.basename(shape_name)
    prj_string = open(shape_name +'.prj','r').read()
    ret = srs.SetFromUserInput(prj_string)
    proj4 = srs.ExportToProj4()
    if not proj4:
        prj_file = open(shape_name +'.prj','r')
        prj_lines = prj_file.readlines()
        prj_file.close()
        for i in range(len(prj_lines)):
            prj_lines[i] = prj_string.rstrip( prj_lines[i] )
        srs = osr.SpatialReference()
        srs.ImportFromESRI(prj_lines)
        proj4 = srs.ExportToProj4()
        """
        if not proj4:
            #print 'Failed to convert prj of %s, giving up...' % shpfile
        else:
            #print 'Second try assuming ESRI wkt worked for %s!' % shpfile           
        """
        srs.from_esri = True
    else:
        srs.from_esri = False
    srs.AutoIdentifyEPSG()
    return srs

def to_epsg(srs):
    if srs.IsGeographic():
        return srs.GetAuthorityCode('GEOGCS')
    else:
        c = srs.GetAuthorityCode('PROJCS')
        if c:
            return c
        else:
            try:
                return srs.GetAuthorityCode('GEOGCS')
            except:
                return c


#Try detecting the SRID
if os.path.isfile(prj_file):
  code = to_epsg(get_spatial_reference(shp_file))
  if code:
    srid = code
  else:
    #Ok, no luck, lets try with the OpenGeo service
    try:
      query = urlencode({
          'exact' : True,
          'error' : True,
          'mode' : 'wkt',
          'terms' : prj_txt})
      webres = urlopen('http://prj2epsg.org/search.json', query)
      jres = json.loads(webres.read())
      if jres['codes']:
        srid = int(jres['codes'][0]['code'])
    except:
      srid=4326 # ensure set back to 4326 whatever happens    
          
try:
    #Try to detect the encoding
    dbf = open(dbf_file, 'rb')
    db = dbfUtils.dbfreader(dbf)
    detector = UniversalDetector()
    for row in db:
      detector.feed(str(row))
      if detector.done: break
    detector.close()
    dbf.close()
    encoding = detector.result["encoding"]
    if encoding=="ascii":
        encoding="LATIN1"
except:
    #if encoding detection fails, attempt default UTF8
    encoding = "UTF8"

print "%s,%s,%s,%s" % (srid,encoding,shp_file,name)
