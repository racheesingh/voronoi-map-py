#!/usr/bin/python2

import sys
import numpy as np

# py_geo_voronoi: https://github.com/Softbass/py_geo_voronoi
import voronoi_poly 

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def main():

    PointsMap={}
    lat = []
    lon = []
    serverName = []

    for line in sys.stdin:
        data=line.strip().split(" ")
        try:
            
            if data[ 1 ] == 'Not':
                continue
            lat.append( float( data[ 1 ] ) )
            lon.append( float( data[ 2 ] ) )
            serverName.append( data[ 0 ] )
            PointsMap[data[0]]=(float(data[2]),float(data[1]))
          
        except:
            sys.stderr.write( "Invalid Input Line: "+line)
    
    # Method provided by py_geo_voronoi, returns a dictionary
    # of dictionaries, each sub-dictionary carrying information 
    # about a polygon in the Voronoi diagram.
    # PlotMap=False prevents the function from plotting the
    # polygons on its own, so that the printing can be handled 
    # here, on a Basemap.
    voronoiLattice = voronoi_poly.VoronoiPolygons(
        PointsMap, BoundingBox="W", PlotMap=False)

    # Creating a Basemap object with mill projection
    map = Basemap(projection='mill',lon_0=0,resolution='c')    
    
    # Filling colors in the continents and water region
    map.fillcontinents( color='white',lake_color='#85A6D9' )
    
    # Drawing coastlines and countries
    map.drawcoastlines( color='#6D5F47', linewidth=.7 )
    map.drawcountries( color='#6D5F47', linewidth=.7 )

    map.drawmapboundary( fill_color='#85A6D9' )

    # Drawing latitudes and longitude lines
    map.drawmeridians(np.arange(-180, 180, 30), color='#bbbbbb')
    map.drawparallels(np.arange(-90, 90, 30), color='#bbbbbb')
    
    # Preparing the data for a scatter plot of server locations
    x,y = map( lon, lat )
    X = np.array( x )
    Y = np.array( y )
    
    map.scatter( x, y, c='black', marker='.', zorder = 2)

    ax = plt.gca()

    # Plotting the Polygons returned by py_geo_voronoi
    for serialNo, data in voronoiLattice.items():
        polygon_data = data[ 'obj_polygon']
      
        pointList = []
        for point in list( polygon_data.exterior.coords ):
            pointMap = map( point[0], point[1] )
            pointList.append( pointMap )
        ax.add_patch( Polygon( pointList, fill=0, edgecolor='black' ))

    plt.title('Server Locations Across the Globe')
    plt.show()

if __name__ == "__main__":
    main()
