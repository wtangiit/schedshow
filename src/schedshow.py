#!/usr/bin/env python

import time
import sys
import matplotlib.pyplot as plt
from color import add,getColor
from optparse import OptionParser

SHOW = False

def getWidth(line_data_dictionary):
    '''get job width'''
    two=[] # two[0]: start point, two[1]: end point
    host=line_data_dictionary["exec_host"].rsplit("-")
    if len(host)==4:
        x=host[1][1:]    # case 1: ANL-R20-R21-2048 ---> x=20 y=21
        y=host[2][1:]    # case 2: ANL-R44-M1-512   ---> x=44 y=1 else:
    else:
        x=host[1][1:]    # case 3: ANL-R25-1024     ---> x=25 y=25
        y=host[1][1:]
     
    # Here x y are numbers represent for row and colums 
    # Following is converting them to x1 & y1 which are in "80" form

    if len(y) == 1:   # This is for case 2: which y=one_digit_number.
        x1 = 16*int(x[0:1]) + 2 * int(x[1:2]) + int(y) + 1
        y1 = x1 + 1
    else:                # For case 1 & 3:
        x1 = 16 * int(x[0:1]) + 2 * int(x[1:2])
        y1 = 16 * int(y[0:1]) + 2 * int(y[1:2]) + 2
    two.append(x1)
    two.append(y1)
    return two

def date_to_sec(fmtdate, dateformat="%m/%d/%Y %H:%M:%S"):
    t_tuple = time.strptime(fmtdate, dateformat)
    sec = time.mktime(t_tuple)
    return sec

def parseLine(line):
    '''parse a line into dictionary form:
     line_data[jobid:xxx, date:xxx, start_time:xxx, mjobidplane:xxx, etc.]
    '''
    line_data={}
    firstParse=line.split(";")
    line_data["eventType"]=firstParse[1]  
    
    # EventTypes: Q - submitting time, S - starting time, E - ending time
    
    if line_data["eventType"] == "Q":
        line_data["submitTime"] = firstParse[0]
    line_data["jobid"] = firstParse[2]
    substr = firstParse.pop()
    if len(substr) > 0:
        secondParse = substr.split(" ")
        for item in secondParse:
            tup = item.partition("=")
            if not line_data.has_key(tup[0]):
                line_data[tup[0]] = tup[2]
    return line_data                                      

def parseLogFile(filename):
    '''parse the whole work load file'''
    line_data={}
    # raw_job_dict = { "<jobid>":line_data, "<jobid2>":line_data2, ...}
    raw_job_dict = {}
    wlf = open(filename, "r")
    
    for line in wlf:
        if line[0].isdigit():
            line = line.strip("\n")
            line = line.strip("\r")
            line_data = parseLine(line)
            
            jobid = line_data["jobid"]
            #new jobid encountered, add a new entry for this job
            if not raw_job_dict.has_key(jobid):
                raw_job_dict[jobid] = line_data
            else:  #not a new job jobid, update the existing entry
                raw_job_dict[jobid].update(line_data)
                
    job_dict={}
    min_qtime = sys.maxint
    min_start = sys.maxint
    max_end = 0
    for k,v in raw_job_dict.iteritems():
        if v.has_key("end") and v.has_key("submitTime"):
            qtime_sec = date_to_sec(v['submitTime'])
            if qtime_sec < min_qtime:
                min_qtime = qtime_sec
            if float(v['start']) < min_start:
                min_start = float(v['start'])
            if float(v['end']) > max_end:
                max_end = float(v['end'])
            job_dict[k] = v 
    
    wlf.close()
                                     
    return job_dict, min_qtime, min_start, max_end

def getInHMS(seconds):
    hours = int(seconds) / 3600
    seconds =seconds - 3600*hours
    minutes = int(seconds) / 60
    seconds =seconds - 60*minutes
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def draw_job_allocation(job_dict, min_start, max_end, savefile=None):
    '''illustrate job allocation'''
    
    print "plotting: job allocation chart"

    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    timeTotal = max_end - min_start
    for k, v in job_dict.iteritems():
        start = float(v["start"])
        end = float(v["end"])
        width = getWidth(v)
        x = width[0]
        y = width[1]
    #print v["exec_host"]," ",x,"-",y,":",y-x   # this is for test
        #width[0]:x   start point on y-axes
        #width[1]:y   end point on y-axes
        threshold_x = (end-start) / 40.0
        threshold_y = 0
        currentColor = getColor(y, x, start, end, threshold_x, threshold_y)
        add(y, x, start, end, currentColor)
        
        #for i in range(x,y):    # old method of plotting.
        #    ax.broken_barh([(start,end-start)],(i,1),facecolor=currentColor)
        ax.barh(x, end-start, y-x, start, facecolor=currentColor)
    
    yticks=[0, 15, 16, 31, 32, 47, 48, 63, 64, 80]
    ax.set_yticks(yticks)
    ax.set_yticklabels(['R00','R07','R10','R17','R20','R27','R30','R37','R40','R47'],fontsize=6)
    ax.set_ylim(0, 80)
    
    inteval = timeTotal / 10
    timelist = []
    labels = []
    temptime = min_start
    for i in range(0,11):
        timelist.append(temptime)
        temptime = temptime+inteval
    for i in range(0,11):
        labels.append(time.asctime(time.localtime(timelist[i])))
    ax.set_xticks(timelist)
    ax.set_xticklabels(labels,fontsize = 6)
    ax.set_xlim(min_start , max_end)
    ax.set_xlabel('Time')
    
    ax.grid(True)
    
    if savefile:
        savefile += "-alloc.eps"
    else:
        savefile = "schedshow-alloc.eps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
    
