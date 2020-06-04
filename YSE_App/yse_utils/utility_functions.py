import os,shutil,pdb,subprocess,shlex
import json,datetime,time,string,random,logging
import numpy as np
import healpy as hp
import MySQLdb

#from celery.contrib import rdb
from astropy.io import fits
from django.conf import settings
from django.db.models import Q, F, Avg


from YSE_App.models import *

logger = logging.getLogger(__name__)


### Utility functions ###
def sex2deg(inStr):
    bits = inStr.split(':')
    dsign = 1.0
    major = float(bits[0])
    minor = float(bits[1])
    sec = float(bits[2])
    if major==0.0 and inStr.startswith("-"):
        dsign = -1.0
    if major < 0.0 :
        decimal = major - minor/60.0 - sec/3600.0
    else :
        decimal = major + minor/60.0 + sec/3600.0
    decimal *= dsign
    return decimal

def deg2sex(angle):
    arg = np.fabs(angle)
    dd = int(arg)
    temp = 60.0*(arg - float(dd))
    mm = int(temp)
    ss = 3600.0*(arg - (float(dd)+(float(mm)/60.0)))
    if angle < 0:
        sexStr = "-{:02d}:{:02d}:{:05.2f}".format(dd,mm,ss)
    else:
        sexStr = "{:02d}:{:02d}:{:05.2f}".format(dd,mm,ss)
    return sexStr

def str2bool(s):
    if s.strip().lower() in ['t','true','ture']:
        return True 
    else:
        return False


def parse_field_input_data(fieldset_text_data):
    fieldData = []
    for line in fieldset_text_data.split('\n'):
        if len(line) > 0 and line[0] != '#':
            # parse
            row = line.strip().split(',')
            fieldName = row[0].lower().strip()
            # if sexagesimal, store, convert for decimal degrees
            if ':' in row[1]:
                fieldRA = row[1]
                fieldRA_deg = 15.*sex2deg(row[1].strip())
            else:
                fieldRA = deg2sex(float(row[1].strip())/15.)
                fieldRA_deg = float(row[1])

            # if sexagesimal, store, convert for decimal degrees
            if ':' in row[2]:
                fieldDec = row[2]
                fieldDec_deg = float(sex2deg(row[2].strip()))
            else:
                fieldDec = deg2sex(float(row[2].strip()))
                fieldDec_deg = float(row[2])
            telinstName = row[3].strip()
            filterName = row[4].strip()
            exposureTime = float(row[5].strip())
            fieldPriority = float(row[6].strip())
            obsStatus = str2bool(row[7])

            newEntry = [fieldName,fieldRA,fieldDec,fieldRA_deg,fieldDec_deg,
                        telinstName,filterName,exposureTime,fieldPriority,obsStatus]
            fieldData.append(newEntry)
    return fieldData

def parse_healpix_file(healpixForm):

    # this is extracting information about the healpix map
    # from the FORM that gets submitted. The form contains
    # the file, so we'll have to figure out a way to open the
    # file and extract nSide, etc. For now, just return
    # some dummy values that will allow us to save the model.

    return (1024,False)


def bulk_load_healpix(healPixFileID):

    try:
        # read in and resample (if needed)
        hpf = models.HealPixFile.objects.get(id__exact=healPixFileID)
        infile = '{}{}'.format(settings.MEDIA_ROOT,hpf.healPixFile.name)

        # temporary hack for dev/testing w/ text files
        if infile.split('.')[-1] == 'txt':
            return 0

        # create the temporary dump csv for the mysql read
        csvFile = '{}/healpixmaps/bulk_healpix.csv'.format(settings.FILE_DUMP_DIR)

        # try to fetch nside from the header
        hdu = fits.open(infile)
        nSide = hdu[1].header.get('NSIDE','NONSIDE')

        if nSide == 'NONSIDE' or nSide > 1024:
            # Honestly this should throw an exception...if the header doesn't have NSIDE
            # I don't think healpy will successfully read it (even though it tries).
            # We ought to assume we're getting reliable map data, and just bail if we're not.
            # For now this is here as a kludge, even though I doubt the map will get read in
            resampled_nside = 1024
        else:
            resampled_nside = nSide


        # read in and resample
        # note that in practice the map sampling shouldn't change since resampled_nside=nside
        # this is just written like this to accomodate resampling if its something we pursue
        hpMap,hpHeader = hp.read_map(infile,h=True,verbose=False)
        resampledMap = hp.ud_grade(hpMap,resampled_nside)
        pixRAArr,pixDecArr = hp.pix2ang(resampled_nside,range(len(resampledMap)),lonlat=True)

        # create a CSV with all the healpix data in the dump location
        outData = '# pixIndex pixRA pixDec pixProb mapFK'
        nPix = len(pixRAArr)
        with open(csvFile,'w') as fout:
            for i in range(nPix):
                outRow = '\n{}, {}, {}, {}, {}'.format(i,pixRAArr[i],pixDecArr[i],resampledMap[i],hpf.id)
                fout.write(outRow)
        # with open(csvFile, 'w') as fout:
        #     fout.write(outData)

        # connect to the database to run some SQL
        db = MySQLdb.connect(host=settings.DATABASES['default']['HOST'],
                             user=settings.DATABASES['default']['USER'],
                             passwd=settings.DATABASES['default']['PASSWORD'],
                             db=settings.DATABASES['default']['NAME'],
                             local_infile=True)
         
        # create a Cursor object to execute queries.
        cur = db.cursor()
        # construct the query
        # we can also drop/add indexes using this same process
        execCmd = 'LOAD DATA LOCAL INFILE \'{}\' '.format(csvFile)
        execCmd += 'INTO TABLE gw_assessor_healpixcell '
        execCmd += 'FIELDS TERMINATED BY \',\' '
        execCmd += 'LINES TERMINATED BY \'\n\' '
        execCmd += 'IGNORE 1 LINES ' #ignore the header
        execCmd += '(cellIndex,cellRA_deg,cellDec_deg,cellProb,cellHPFileFK_id);'
        # execute the bulk upload
        cur.execute(execCmd)
        db.commit()

        # close the cursor
        cur.close()
        # close the database connection
        db.close()

        return 0

    except Exception as e:
        hpf.ingestStatus = 'FAILED'
        hpf.save()
        logger.exception('failed in bulk_load_healpix: {}'.format(e))
        raise e


