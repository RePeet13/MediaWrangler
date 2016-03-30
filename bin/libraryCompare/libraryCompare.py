import csv, inspect, os, pprint, sys
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"lib")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
import progressbar as pb

files = [
    'Hulk-Movies-Level 4-20160226-153135.csv',
    'TheCave-Movies-Level 4-20160226-183246.csv'
]


def read_csv(filename):
    with open('files/' + filename) as input_list:
        missingImdb = []
        ret_dict = {}
        reader = csv.DictReader(input_list, delimiter=',')

        for line in reader:
            # pprint.pprint(line)
            # print(line['Title']),
            # print(line['Bitrate']),
            # print(line['Width']),
            # print(line['Height'])
            # if ret_dict.has_key(line['Title']):
                # print (filename, line['Title'], ret_dict[line['Title']])
            # TODO we should add it to the delete list and keep highest quality
            # ret_dict[line['Title']] = (line['Bitrate'], line['Width'], line['Height']) # TODO this will just overwrite if there is two of the same title in one collection, though, right?

            if 'IMDB Id' in line and line['IMDB Id'] == '':
                missingImdb.append(line)

            if line['Title'] not in ret_dict:
                ret_dict[line['Title']] = []
            ret_dict[line['Title']].append(line)

        if len(missingImdb) > 0:
            ret_dict['missingImdb'] = missingImdb
        return ret_dict


def processLists(lists):
    missingInHost = {}
    masterList = {}
    duplicateList = {}

    for host, itemlist in lists.iteritems():
        if host not in missingInHost:
            missingInHost[host] = []

        # bar = pb.ProgressBar()
        print('Ingesting host: ' + host)
        # for title,item in bar(itemlist.iteritems()):
        for title, item in itemlist.iteritems():
            for i in item:
                i['host'] = host
                i = rankItem(i)
                if title not in masterList:
                    masterList[title] = [i]
                else:
                    ## TODO need a bit more logic to see if really a dupe, or just in both libraries
                    add = True # add by default, don't add if only different hosts
                    for m in masterList[title]:
                        eq = moviesAreEqual(m, i)
                        if eq['equal']:
                            add = False
                    if add:
                        tmp = masterList[title]
                        i['differences'] = eq
                        tmp.append(i)
                        # for x in tmp:
                            # print x['Title']
                        duplicateList[title] = tmp
                        masterList[title].append(i)

    writeOutDupeList(duplicateList)

    for title in masterList:
        for host, itemlist in lists.iteritems():
            if title not in itemlist:
                missingInHost[host].append(title)

    writeOutMissingList(missingInHost)


def rankItem(item):
    # TODO have a ranking system here
    item['rank'] = 1
    return item


def moviesAreEqual(item1, item2):
    out = {'equal':True}
    ## TODO handle duplicate movies in one listing, values look like {'Audio Channels': '2 - 6'},
    print ('---------\nLooking for differences in ' + item1['Title'] + ' and ' + item2['Title'])
    # might be better to have white list of keys (not in whitelist)
    ignoredKeys=['Updated', 'Added', 'Media ID', 'Video FrameRate', 'Audio Title', 'Genres', 'Content Rating']

    for key,value in item1.iteritems():
        if item1['IMDB Id'] != item2['IMDB Id']:
            # print ('Difference for ' + item1['IMDB Id'] + ' and ' + item2['IMDB Id'])
            out['IMDB Id'] = {1:item1['IMDB Id'], 2:item2['IMDB Id']}
        elif key == 'host':
            print ('Hosts are: ' + item1['host'] + ' and ' + item2['host'])
            out['host'] = {1:item1['host'], 2:item2['host']}
        elif (item1['Duration'] != item2['Duration']) and (abs(int(item1['Duration'].split(':')[1]) - int(item2['Duration'].split(':')[1])) > 10):
            ## TODO handle the case when there's no hours
            print ('Difference for ' + item1['Duration'] + ' and ' + item2['Duration'])
            out['Duration'] = {1:item1['Duration'], 2:item2['Duration']}
        ## TODO Could put the difference in size bit here
        elif key in ignoredKeys:
            continue
        elif value != item2[key]:
            print (value + ' is not equal to ' + item2[key])
            out[key] = {1:value, 2:item2[key]}
    if len(out) > 2: # greater than one to account for host and equal fields
        out['equal'] = False
    return out


