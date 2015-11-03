import argparse, logging, os, urllib, urllib2, zipfile
import xml.etree.ElementTree as xml
import pprint

apiKey = '269A9437555594F2'
apiBase = 'http://thetvdb.com/api/'
defaultLang = 'en'


def getLanguages():
    cwd = os.getcwd()
    os.chdir(getScriptPath())

    if (os.path.isfile('languages.xml') is False):
        logging.warning("Fetching languages")
        response = urllib2.urlopen(apiBase + apiKey + '/' + 'languages.xml')
        res = response.read()

        f = open('languages.xml', 'w')
        f.write(res)
        f.close()

    os.chdir(cwd)


### Save tvdb server time for incremental updates
def getServerTime():

    ### TODO likely this needs to be implemented in such a way that you can pass in a show name and look up when it was grabbed, or nothing

    cwd = os.getcwd()
    os.chdir(getScriptPath())

    if (os.path.isfile('serverTime.txt') is False):
        logging.debug("Fetching server time")
        response = urllib2.urlopen(apiBase + 'Updates.php?type=none')
        res = response.read()
        root = xml.fromstring(res)
        t = root[0].text
        # logging.debug('Server time is: ' + t)

        f = open('serverTime.txt', 'w')
        f.write(t)
        f.close()
    else:
        f = open('serverTime.txt', 'r')
        t = f.readline()
        f.close()
        # logging.debug('Loaded Server time is: ' + t)

    os.chdir(cwd)

    return t


### High level processing of tv show folder
def processTvFolder(d):

    cwd = os.getcwd()

    logging.debug('Checking TV directory: ' + d)

    out = []

    if (os.path.isfile(d) is True):
        logging.error('Passed in dir is a file: ' + d)
        return {'dir': d, 'success': False, 'error': 'Directory is not a folder'}

    os.chdir(d)

    tv_dirs = [x for x in os.listdir(os.getcwd()) if not os.path.isfile(os.path.join(d, x)) and x[0] != '.' and x != 'scratch']
    tv_dirs.sort()
    # logging.debug('TV Dirs to be considered: \n' + str(tv_dirs))

    for tvd in tv_dirs:
        o = processTvShow(os.getcwd(), tvd)
        out.append({'dir': tvd, 'parentDir': d, 'success': o['success'], 'error': o['error']})

    os.chdir(cwd)


### Process bits in the tv folder
def processTvShow(rootDir, d):

    cwd = os.getcwd()
    os.chdir(d)

    out = {}

    logging.debug('Processing TV Show Folder: ' + d)

    show = getTvShow(rootDir, d)

    showDetails = getTvShowDetails(rootDir, show)

    # TODO Remove
    out['success'] = True
    out['error'] = 'None'

    os.chdir(cwd)
    return out


### Call TVDB to get candidates, and then choose, show name
def getTvShow(rootDir, name):
    basePath = os.getcwd()
    out = {}
    # http://thetvdb.com/api/GetSeries.php?seriesname=

    websafeName = urllib.quote_plus(name)

    url = apiBase + 'GetSeries.php?seriesname="' + websafeName + '"'
    logging.debug('Querying TVDB for: ' + websafeName+ ' at: \n' + url)
    response = urllib2.urlopen(url)
    res = response.read()

    goToScratch(rootDir, name)
    f = open(websafeName + '.xml', 'w')
    f.write(res)
    f.close()
    os.chdir(basePath)

    allShows = []
    root = xml.fromstring(res)
    for series in root:

        s = {'seriesId': series.find('seriesid').text if series.find('seriesid') is not None else 'None', 
            'name': series.find('SeriesName').text if series.find('SeriesName') is not None else 'None',
            'imdbId': series.find('IMDB_ID').text if series.find('IMDB_ID') is not None else 'None',
            'overview': series.find('Overview').text if series.find('Overview') is not None else 'None',
            'imdbUrl': 'http://www.imdb.com/title/' + series.find('IMDB_ID').text if series.find('IMDB_ID') is not None else 'None',
            'originalName': name
            }

        allShows.append(s)

    printTheShows(allShows)

    pickedShow = False

    while not pickedShow:
        try:
            ans = raw_input('Choose a show (1), or ask for overview of show (2?): ')
            if len(ans) == 1:
                out = allShows[int(ans)-1]
                pickedShow = True
            elif len(ans) == 2 and ans[1] =='?':
                printShowDetails(allShows[int(ans[0])-1])
            else:
                print('What? \n')
        except IndexError, e:
                print("What? That's not a choice! \n")
    return out


### Print the shows for selection
def printTheShows(arr):
    c = 1
    for s in arr:
        print(str(c) + ') ' + s['name'] + ' - IMDB: ' + s['imdbUrl'])
        c += 1


### Print the overview for the show as well
def printShowDetails(o):
    print(o['name'])
    print(o['imdbUrl'])
    print(o['overview'])


