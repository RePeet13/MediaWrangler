import argparse, logging, os

# Author taylor.peet (2015)

fileTypes = ('.mkv', '.mp4', 'avi', '.m4v') # TODO didn't i have a 'isVideo' link from devon somewhere?

def checkForDupes(dirs):

    dupes = set()
    master = {}

    for d in dirs:
        logging.debug('Checking into ' + d)
        # return all sub directories that are not hidden (and of course weed out files)
        # print(str(os.listdir(d)))
        subdirs = [x for x in os.listdir(d) if os.path.isdir(os.path.join(d,x)) and x[0] !='.']
        for subdir in subdirs:
            logging.debug('Looking at subdir ' + subdir)
            path = os.path.abspath(os.path.join(d,subdir))
            info = {
                    'path':path, # size, format
                    'file':[({'name':x,'size':sizeof_fmt(os.path.getsize(os.path.join(path,x)))}) for x in os.listdir(path) if os.path.isfile(os.path.join(path,x)) and x.endswith(fileTypes)]
                    }

            # If folder has more than one movie file, add to list
            if len(info['file']) > 1:
                dupes.add(subdir)
            # If movie is already in the master list, append info
            if subdir in master:
                master[subdir].append(info)
                dupes.add(subdir)
            else:
                master[subdir] = [info]

    # TODO have it pretty print the list of duplicats and their paths/sizes
    logging.debug('Dupes\n' + str(dupes))
    logging.debug([master[x] for x in master if x in dupes])


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


# For directories without a leading slash, append the current working dir
def massageInputDirs(dirs):
    out = []
    for d in dirs:
        if d[0] is not '/':
            out.append(os.path.join(os.getcwd(), d))
            logging.debug(d)
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
    parser.add_argument('dirs', help='Directories to check for duplicates', nargs='+')
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

    dirs = massageInputDirs(args.dirs)

    checkForDupes(dirs)

    ### Reset working directory to original ###
    os.chdir(cwd)

    