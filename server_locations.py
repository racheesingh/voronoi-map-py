#!/usr/bin/python2

import sys
import numpy as np
import pygeoip

# py_geo_voronoi: https://github.com/Softbass/py_geo_voronoi
import voronoi_poly 

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import matplotlib.nxutils as nx

def plotDiagramFromLattice( ax, voronoiLattice, map ):
    voronoiPolygons = {}
    
    # Plotting the Polygons returned by py_geo_voronoi
    for serialNo, data in voronoiLattice.items():
        polygon_data = data[ 'obj_polygon']
        pointList = []

        for point in list( polygon_data.exterior.coords ):
            pointMap = map( point[0], point[1] )
            pointList.append( pointMap )

        ax.add_patch( Polygon( pointList, fill=0, edgecolor='black' ))
        #if serialNo == 6:
        #    ax.add_patch( Polygon( pointList, fill="red", edgecolor='red' ))
        voronoiPolygons[ serialNo ] = np.array( pointList )

    return voronoiPolygons

def mergeDuplicates( PointsMap ):

    uniquePointsMap = {}
    blackList = frozenset( [ ] )
    for name, coordinates in PointsMap.items():
        # Checking if we blacklisted this name before
        if name in blackList:
            continue

        finalName = name

        for name1, coordinates1 in PointsMap.items():
            if name == name1:
                continue
            if coordinates[0] == coordinates1[0] and \
            coordinates[1] == coordinates1[1]:
                # Add this name to blacklist so that
                # we don't consider it again
                blackList = blackList.union( [ name1 ] )
                finalName = finalName + ", " + name1

        uniquePointsMap[ finalName ] = coordinates

    return uniquePointsMap

def drawBarChart( serverNames, histDataList ):
    fig = plt.figure()
    ax = fig.add_subplot( 1,1,1 )

    N = len( histDataList )
    ind = range( N )
    ax.bar( ind, histDataList, facecolor='#777700',
             align='center')
    ax.set_ylabel('Number of Networks')
    ax.set_title('Distribution of Networks in Voronoi Cells',
                 fontstyle='italic')
    # This sets the ticks on the x axis to be exactly where we put
    # the center of the bars.
    ax.set_xticks(ind)
 
    # Set the x tick labels to the group_labels defined above.
    #ax.set_xticklabels(serverNames)
    
    # Extremely nice function to auto-rotate the x axis labels.
    # It was made for dates (hence the name) but it works
    # for any long x tick labels
    fig.autofmt_xdate()
    

def getNetworkLocations( map ):

    file = open( "GeoIPCountryWhois.csv", "r" )
    networkLatLon = []

    #for x in range( 50000 ):
    #while True:
    for x in range( 160222 ):
        try:
            whois = file.readline().split(",")
        except EOFError:
            break
        networkFromIP = whois[0].strip( '"' )
        gi = pygeoip.GeoIP( "/usr/local/share/GeoIP/GeoIPCity.dat",
                            pygeoip.STANDARD )
        try:
            gir = gi.record_by_addr( networkFromIP )
        except pygeoip.GeoIPError:
            print 'Error in:', networkFromIP
        if gir != None:
            x,y = map( gir[ 'longitude' ], gir[ 'latitude' ] )
            networkLatLon.append( [x, y] )
    return networkLatLon
        
def main():

    PointsMap={}
    lat = []
    lon = []
    # List of all server names
    serverName = []

    for line in sys.stdin:
        data = line.strip().split( " " )
        
        try:
            # Pygeoip could not find the location of the server
            if data[ 1 ] == 'Not':
                continue
            lat.append( float( data[ 1 ] ) )
            lon.append( float( data[ 2 ] ) )
            serverName.append( data[ 0 ] )
            PointsMap[ data[ 0 ] ]=( float( data[ 2 ] ), float( data[ 1 ] ) )
          
        except:
            sys.stderr.write( "Invalid Input Line: " + line )

    # Many server sites map to the same latitude and longitudes
    # Lets merge the duplicates
    PointsMap = mergeDuplicates( PointsMap )

    serverName = PointsMap.keys()

    # Method provided by py_geo_voronoi, returns a dictionary
    # of dictionaries, each sub-dictionary carrying information 
    # about a polygon in the Voronoi diagram.
    # PlotMap=False prevents the function from plotting the
    # polygons on its own, so that the printing can be handled 
    # here, on a Basemap.
    voronoiLattice = voronoi_poly.VoronoiPolygons(
        PointsMap, BoundingBox="W", PlotMap=False )

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

    # Plotting all the servers with a scatter plot
    map.scatter( x, y, c='black', marker='.', zorder = 2)

    ax = plt.gca()
    # Plotting the Polygons returned by py_geo_voronoi
    voronoiPolygons = plotDiagramFromLattice( ax, voronoiLattice, map )

    # Processing networks from Whois database
    # and getting each network's lat, long
    networkLatLon = getNetworkLocations( map )

    histogramData = {}
    histogramData = histogramData.fromkeys( 
        range( 0, len( voronoiPolygons ) ), 0 )

    for net in networkLatLon:
        net = np.array( [ net ] )
        for serialNo, polygon in voronoiPolygons.items():
            #print "For server Number " + str( serialNo ) + " checking.."
            if nx.points_inside_poly( net, polygon ):
                #print "Got one!"
                histogramData[ serialNo ] += 1
                break

    print histogramData

    totalNetworks = sum( [ y for (x, y) in histogramData.items() ] )
    print totalNetworks, len(voronoiPolygons)
            
        #if nx.points_inside_poly( points, verts )[0]:
        #    ax.add_patch( Polygon( pointList, fill=0, edgecolor='red' ))

    plt.title( 'Server Locations Across the Globe' )
    plt.savefig( 'voronoi-py.png' )
    plt.show()

    # Drawing histogram from the data
    histDataList = np.array( [ y for (x,y) in histogramData.items() ] )
    drawBarChart( serverName, histDataList )
    plt.show()

if __name__ == "__main__":
    main()