def list_in_dict(list1, list2, list1name, list2name):
    ret_string = list1name + 'and ' + list2name + ' differences' + '/n'
    ret_string1 = ''
    ret_string2 = ''
    ret_string3 = ''


    for item in list1:
        #check for in list1, but not 2
        if item not in list2:
            ret_string1 += createout(item, list1)
        #check for in list2, but not 1
        #check for in both list, but not the same bitrate/width/height

    for item in list2:
        if item not in list1:
            ret_string2 += createout(item, list2)

        if (item in list1 and not (item, list1[item][0], list1[item][1], list1[item][2]) == (item, list2[item][0], list2[item][1], list2[item][2])):
            ret_string3 += '(' + list1name +') ' + createout(item, list1) + ' and (' + list2name + ') ' + createout(item, list2)

    ret_string += list1name + ' items not in '+ list2name + '\n--------------------------------\n' + ret_string1 + '\n'
    ret_string += list2name + ' items not in '+ list1name + '\n--------------------------------\n' + ret_string2 + '\n '
    ret_string += 'items in both that are different ' + '\n--------------------------------\n' + ret_string2
    return ret_string + '\n\n'


def createout(item, list):
    return ', '.join((item, list[item][0], list[item][1], list[item][2])) + '\n'


def createMissingText(host, itemlist):
    t = '\n' + host + '\n--------------------------------\n'
    for item in itemlist:
        t += item['Title'] + '\n' # + ' -> ' + item + '\n'
    return t


def writeOutDupeList(dupeList):
    text = 'Duplicates Found and Where\nTotal Found: ' + str(len(dupeList)) + '\n--------------------------------\n\n'

    for t, d in dupeList.iteritems():
        text += t + '\n'
        for item in d:
            text += stripChars(item['host'] + ' - rank: ' + str(item['rank'])) + '\n' # we could put more info here if desired
            if 'differences' in item:
                text += '\t' + str(item['differences']) + '\n'
        text += '--------------------------------\n'
    print ('Writing Duplicates file')
    with open('output/duplicateList.txt', 'wb') as text_file:
        text_file.write(text)


def writeOutMissingList(missingInHost):
    l = 0
    h = 0

    for host in missingInHost:
        h = h + 1
        l = l + len(missingInHost[host])

    text = 'Items Found Missing in Hosts and Where\nTotal Found: ' + str(l) + ' in ' + str(h) + ' hosts' + '\n--------------------------------\n\n'

    for host, items in missingInHost.iteritems():
        text += host + ':\n'
        for title in items:
            text += stripChars('- ' + title) + '\n' # we could put more info here if desired
        text += '\n'

    print ('Writing Missing Items file')
    with open('output/missingList.txt', 'wb') as text_file:
        text_file.write(text)


def stripChars(t):
    return t.replace('\n', ' ')


def getfiles():
    global files
    hulk_movie = read_csv(files[0])
    cave_movie = read_csv(files[1])

    missingText = 'Files Missing IMDB\n'
    if 'missingImdb' in hulk_movie:
        missingText += createMissingText('hulk', hulk_movie['missingImdb'])
    if 'missingImdb' in cave_movie:
        missingText += createMissingText('cave', cave_movie['missingImdb'])
    print('Writing missingImdb file')
    with open('output/missingImdb.txt', 'wb') as text_file:
        text_file.write(missingText)

    # Remove missing imdbs because it will add duplicate noise (they're already in the main list)
    hulk_movie.pop('missingImdb')
    cave_movie.pop('missingImdb')

    processLists({'hulk':hulk_movie,'cave':cave_movie})
    # out_text = 'File Differences \n'
    # out_text += list_in_dict(hulk_movie, cave_movie, 'Hulk', 'Cave')
    # with open('Output.txt', 'wb') as text_file:
    #     text_file.write(out_text)


getfiles()
