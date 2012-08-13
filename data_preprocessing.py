#!/usr/bin/python2

import re, pygeoip
import server_locations

def parseXMLFile( name ):
    file = open( name )
    data = file.read()
    dataLines = data.split( '\n' )

    # Patterns to match
    dirOpenPattern = re.compile(r'<Directory .*>', re.MULTILINE )
    parentDirClosePattern = re.compile(r'^</Directory>', re.MULTILINE )
    subDirClosePattern = re.compile(r'(\s)*</Directory>', re.MULTILINE )
    regexName = re.compile( r'LocalSite .*', re.DOTALL|re.IGNORECASE )
    regexURL = re.compile( r'HttpProxy .*', re.DOTALL|re.IGNORECASE )

    parentDirFlag = False
    subDirFlag = False
    foundLocalSite = False
    foundURLs = False

    parentDirName = ''
    subDirName = ''

    list_domain_names = []
    serverNamesDict = {}
    
    for line in dataLines:
        if not parentDirFlag:
            dirOpenMatch = dirOpenPattern.findall( line )
            if dirOpenMatch:
                parentDirFlag = True
                parentDirName = dirOpenMatch[0].split( '"' )[1][1:3]
                continue

        if not subDirFlag and parentDirFlag:
            assert parentDirFlag
            # Each ParentDir has atleast one Subdir
            dirOpenMatch = dirOpenPattern.findall( line )
            if dirOpenMatch:
                subDirFlag = True
                continue

        if not foundLocalSite and subDirFlag:
            assert subDirFlag and parentDirFlag
            matchName = regexName.findall( line )
            
            if matchName:
                foundLocalSite = True
                x = matchName[0]
                x = x.split()[-1][1:-1]
                subDirName = parentDirName + '/' + x
                continue
    
        if not foundURLs and foundLocalSite:
            assert foundLocalSite and subDirFlag and parentDirFlag
            list_domain_URLs = []
            matchURL = regexURL.findall( line ) 
            if matchURL:
                foundURLs = True
                matchURL = matchURL[0]

                pattern = r'http://.*?:'
                regex = re.compile( pattern, re.DOTALL|re.IGNORECASE )
                match = regex.findall( matchURL )
                match = [ x[:-1] for x in match ]

                serverNamesDict[ subDirName ] = match
                continue

        subDirCloseMatch = subDirClosePattern.findall( line )
        if subDirCloseMatch:
            subDirFlag = False
            foundLocalSite = False
            foundURLs = False

        parentDirCloseMatch = parentDirClosePattern.findall( line )
        if parentDirCloseMatch:
            parentDirFlag = False
            parentDirName = ''

    return serverNamesDict

def getServerNameAddr():
    patternName = r'LocalSite .*'
    patternURL = r'HttpProxy .*'
    list_domain_URLs = []
    list_domain_names = []
    while True:
        try:
            string = raw_input()
        except EOFError:
            break
        regexName = re.compile( patternName, re.DOTALL|re.IGNORECASE )
        regexURL = re.compile( patternURL, re.DOTALL|re.IGNORECASE )
        matchName = regexName.findall( string )
        matchURL = regexURL.findall( string )
        if matchName:
            for x in matchName:
                x = x.split()[-1][1:-1]
                list_domain_names.append( x )
        if matchURL:
            for x in matchURL:
                x = x.split()[-1][1:-1]
                list_domain_URLs.append( x )

    N = len( list_domain_names )    
    serverDict = {}
    # Make a dictionary from this information
    for i in range( N ):
        name = list_domain_names[ i ]
        
        # Getting all URLs from the URL string
        URLs = list_domain_URLs[ i ]
        pattern = r'http://.*?:'
        regex = re.compile( pattern, re.DOTALL|re.IGNORECASE )
        match = regex.findall( URLs )
        URLsFinal = []
        for x in match:
            URLsFinal.append( x[:-1] )

        serverDict[ name ] = URLsFinal

    return serverDict

def getServerLocations( serverDict ):
    gi = pygeoip.GeoIP( "/usr/local/share/GeoIP/GeoIPCity.dat",
                        pygeoip.STANDARD )
    import socket
    serverDictLocation = {}
    for name, urls in serverDict.iteritems():
        for url in urls:
            url = url[7:]
            gir = None
            try:
                gir = gi.record_by_name( url )
            except socket.gaierror:
                print 'socket error in', url
            except pygeoip.GeoIPError:
                print 'geoip error in', url
            if gir != None:
                break
        
        if gir != None:
            serverDictLocation[ name ] = \
            { 'url': urls, 'latitude': gir[ 'latitude' ], 
              'longitude': gir[ 'longitude' ] }
        #else:
        #    # NF = Not Found
        #    serverDictLocation[ name ] = \
        #    { 'url': urls, 'latitude': "NF", 'longitude': "NF" }

    return serverDictLocation

def main():

    # Parsing geolist.txt to get the names and addresses of all servers
    #serverDict = getServerNameAddr()
    serverDict = parseXMLFile( "geolist.txt" )
    print len(serverDict.items())

    # Get locations of all servers
    serverDictLocation = getServerLocations( serverDict )

    f = open( "location", "w" )
    for name, detail in serverDictLocation.iteritems():
        location = ( detail[ 'longitude' ], detail[ 'latitude' ] )
        urls = detail[ 'url' ]
        urlStr = ''
        for url in urls:
            urlStr = urlStr + ',' + url
        f.write( name + ' ' + str( location[0] ) + ' ' +
                 str( location[1] ) + ' ' + urlStr + '\n' )
    f.close()

    print len( serverDictLocation.items() )
    
    #server_locations.main( PointsMap )
        
if  __name__ == "__main__":
    main()