def run_tiling(**kwargs):

    # unpack kwargs used for running scripts
    fieldSetName = kwargs.get('fieldSetName')
    eventName = kwargs.get('fieldSetEventName')
    telescope = kwargs.get('telescope').upper()
    telescopeAbbreviation = telescope[0].upper()
    healPixBaseName = os.path.basename(kwargs.get('hpMap'))
    user = kwargs.get('user')
    scheduleDesignation = kwargs.get('scheduleDesignation','AA')

    # get the relevant paths
    tilingDir = os.path.join(settings.FILE_DUMP_DIR,'tiling/')
    userTilingDir = os.path.join(tilingDir,user)
    eventDir = os.path.join(userTilingDir,eventName)
    workingDir = os.path.join(eventDir,'{}_{}'.format(eventName,telescope))
    systemHealPixFile = os.path.join(settings.MEDIA_ROOT,kwargs.get('hpMap')) # the systems copy of the file
    workingHealPixFile = os.path.join(eventDir,healPixBaseName) # the copy we're using for this tiling


    # unpack kwargs for processing output
    # these will eventually become keywords in the telgon call itself
    raLoLimit = kwargs.get('raLoLimit',0.)
    raUpLimit = kwargs.get('raUpLimit',360.)
    decLoLimit = kwargs.get('decLoLimit',-90.)
    decUpLimit = kwargs.get('decUpLimit',90.)
    maxNTiles = kwargs.get('maxNTiles',10000)
    eventNumber = kwargs.get('fieldSetNumber',1) # this is not currently used for anything
    limitRABool = kwargs.get('limitRABool',False)
    limitDecBool = kwargs.get('limitDecBool',False)
    limitNTilesBool = kwargs.get('limitNTiles',False)

    # other
    fieldsOutFile = '{}/{}_{}_{}_Tiles.txt'.format(workingDir,eventName,scheduleDesignation,telescope)

    # make directories and move files into place
    if not os.path.isdir(tilingDir):
        os.mkdir(tilingDir)
    if not os.path.isdir(userTilingDir):
        os.mkdir(userTilingDir)
    if not os.path.isdir(eventDir):
        os.mkdir(eventDir)
    if not os.path.isdir(workingDir):
        os.mkdir(workingDir)

    shutil.copy(systemHealPixFile,workingHealPixFile)

    # formulate the calling string
    callingStr = 'export HOME=/home/brojonat/ \n ' # hack for astropy stuff
    callingStr += 'export PATH=\"{}:$PATH\" \n '.format(settings.CONDA_PATH)
    callingStr += 'source activate tiling \n '
    callingStr += 'python {}/Generate_Tiles.py '.format(settings.TEGLON_PATH)
    callingStr += '--gw_id {} '.format(eventName)
    callingStr += '--healpix_dir {} '.format(eventDir)
    callingStr += '--healpix_file {} '.format(healPixBaseName)
    callingStr += '--working_dir {} '.format(workingDir)
    callingStr += '--event_number {} '.format(eventNumber) #whatever
    callingStr += '--telescope_abbreviation {} '.format(telescopeAbbreviation)
    callingStr += '--filter r ' # TEMPORARY, dave should make this multiple?
    callingStr += '--exp_time 180 ' # TEMPORARY, dave should make this multiple?
    callingStr += '--schedule_designation {} \n'.format(scheduleDesignation)

    with subprocess.Popen('/bin/bash', 
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          universal_newlines=True) as proc:
        try:
            outs, errs = proc.communicate(callingStr)
            logger.info(outs)
            logger.info(errs)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            errStr = 'Failed in tiling subprocess (TIMEOUT): {}'.format(e)
            logger.exception(errStr)
            logger.info(outs)
            logger.info(errs)
        except Exception as e:
            errStr = 'Failed in tiling subprocess: {}'.format(e)
            logger.exception(errStr)


    # enter celery debugging at command line with `nc localhost 6900`
    # rdb.set_trace()


    # read in the data file to fieldText
    try:
        fieldText = ''
        fieldTextLineCounter = 0
        with open(fieldsOutFile,'r') as fin:
            for line in fin:
                # automatically skip the poorly formatted teglon header (!)
                if fieldTextLineCounter > 0 and len(line) > 0 and line[0] != '#':
                    fieldText += line
                fieldTextLineCounter += 1
    except Exception as e:
        errStr = 'Failed in reading {}'.format(fieldsOutFile)
        logger.exception(errStr)

    # create the fieldSet
    try:
        fieldSetInstance = models.FieldSet(fieldSetName=fieldSetName,
                                           fieldText=fieldText,
                                           fieldSetActive=False)
        fieldSetInstance.save()

        # parse the data
        parsingFieldData = parse_field_input_data(fieldText)
    except Exception as e:
        errStr = 'Failed in creating FieldSet'
        logger.exception(errStr)

    # iterate thru the text data and create the TargetField instances
    try:
        targetFieldList = []
        for i, row in enumerate(parsingFieldData):
            # populate and save the field models
            newTargetField = models.TargetField(fieldName = row[0],
                                         fieldRA = row[1],
                                         fieldDec = row[2],
                                         fieldRA_deg = row[3],
                                         fieldDec_deg = row[4],
                                         telinstName = row[5],
                                         filterName = row[6],
                                         exposureTime = row[7],
                                         fieldPriority = row[8],
                                         obsStatus = row[9],
                                         targetFieldActive = fieldSetInstance.fieldSetActive,
                                         fieldSet = fieldSetInstance)
            targetFieldList.append(newTargetField)
        models.TargetField.objects.bulk_create(targetFieldList) # boom
    except Exception as e:
        errStr = 'Failed in populating TargetFields'
        logger.exception(errStr)

    # now remove tiles that don't satisfy the user criteria
    # first get all TargetFields in this FieldSet
    # get all fields for this fieldset
    all_fields_queryset = fieldSetInstance.targetfield_set.all()
    logger.info('{} {} {}'.format(limitRABool,limitDecBool,limitNTilesBool))

    # if limitRA, select and delete
    if limitRABool:
        delete_fields_list = all_fields_queryset.filter(Q(fieldRA_deg__lt=raLoLimit) |
                                                        Q(fieldRA_deg__gt=raUpLimit)).values_list('id', flat=True)
        delRes = models.TargetField.objects.filter(pk__in=list(delete_fields_list)).delete()
        logger.info('DELETED {}'.format(delRes))

    # if limitDec, select and delete
    if limitDecBool:
        delete_fields_list = all_fields_queryset.filter(Q(fieldDec_deg__lt=decLoLimit) |
                                                        Q(fieldDec_deg__gt=decUpLimit)).values_list('id', flat=True)
        delRes = models.TargetField.objects.filter(pk__in=list(delete_fields_list)).delete()
        logger.info('DELETED {}'.format(delRes))

    # if limitNTiles, select, sort by prio, delete
    if limitNTilesBool:
        delete_fields_list = all_fields_queryset.order_by('-fieldPriority').values_list('id', flat=True)
        delete_fields_list = delete_fields_list[maxNTiles::]
        delRes = models.TargetField.objects.filter(pk__in=list(delete_fields_list)).delete()
        logger.info('DELETED {}'.format(delRes))




    # if any limits, we have to update fieldText in the fieldSet
    if limitRABool or limitDecBool or limitNTilesBool:
        # init
        fieldSetInstance.fieldText = ''
        all_fields_list = list(fieldSetInstance.targetfield_set.all())
        for tf in all_fields_list:

            # update the FieldSet text to reflect the new entry
            newTextRow = '{}, '.format(tf.fieldName)
            newTextRow += '{}, {}, '.format(tf.fieldRA,tf.fieldDec)
            newTextRow += '{}, {}, {}, '.format(tf.telinstName,tf.filterName,tf.exposureTime)
            newTextRow += '{}, {}\n'.format(tf.fieldPriority,tf.obsStatus)
            fieldSetInstance.fieldText += newTextRow
        # save
        fieldSetInstance.save()

    # clean up
    try:
        os.remove(workingHealPixFile)
        os.remove(fieldsOutFile)
    except Exception as e:
        errStr = 'Failed in cleanup'
        logger.exception(errStr)


    return 0