def draw_live_jobs(job_dict, min_start, max_end, savefile=None):
    '''plot number of waiting jobs and running jobs'''
    print "plotting: waiting and running jobs"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("running jobs & waiting jobs")
    inteval = (max_end-min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    jobNumbers = []
    maxjob = 0
    for i in range(0,2000):
        jobNumber = 0
        for k,v in job_dict.iteritems():
            if float(v["start"])<timepoint and timepoint<float(v["end"]):
                jobNumber = jobNumber+1
        if jobNumber > maxjob:
            maxjob = jobNumber
        jobNumbers.append(jobNumber)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, jobNumbers, color="red")
    ax.set_ylim(0,maxjob + maxjob*0.1, color="red")
    ax.set_ylabel("running jobs", color="red")
    
    #waiting job axes
    ax2 = ax.twinx()
    inteval = (max_end-min_start) / 2000.0 #2000 points here
    timepoint = min_start
    timepoints = []
    
    waitNumbers = []
    maxwait = 0
    for i in range(0,2000):
        waitNumber = 0
        for k,v in job_dict.iteritems():
            if float(v["qtime"]) < timepoint and timepoint < float(v["start"]):
                waitNumber = waitNumber+1
        if waitNumber > maxwait:
            maxwait = waitNumber
        waitNumbers.append(waitNumber)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax2.plot(timepoints,waitNumbers,color='blue')
    ax2.set_ylim(0,maxwait+maxwait*0.1,color='blue')
    ax2.set_ylabel('waiting jobs',color='blue')

    ax.set_xlim( min_start ,max_end )
    timeTotal = max_end-min_start
    inteval = timeTotal/10
    timelist = []
    labels = [] 
    temptime = min_start
    for i in range(0,11):
        timelist.append(temptime)
        temptime = temptime + inteval
    for i in range(0,11):
        labels.append(time.asctime(time.localtime(timelist[i])))
    for i in range(0,11):
        labels[i]=labels[i][4:19]
    ax.set_xticks(timelist)
    ax.set_xticklabels(labels, fontsize=6)
    ax.set_xlabel('Time')
    ax.grid(True)
    
    if savefile:
        savefile += "-jobs.eps"
    else:
        savefile = "schedshow-jobs.edraw_job_allocationpnps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
    
def draw_sys_util(job_dict, min_start, max_end, savefile=None):
    '''draw number of busy nodes and nodes requested by queuing jobs'''
    print "plotting: system utilization"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("running jobs & waiting jobs")
    inteval = (max_end-min_start)/2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    jobNodes = []
    maxjobnode = 0
    for i in range(0,2000):
        jobNode = 0
        for k,v in job_dict.iteritems():
            if float(v["start"]) < timepoint and timepoint < float(v["end"]):
                jobNode = jobNode + int(v["Resource_List.nodect"])
        if jobNode > maxjobnode:
            maxjobnode = jobNode
        jobNodes.append(jobNode)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, jobNodes, color="red")
    ax.set_ylim(0, maxjobnode+maxjobnode*0.1, color="red")
    ax.set_ylabel("running jobs", color="red")
    
    #waiting job axes
    ax2 =ax.twinx()
    inteval = (max_end-min_start) / 2000.0 #2000 points here
    timepoint = min_start
    timepoints =[]
    
    waitNodes = []
    maxwaitnode = 0
    for i in range(0,2000):
        waitNode = 0
        for k, v in job_dict.iteritems():
            if float(v["qtime"]) < timepoint and timepoint < float(v["start"]):
                waitNode = waitNode + int(v["Resource_List.nodect"])
        if waitNode > maxwaitnode:
            maxwaitnode = waitNode
        waitNodes.append(waitNode)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax2.plot(timepoints, waitNodes, color='blue')
    ax2.set_ylim(0,maxwaitnode + maxwaitnode*0.1)
    ax2.set_ylabel('waiting jobs', color='blue')
   
    # plot for x axes and its labels
    ax.set_xlim(min_start ,max_end)
    timeTotal = max_end - min_start
    inteval = timeTotal/10
    timelist = []
    labels = []
    temptime = min_start
    for i in range(0, 11):
        timelist.append(temptime)
        temptime = temptime + inteval
    for i in range(0, 11):
        labels.append(time.asctime(time.localtime(timelist[i])))
    for i in range(0, 11):
        labels[i] = labels[i][4:19]
    ax.set_xticks(timelist)
    ax.set_xticklabels(labels,fontsize=6)
    ax.set_xlabel('Time')
    ax.grid(True)
    
    if savefile:
        savefile += "-sysutil.eps"
    else:
        savefile = "schedshow-sysutil.eps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()

