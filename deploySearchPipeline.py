# Author: Yizheng Cai
# Email: yicai@microsoft.com

import sys
import os
import datetime
import fnmatch
import glob
import emailhelper
from optparse import OptionParser
from xml.dom.minidom import Document

class MyVersion:
    version = []
    def __init__(self, ver):
        self.version = [int(x) for x in ver.split('.')]

    def __cmp__(self, ver):
        tocmp =  [int(x) for x in ver.split('.')]
        if len(tocmp) != len(self.version):
            raise Exception("Can't compare versions with different format") 

        for i in range(len(self.version)):
            if self.version[i] < tocmp[i]:
                return -1
            elif self.version[i] > tocmp[i]:
                return 1

        return 0


def write_deployment_log(user, reason, datestr, logfile):
    # Create the deployment log history
    # <deployment>
    #   <owner name="yicai"/>
    #   <date value="2012-02-06"/>
    #   <description>test</description>
    # </deployment>

    doc = Document()
    
    deployment = doc.createElement("deployment")
    doc.appendChild(deployment)

    owner = doc.createElement("owner")
    owner.setAttribute("name", user)
    deployment.appendChild(owner)

    date = doc.createElement("targetdate")
    date.setAttribute("value", datestr)
    deployment.appendChild(date)

    deploytime = doc.createElement("deploytime")
    deploytime.setAttribute("value", datetime.datetime.now().isoformat())
    deployment.appendChild(deploytime)

    description = doc.createElement("description")
    ptext = doc.createTextNode(reason)
    description.appendChild(ptext)
    deployment.appendChild(description)

    if os.path.exists(logfile):
        f = open(logfile, 'a')
        f.write(deployment.toprettyxml(indent="  "))
    else:
        f = open(logfile, 'w')
        f.write(doc.toprettyxml(indent="  "))

    f.close()

def deploy(options, reason):

    targetDir = options.target
    srcMergeAppDir = options.mergeapp
    srcSmartProcessingDir = options.smartprocessing

    binglabPath = r'\\binglab\builds\search\datamining_live'
    pipelineRoot = r'\\dmpipeline\Pipelines\Search'

    if options.buildname == 'official':
        binglabPath = os.path.join(binglabPath, options.buildname)
        folder = sorted(os.listdir(binglabPath), lambda x, y: MyVersion(x).__cmp__(y))[-1]
        binglabPath = os.path.join(binglabPath, folder)
    
    if options.buildname == 'rolling':
        binglabPath = os.path.join(binglabPath, options.buildname)
        binglabPath = os.path.join(binglabPath, os.path.split(glob.glob( os.path.join(binglabPath, 'latest', '*.latest'))[0])[-1].strip('.latest'))

    if len(options.mergeapp) == 0:
        srcMergeAppDir = os.path.join(binglabPath, r'retail\amd64\DataMining\ScopeJobs\SearchMergeApp')
        print srcMergeAppDir

    if len(options.smartprocessing) == 0:
        # Before smart processing build in the lab, use the following location as the source. 
        #srcSmartProcessingDir = os.path.join(binglabPath, r'retail\amd64\DataMining\ScopeJobs\SearchMergeApp')
        srcSmartProcessingDir = r'\\dmpipeline\Pipelines\Search\Bin\SmartProcessing'
        print srcSmartProcessingDir

    deploydate = datetime.datetime.strptime(options.deploydate, "%Y-%m-%d").date()

    tmpDir = 'tmp' + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    if len(options.target) == 0:
        targetDir = os.path.join(pipelineRoot, 'Bin')
        
        tmpDir = os.path.join(targetDir, tmpDir)
        
        if deploydate <= datetime.date.today():
            print 'Deployment date must be a future date'
            return
 
        targetDir = os.path.join(targetDir, options.deploydate)
        print targetDir
    else:
        tmpDir = os.path.join(os.path.split(options.target)[0], tmpDir)

    print tmpDir

    os.system("mkdir %s" % tmpDir)

    os.system("xcopy /E/I %s %s" % (srcSmartProcessingDir, tmpDir))    
    os.system("xcopy /E/I %s %s" % (srcMergeAppDir, tmpDir))
    
    if os.path.exists(targetDir):
        os.system("rd /S/Q %s" % targetDir)

    os.system("mv %s %s" % (tmpDir, targetDir))
        
    logPath = os.path.join(targetDir, "Logs")
    os.system("mkdir %s" % logPath)

    write_deployment_log(os.environ.get("USERNAME"), reason, deploydate.strftime("%Y-%m-%d"), os.path.join(pipelineRoot, "deploymentHistory.xml"))

    subject = '[Notification] SearchMergeApp deployed for ' + deploydate.strftime("%Y-%m-%d")

    if options.debug:    
        receivers = ['yuzhan']
    else:
        receivers = ['bingdmdpdri','srchdmtm']
    
    emailhelper.send_email_from_current_user(receivers, subject, reason) 


def main():

    tomorrowStr = (datetime.date.today() + datetime.timedelta(1)).strftime('%Y-%m-%d')
    
    usage = "usage: %prog [options] reason"
    parser = OptionParser(usage)

    parser = OptionParser()
    parser.add_option("-b", "--build", action="store", type="string", dest="buildname", default="official", help="choose official or rolling build to deploy")
    parser.add_option("-d", "--date", action="store", type="string", dest="deploydate", default=tomorrowStr, help="specify which date to deploy")
    parser.add_option("-s", "--smartprocessing", action="store", type="string", dest="smartprocessing", default="", help="specify the smart processing source binary folder to deploy")
    parser.add_option("-m", "--mergeapp", action="store", type="string", dest="mergeapp", default="", help="specify the merge app source binary folder to deploy")
    parser.add_option("-t", "--target", action="store", type="string", dest="target", default="", help="choose the target binary folder to deploy")
    parser.add_option("-p", "--debug", action="store_true", dest="debug", help="turn on debug mode")

    (options, args) = parser.parse_args()
    if (len(args) > 0):
        deploy(options, args[0])
    else:
        parser.error("reason for deployment is required")

if __name__ == "__main__":
    main()

