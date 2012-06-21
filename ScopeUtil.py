# Scope/VCWS Module

import sys
import os
import datetime


##################################################################################
# Add Scope runtime into PATH
SCOPEBIN = os.path.join(os.environ['INETROOT'], r'private\tools\ScopeBin')
os.environ['PATH'] = os.environ['PATH'] + ';' + SCOPEBIN
##################################################################################



def GetStreamInfo(streamName):
  ''' Get the stream infomation, return (filesize, createTime)
  If the stream doesn't exist, filesize will be -1'''
  if streamName.find('?') > 0 :
    streamName = ResolveStreamset(streamName)

  getStreamInfoCommand = 'scope.exe streaminfo ' + streamName

  fileSize = -1
  createTime = ''

  for property in os.popen(getStreamInfoCommand):
    if property.find('Committed Length') > 0 :
      fileSize = long(property.split(' : ')[1].strip())
    elif property.find('Creation Time') > 0 :
      createTime = property.split(' : ')[1].strip()
    elif property.find('Published Update Time') > 0 :
      modifyTime = property.split(' : ')[1].strip()
    elif property == "Error getting stream info." :
      fileSize = -1
      break

  return fileSize, createTime, modifyTime

def IsStreamExist(streamName):
  '''Query if a stream exists'''
  return GetStreamInfo(streamName)[0] >= 0

def GetStreamNames(dir):
  '''Get all the stream names under a certain directory on cosmos
  It's not recursive. If the dir doesn't exist return empty array'''
  command = 'scope.exe dir -b -nd ' + dir
  # each line of the output is a stream in that dir.
  result = [line.strip() for line in os.popen(command)]
  if len(result) > 0 and result[0].find('Error in running') == 0:
    return []
  else:
    return result

def UploadStreamToCluster(srcName, dstName):
  '''Copy a local file to a cosmosr.'''
  uploadStreamCommand = 'scope.exe copy {0} {1}'.format(srcName, dstName)
  os.system(uploadStreamCommand)
	
def RenameStream(srcName, dstName):
  '''Rename a cosmos stream.'''
  command = 'scope.exe rename %s %s' % (srcName, dstName)
  os.system(command)

def DeleteStream(streamName):
  '''Delete a cosmos stream.'''
  command = 'scope.exe delete %s' % streamName
  os.system(command)

def GetFileNames(dir):
  '''Get all files under a local dir not including sub-dir.
  All names include absolute path'''
  result = []
  for file in os.listdir(dir):
    name = os.path.join(dir, file)
    if not os.path.isdir(name):
      result.append(name)
  return result

def GetNameOnly(file):
  '''Retrive the name from the absolute path name'''
  index = max(file.rfind('\\'), file.rfind('/'))
  if index >= 0:
    return file[index + 1:]
  else:
    return file

def CloneDirToCluster(localDir, clusterDir):
  '''Copy a local folder to cluster directory.
  The cluster directory will be deleted.'''
  # Delete Cluster folder first.
  for stream in GetStreamNames(clusterDir):
    DeleteStream(stream)
  # Copy the local Dir to Cluster
  for file in GetFileNames(localDir):
    UploadStreamToCluster(file, clusterDir + GetNameOnly(file))

def CloneClusterDirByRenaming(srcDir, destDir):
  '''Rename a cosmos srcDir to the destDir, the destDir
  will be moved to backup.'''
  
  today = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')

  # Rename destDir first to backup
  for stream in GetStreamNames(destDir):
    RenameStream(stream, destDir + 'backup/' + today + '/' + GetNameOnly(stream))
  # Rename
  for stream in GetStreamNames(srcDir):
    RenameStream(stream, destDir + GetNameOnly(stream))

