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
from cidrize import cidrize
import time

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

def plotDiagramFromLattice( ax, voronoiLattice, map ):
    voronoiPolygons = {}

    # Plotting the Polygons returned by py_geo_voronoi
    N = len( voronoiLattice.items() )
    for x in range( N ):
        data = voronoiLattice[ x ]
        serialNo = x
        polygon_data = data[ 'obj_polygon']
        pointList = []

        for point in list( polygon_data.exterior.coords ):
            pointMap = map( point[0], point[1] )
            pointList.append( pointMap )

        ax.add_patch( Polygon( pointList, fill=0, edgecolor='black' ))
        voronoiPolygons[ serialNo ] = np.array( pointList )
    
    return voronoiPolygons


def drawBarChart( serverNames, histDataList, maxIndex ):
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
 
    # Extremely nice function to auto-rotate the x axis labels.
    # It was made for dates (hence the name) but it works
    # for any long x tick labels
    fig.autofmt_xdate()
    

def getNetworkLocations( map ):

    f = open( "GeoIPCountryWhois.csv", "r" )
    networkLatLon = {}

    #for i in range( 160223 ):
    for i in range( 100 ):
        try:
            whois = f.readline().split(",")
        except EOFError:
            break
        networkFromIP = whois[0].strip( '"' )
        networkToIP = whois[1].strip( '"' )

        if networkFromIP == networkToIP:
            continue

        ip_range = str( networkFromIP ) + "-" + str( networkToIP )

        cidr_ip = cidrize( ip_range )

        gi = pygeoip.GeoIP( "/usr/local/share/GeoIP/GeoIPCity.dat",
                            pygeoip.STANDARD )
        try:
            gir = gi.record_by_addr( networkFromIP )
        except pygeoip.GeoIPError:
            print 'Error in:', networkFromIP
        if gir != None:
            x,y = map( gir[ 'longitude' ], gir[ 'latitude' ] )
            networkLatLon[ i ] = { 'xCoord': x, 'yCoord': y, 'cidr': cidr_ip }

        f.close()
    return networkLatLon
        
def main( PointsMap ):

    # Many server sites map to the same latitude and longitudes
    # Lets merge the duplicates
    PointsMap = mergeDuplicates( PointsMap )
    print len( PointsMap.keys() )
    for x,y in PointsMap.iteritems():
        print x, y

    # Method provided by py_geo_voronoi, returns a dictionary
    # of dictionaries, each sub-dictionary carrying information 
    # about a polygon in the Voronoi diagram.
    # PlotMap=False prevents the function from plotting the
    # polygons on its own, so that the printing can be handled 
    # here, on a Basemap.
    voronoiLattice = voronoi_poly.VoronoiPolygons(
        PointsMap, BoundingBox="W", PlotMap=False )

    numVoronoiCells = len( voronoiLattice.keys() )

    serverNames = []
    serialNum = []
    lat = []
    lon = []
    # Getting server names and lat, lon in order
    for x in range( numVoronoiCells ):
        serialNum.append( x )
        serverNames.append( voronoiLattice[ x ][ 'info' ] )
        lat.append( voronoiLattice[ x ][ 'coordinate' ][ 1 ] )
        lon.append( voronoiLattice[ x ][ 'coordinate' ][ 0 ] )

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

    # Adding annotations
    '''
    for name, a, b in zip(serialNum, x, y):
        plt.annotate(
            name, 
            xy = (a, b), xytext = (20,60),
            textcoords = 'offset points', ha = 'right', va = 'bottom',
            bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 1.5),
            arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
    '''

    now = time.time()
    # Processing networks from Whois database
    # and getting each network's lat, long
    # Also get the cidr notation
    networkLatLon = getNetworkLocations( map )

    print 'Time taken to run cidr stuff for 100 entries ' + \
        str( time.time() - now )

    ax = plt.gca()

    # Plotting the Polygons returned by py_geo_voronoi
    voronoiPolygons = plotDiagramFromLattice( ax, voronoiLattice, map )

    histogramData = {}
    histogramData = histogramData.fromkeys( 
        range( 0, len( serverNames ) ), 0 )

    # Writing the mapping of networks to servers to file
    pdnsFile = open( "pdns-config", "w" )

    for sNo, netDetail in networkLatLon.iteritems():
        net = np.array( [ [ netDetail[ 'xCoord' ], netDetail[ 'yCoord' ] ] ] )
        for serialNo, polygon in voronoiPolygons.items():
            if nx.points_inside_poly( net, polygon ):
                histogramData[ serialNo ] += 1
                for cidr_net in netDetail[ 'cidr' ]:
                    pdnsFile.write( str( cidr_net ) + ' :' + 
                                    '127.0.0.' + str( serialNo ) + "\n" )
                break
    pdnsFile.close()

    totalNetworks = sum( [ y for (x, y) in histogramData.items() ] )

    plt.title( 'Server Locations Across the Globe' )
    plt.savefig( 'voronoi-py.png' )
    plt.show()

    histDataList = [ y for (x,y) in histogramData.items() ]
    maxIndex = histDataList.index( max( histDataList ) )
    print 'The most loaded server:', serverNames[ maxIndex ], 'at index', maxIndex
    histDataList = np.array( histDataList )

    # Drawing histogram from the data
    drawBarChart( serverNames, histDataList, maxIndex )
    plt.show()
    print 'Printing server names and their corresponding serial numbers'
    for i in serialNum:
        print i, ':', voronoiLattice[ i ][ 'info' ]
    