### Get the details for each show
def getTvShowDetails(rootDir, show):
    basePath = os.getcwd()
    sid = show['seriesId']
    # TODO catch keyError here, check that sid has something in it

    url = apiBase + apiKey + '/series/' + sid + '/all/' + defaultLang + '.zip'
    logging.debug('Querying TVDB for: ' + show['name'] + ' at: \n' + url)
    # response = urllib2.urlopen(url)
    # res = response.read()

    goToScratch(rootDir, show['originalName'])
    # f = open(show['name']+'.zip', 'w')
    # f.write(res)
    # f.close()

    getunzipped(url, os.getcwd())

    if os.path.isfile(defaultLang + '.xml'):
        processSeriesXml(defaultLang + '.xml')

    os.chdir(basePath)


### Process the series detail data returned from TVDB
def processSeriesXml(seriesFileName):
    tree = xml.parse(seriesFileName)
    root = tree.getroot()
    logging.debug(root)

    seasons = {}
    for ep in root.findall('Episode'):
        s = ep.find('SeasonNumber').text
        if s not in seasons:
            seasons[s] = []
        tmp = {
            'id': ep.find('id').text,
            'EpisodeName': ep.find('EpisodeName').text,
            'EpisodeNumber': ep.find('EpisodeNumber').text
        }
        seasons[s].append(tmp)

    for s in seasons:
        seasons[s].sort(key=lambda x: x['EpisodeNumber'])
    pprint.pprint(seasons)



### Go to (and make if necessary) scratch folder
def goToScratch(rootDir, name):
    ### Find and/or go into scratch folder
    tv_dirs = [x for x in os.listdir(rootDir) if x == 'scratch']
    # logging.debug(str(tv_dirs))
    if (len(tv_dirs) == 0):
        os.mkdir(os.path.join(rootDir, 'scratch'))
    os.chdir(os.path.join(rootDir, 'scratch'))

    ### Find and/or go into the specific folder
    tv_dirs = [x for x in os.listdir(os.getcwd()) if x == name]
    if (len(tv_dirs) == 0):
        os.mkdir(os.path.join(os.getcwd(), name))
    os.chdir(os.path.join(os.getcwd(), name))


### Get and unzip a file
### From: http://stackoverflow.com/questions/1774434/download-a-zip-file-to-a-local-drive-and-extract-all-files-to-a-destination-fold
def getunzipped(theurl, thedir):
    name = os.path.join(thedir, 'temp.zip')
    try:
        name, hdrs = urllib.urlretrieve(theurl, name)
    except IOError, e:
        print "Can't retrieve %r to %r: %s" % (theurl, thedir, e)
        return
    try:
        z = zipfile.ZipFile(name)
    except zipfile.error, e:
        print "Bad zipfile (from %r): %s" % (theurl, e)
        return
    for n in z.namelist():
        dest = os.path.join(thedir, n)
        destdir = os.path.dirname(dest)
        if not os.path.isdir(destdir):
            os.makedirs(destdir)
        data = z.read(n)
        f = open(dest, 'w')
        f.write(data)
        f.close()
    z.close()
    os.unlink(name)


### Path where this script resides ###
def getScriptPath():
    return os.path.dirname(os.path.realpath(__file__))


# For directories without a leading slash, append the current working dir
def massageInputDirs(dirs):
    out = []
    for d in dirs:
        if d[0] is not '/':
            out.append(os.path.join(os.getcwd(), d))
            # logging.debug(d)
        else:
            out.append(d)
    return out


### Respond to call from command line ###
if __name__ == "__main__":
    global cwd
    cwd = os.getcwd()
    
    ### Arg Parsing ###
    parser = argparse.ArgumentParser()
    # parser.add_argument('name', help='Name of the project (and folder) to create', nargs='?', default='_stop_')
    # parser.add_argument('-c', '--contributors', dest='contributors', help='Contributors to the project', nargs=3, action='append', metavar=('cName', 'cEmail', 'cRank'))
    # parser.add_argument('-e', '--example', dest='example', help='Generate example folder', action='store_true')
    # parser.add_argument('-i', '--info', dest='info', help='Very short description of the project')
    # parser.add_argument('-s', '--scm', dest='scm', help='Which source control management you would like initialized', choices=['git', 'None'])
    # parser.add_argument('-t', '--template', dest='template', help="Template name (also used as the name of the template's enclosing folder)", default='Generic')

    parser.add_argument('-v', '--verbose', dest='verbosity', help='Increase verbosity (off/on/firehose)', action='count', default=0)
    parser.add_argument('dirs', help='TV Show Directory', nargs='+')
    args = parser.parse_args()
    
    ### Initialize Logging ###
    if args.verbosity == 0:
        l = logging.WARNING
    elif args.verbosity == 1:
        l = logging.INFO
    else:
        l = logging.DEBUG

#   TODO remove, only for debuggin purposes
    l = logging.DEBUG
        
    logging.basicConfig(level=l, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.debug(str(args))

    ### Implement language chooser here if desired
    getLanguages()

    ### THE REAL WORK
    dirs = massageInputDirs(args.dirs)
    for d in dirs:
        processTvFolder(d)

    ### Reset working directory to original ###
    os.chdir(cwd)

    