def show_resp(job_dict):
    '''calculate response time'''
    li = []
    for k,v in job_dict.iteritems():
        temp = float(v["end"])-float(v["qtime"])
        li.append(temp)
    total = 0.0
    for item in li:
        total += item
    average = total/float(len(li))
    li.sort()
    maximum = li[len(li)-1]
    minimum = li[0]
    print "Response time\tTime in minutes\t\tTime in HMS"
    print "average:\t", int(average/60), "\t\t", getInHMS(average)
    print "maximum:\t", int(maximum/60), "\t\t", getInHMS(maximum)
    print "minimum:\t", int(minimum/60), "\t\t", getInHMS(minimum)
    print "\n"

def show_slowdown(job_dict):
    '''calculate slowdown'''
    li=[]
    for k, v in job_dict.iteritems():
        temp1 = float(v["start"])-float(v["qtime"])
        temp2 = float(v["end"])-float(v["start"])
        temp = (temp1+temp2)/temp2
        li.append(temp)
    total=0.0
    for item in li:
        total += item
    average = total/float(len(li))
    li.sort()
    maximum = li[len(li)-1]
    minimum = li[0]
    print "Bounded Slowdown"
    print "average:\t", average
    print "maximum:\t", maximum
    print "minimum:\t", minimum
    print "\n"

def show_wait(job_dict):
    '''calculate waiting time'''
    li = []
    for k,v in job_dict.iteritems():
        temp = float(v["start"]) - float(v["qtime"])
        li.append(temp)
    total = 0.0
    for item in li:
        total += item
    average = total/float(len(li))
    li.sort()
    maximum = li[len(li)-1]
    minimum = li[0]
    print "Wait time\tTime in minutes\t\tTime in HMS"
    print "average:\t", int(average/60), "\t\t", getInHMS(average)
    print "maximum:\t", int(maximum/60), "\t\t", getInHMS(maximum)
    print "minimum:\t", int(minimum/60), "\t\t", getInHMS(minimum)
    print "\n"

if __name__ == "__main__":
    p = OptionParser()
    p.add_option("-l", dest="logfile", type="string", 
                 help="path of log file (required)")
    p.add_option("-a", "--alloc", dest="alloc", action="store_true", default=False, 
                 help="plot bars represent for individual jobs ")
    p.add_option("-j", "--jobs", dest="jobs", action="store_true", default=False, 
                 help="show number of waiting & running jobs")
    p.add_option("-n", "--nodes", dest="nodes", action="store_true", default=False,
                 help="show number of waiting $ running nodes")
    p.add_option("-r", dest="response", action="store_true", default=False,
                 help="print response time to terminal")
    p.add_option("-b", dest="slowdown", action="store_true", default=False,
                 help="print bound time to terminal")
    p.add_option("-w", dest="wait", action="store_true", default=False,
                 help="print wait time to terminal")
    p.add_option("-o", dest="savefile", default="schedshow",
                 help="feature string of the output files")
    p.add_option("-s", dest="show", action="store_true", default=False,
                 help="show plot on the screen")
    (opts, args)=p.parse_args()
    
    if not opts.logfile:
        print "please specify path of log file"
        p.print_help()
        exit()
        
    if opts.savefile:
        savefile = opts.savefile
    else:
        savefile = "schedshow"
        
    if opts.show:
        SHOW = True

    starttime_sec = time.time()
        
    (job_dict, first_submit, first_start, last_end)=parseLogFile(opts.logfile)

    print "number of jobs:", len(job_dict.keys())
#print color_bars
    if opts.alloc:
        draw_job_allocation(job_dict, first_submit, last_end, savefile)
#print running & waiting jobs
    if opts.jobs:
        draw_live_jobs(job_dict, first_submit, last_end, savefile)
#-n print running & waiting nodes
    if opts.nodes:
        draw_sys_util(job_dict, first_submit, last_end, savefile)

    if opts.response:
        show_resp(job_dict)
    if opts.slowdown:
        show_slowdown(job_dict)
    if opts.wait:
        show_wait(job_dict)

    endtime_sec = time.time()
    print "---Analysis and plotting are finished, please check saved figures if any---"
    print "Tasks accomplished in %s seconds" % (int(endtime_sec - starttime_sec))