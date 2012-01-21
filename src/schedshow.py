#!/usr/bin/env python
'''Schedshow is a integrated program which will analyse the out \
		put file from Qsim. This program is written in python, \
		which utilizes an external library -- "matplotlib". '''

import time
import datetime
import sys
import random
import matplotlib.pyplot as plt
from optparse import OptionParser


SHOW = False
rec_list = []  # a list contains all the rectangles.
color_list = ['b', 'g', 'r', 'c', 'm', 'y', 'gray']  # 7 color are used here

class Rect:
    def __init__(self, p_1, p_2, p_3, p_4, color): 
    #""" default constructor """
        self.p_1 = p_1
        self.p_2 = p_2
        self.p_3 = p_3
        self.p_4 = p_4
        self.color = color
    def get_1(self):
    #""" get point 1 of the rect"""
        return self.p_1
    def get_2(self):
    #""" get point 2 of the rect"""
        return self.p_2
    def get_3(self):
    #""" get point 3 of the rect"""
        return self.p_3
    def get_4(self):
    #""" get point 4 of the rect"""
        return self.p_4
    def get_color(self):
    #""" get color of the rect"""
        return self.color
# End of Class

def add_rect(a_1, a_2, a_3, a_4, color):
    """ add an rect to rec_list """
    temp = Rect(a_1, a_2, a_3, a_4, color) 
    rec_list.append(temp)  

def get_color(t_1, t_2, t_3, t_4, thresholdx, thresholdy):  
    """test the point and return a color"""    
    temp_color = color_list[:]
    if len(rec_list) == 0:
        return random.choice(temp_color)
    else:
        for i in range(0, len(rec_list)):
            if abs(t_3 - rec_list[i].get_3()) <= thresholdx and \
            abs(t_4 - rec_list[i].get_4()) <= thresholdx and \
            abs(t_1 - rec_list[i].get_2()) <= thresholdy: 
                if rec_list[i].get_color() in temp_color:
                    temp_color.remove(rec_list[i].get_color())
            if abs(t_3 - rec_list[i].get_3()) <= thresholdx and \
            abs(t_4 - rec_list[i].get_4()) <= thresholdx and \
            abs(t_2 - rec_list[i].get_1()) <= thresholdy:
                if rec_list[i].get_color() in temp_color:
                    temp_color.remove(rec_list[i].get_color())
            if abs(t_1 - rec_list[i].get_1()) <= thresholdy and \
            abs(t_2 - rec_list[i].get_2()) <= thresholdy and \
            abs(t_4 - rec_list[i].get_3()) <= thresholdx:
                if rec_list[i].get_color() in temp_color:
                    temp_color.remove(rec_list[i].get_color())
            if abs(t_1 - rec_list[i].get_1()) <= thresholdy and \
            abs(t_2 - rec_list[i].get_2()) <= thresholdy and \
            abs(t_3 - rec_list[i].get_4()) <= thresholdx:
                if rec_list[i].get_color() in temp_color:
                    temp_color.remove(rec_list[i].get_color())
    return random.choice(temp_color)

def get_width(line_data_dictionary):
    '''get job width'''
    #two = [] # two[0]: start point, two[1]: end point
    host = line_data_dictionary["exec_host"].rsplit("-")
    if len(host) == 4:
        x = host[1][1:]    # case 1: ANL-R20-R21-2048 ---> x=20 y=21
        y = host[2][1:]    # case 2: ANL-R44-M1-512   ---> x=44 y=1 else:
    else:
        x = host[1][1:]    # case 3: ANL-R25-1024     ---> x=25 y=25
        y = host[1][1:]
     
    # Here x y are numbers represent for row and colums 
    # Following is converting them to x1 & y1 which are in "80" form

    if len(y) == 1:   # This is for case 2: which y=one_digit_number.
        x1 = 16 * int(x[0:1]) + 2 * int(x[1:2]) + int(y) + 1
        y1 = x1 + 1
    else:                # For case 1 & 3:
        x1 = 16 * int(x[0:1]) + 2 * int(x[1:2])
        y1 = 16 * int(y[0:1]) + 2 * int(y[1:2]) + 2
    return x1, y1

def date_to_sec(fmtdate, dateformat = "%m/%d/%Y %H:%M:%S"):
    '''convert date into seconds'''

    t_tuple = time.strptime(fmtdate, dateformat)
    sec = time.mktime(t_tuple)
    return sec

def parseLine(line):
    '''parse a line into dictionary form:
     line_data[jobid:xxx, date:xxx, start_time:xxx, mjobidplane:xxx, etc.]
    '''
    line_data = {}
    first_parse = line.split(";")
    line_data["eventType"] = first_parse[1]  
    
    # EventTypes: Q - submitting time, S - starting time, E - ending time
    
    if line_data["eventType"] == "Q":
        line_data["submittime"] = date_to_sec(first_parse[0])
    line_data["jobid"] = first_parse[2]
    substr = first_parse.pop()
    if len(substr) > 0:
        second_parse = substr.split(" ")
        for item in second_parse:
            tup = item.partition("=")
            if not line_data.has_key(tup[0]):
                line_data[tup[0]] = tup[2]
                
    if line_data.has_key("Resource_List.nodect"):
        line_data['nodes'] = line_data['Resource_List.nodect']
    else:
        line_data['nodes'] = 'unknown'
        
    return line_data
   
def parseline_alt(line):
    '''parse a line from alternative format'''
    def len2 (_input):
        _input = str(_input)
        if len(_input) == 1:
            return "0" + _input
        else:
            return _input
    
    temp= {}
    splits = line.split(';')
        
    for item in splits:
        tup = item.partition('=')
        if tup[1] == '=':
            temp[tup[0]] = tup[2]
    
    fmtdate = temp['qtime']
    submittime_sec = date_to_sec(fmtdate, "%Y-%m-%d %H:%M:%S")
    temp['submittime'] = submittime_sec
    temp['qtime'] = submittime_sec
    start_date = temp['start']
    start_sec = date_to_sec(start_date, "%Y-%m-%d %H:%M:%S")
    temp['start'] = start_sec
    end_date = temp['end']
    end_sec = date_to_sec(end_date, "%Y-%m-%d %H:%M:%S")
    temp['end'] = end_sec
    walltime_sec = temp['Resource_List.walltime']
    wall_time = int(float(walltime_sec) / 60) 
    walltime_minutes = len2(wall_time % 60)
    walltime_hours = len2(wall_time // 60)
    fmt_walltime = "%s:%s:00" % (walltime_hours, walltime_minutes)
    temp['Resource_List.walltime'] = fmt_walltime
    if not temp.has_key('exec_host'):
        temp['exec_host'] = "unknown"
    if temp.has_key("Resource_List.nodect"):
        temp['nodes'] = temp['Resource_List.nodect']
    else:
        temp['nodes'] = 'unknown'

    return temp                             

def parseLogFile(filename):
    '''parse the whole work load file'''
    # raw_job_dict = { "<jobid>":line_data, "<jobid2>":line_data2, ...}
    raw_job_dict = {}
    wlf = open(filename, "r")
    
    for line in wlf:
        line = line.strip('\n')
        line = line.strip('\r')
        if line[0].isdigit():
            temp = parseLine(line)
        else:
            temp = parseline_alt(line)

        jobid = temp['jobid']
        #new job id encountered, add a new entry for this job
        if not raw_job_dict.has_key(jobid):
            raw_job_dict[jobid] = temp
        else:  #not a new job id, update the existing entry
            raw_job_dict[jobid].update(temp)
                
    job_dict = {}
    min_qtime = sys.maxint
    min_start = sys.maxint
    max_qtime = 0
    max_end = 0
    for jobid, spec in raw_job_dict.iteritems():
        if spec.has_key("end") and spec.has_key("submittime"):
            qtime_sec = spec['submittime']
            if qtime_sec < min_qtime:
                min_qtime = qtime_sec
            if qtime_sec > max_qtime:
                max_qtime = qtime_sec
            if float(spec['start']) < min_start:
                min_start = float(spec['start'])
            if float(spec['end']) > max_end:
                max_end = float(spec['end'])
            #exclude deleted jobs which runtime is 0
            if float(spec["end"]) - float(spec["start"]) <= 0:
                continue
            
            format_walltime = spec.get('Resource_List.walltime')
            spec['walltime'] = 0
            if format_walltime:
                segs = format_walltime.split(':')
                #walltime_minuntes = int(segs[0]) * 60 + int(segs[1])
                spec['walltime'] = str(int(segs[0]) * 60 + int(segs[1]))
            else:  #invalid job entry, discard
                continue
               
            job_dict[jobid] = spec 
    wlf.close()
                                     
    return job_dict, min_qtime, min_start, max_qtime, max_end

def getInHMS(seconds):
    '''this allows convert sec into form HH:MM:SS'''
    hours = int(seconds) / 3600
    seconds = seconds - 3600 * hours
    minutes = int(seconds) / 60
    seconds = seconds - 60 * minutes
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def tune_workload(specs, frac = 1, anchor = 0):
    '''tune workload heavier or lighter, and adjust the start \
	time to anchor, specs should be sorted by submission time'''

#calc intervals (the first job's interval=0)
    lastsubtime = 0
    for spec in specs:
        if (lastsubtime == 0):
            interval = 0
        else:
            interval = float(spec['qtime']) - float(lastsubtime)
        lastsubtime = float(spec['qtime'])
        spec['interval'] = interval
        
    #if anchor is specified, set the first job submission time to anchor
    if anchor:
        specs[0]['qtime'] = anchor
    else:
        pass

    last_newsubtime = float(specs[0].get('qtime'))
    for spec in specs:
        interval = float(spec['interval'])
        newsubtime = last_newsubtime + frac * interval
        spec['qtime'] = newsubtime
        spec['interval'] = frac * interval
        last_newsubtime = newsubtime
    return specs

def sort_dict_qtime(job_dict):
    """ return a sorted-by-qtime list with job data"""
    temp_dict = {}
    sorted_list = []
    for key, val in job_dict.iteritems():
        temp_dict[val["qtime"]] = val
    for key, val in temp_dict.iteritems():
        temp_dict[val["qtime"]] = val
    key_list = temp_dict.keys()
    key_list.sort()
    for key in key_list:
        sorted_list.append(temp_dict[key])
    
    return sorted_list

def write_alt(job_dict, filename = None): 
    """ convert a PBS style log into alternate format """
    if filename:
        filename += "-alternate.log"
    else:
        filename = "schedshow-alternate.log"
    FILE = open(filename, "w")
    sorted_list = sort_dict_qtime(job_dict)
    for value in sorted_list: 
        jobid = "jobid=" + value["jobid"]
        qtime = "qtime=" + sec_to_date(value["qtime"])
        start = "start=" + sec_to_date(value["start"])
        end = "end=" + sec_to_date(value["end"])
        host = "exec_host=" + value["exec_host"]
        nodes = "nodes=" + value["Resource_List.nodect"]
        walltime ="walltime=" + value["Resource_List.walltime"]
        #nodes = "nodes=" + val[]
        line = "%s;%s;%s;%s;%s;%s;%s\n" \
			% (jobid, qtime, start, end, host, \
            nodes, walltime)
        FILE.write(line)
    FILE.close() 

def sec_to_date(s): 
    """ convert a string representing second into a formated string"""
    sec = float(s)
    date = datetime.datetime(time.gmtime(sec).tm_year, \
	  time.gmtime(sec).tm_mon, time.gmtime(sec).tm_mday, \
	  time.gmtime(sec).tm_hour, time.gmtime(sec).tm_min, \
	  time.gmtime(sec).tm_sec)
    return str(date)

def write_util_alt(job_dict, total_sec, util = None):
    """ write a alternate log from PBS log accoding to given util rate"""
    filename = str(util) + "-util-alt.log"
    FILE = open(filename, "w")
    fraction = calculate_sys_util(job_dict, total_sec) / float(util)
    print "fraction is: ", fraction
    sorted_value_list = sort_dict_qtime(job_dict)
    alt_value_list = tune_workload(sorted_value_list, fraction)
    for value in alt_value_list: 
        jobid = "jobid=" + value["jobid"]
        qtime = "qtime=" + sec_to_date(value["qtime"])
        start = "start=" + sec_to_date(value["start"])
        end = "end=" + sec_to_date(value["end"])
        host = "exec_host=" + value["exec_host"]
        nodes = "nodes=" + value["Resource_List.nodect"]
        walltime ="walltime=" + value["Resource_List.walltime"]
        #nodes = "nodes=" + val[]
        line="%s;%s;%s;%s;%s;%s;%s\n" % (jobid, qtime, start, end, host, \
            nodes, walltime)
        FILE.write(line)
    FILE.close() 

def draw_job_allocation(job_dict, min_start, max_end, savefile = None):
    '''illustrate job allocation'''
    
    print "plotting: job allocation chart"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    time_total = max_end - min_start
    for v in job_dict.itervalues():
        start = float(v["start"])
        end = float(v["end"])
        (x, y) = get_width(v)
        threshold_x = (end - start) / 40.0
        threshold_y = 0
        current_color = get_color(y, x, start, end, threshold_x, \
	      threshold_y)
        add_rect(y, x, start, end, current_color)
        ax.barh(x, end - start, y - x, start, facecolor = current_color)
     
    labels = []
    yticks = []
    for i in range(0, 80):
        yticks.append(i)
    ax.set_yticks(yticks)
    for i in range(0, 5):
        for j in range(0, 8):
            labels.append("R" + str(i) + str(j))
            labels.append("")
    ax.set_yticklabels(labels, fontsize = 11)
    ax.set_ylim(0, 80)
    
    inteval = time_total / 10
    timelist = []
    labels = []
    temptime = min_start
    for i in range(0, 11):
        timelist.append(temptime)
        temptime = temptime + inteval
    for i in range(0, 11):
        labels.append(time.asctime(time.localtime(timelist[i]))[4:-4])
    ax.set_xticks(timelist)
    ax.set_xticklabels(labels, rotation = 25, fontsize = 12)
    ax.set_xlim(min_start , max_end)
    ax.set_xlabel('Time', fontsize = 15)
    
    ax.grid(True)
    
    if savefile:
        savefile += "-alloc.png"
    else:
        savefile = "schedshow-alloc.png"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
    
def draw_running_jobs(job_dict, min_start, max_end, savefile=None):
    '''plot number of waiting jobs and running jobs'''
    print "plotting: running jobs"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("number of running jobs")
    inteval = (max_end-min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    job_numbers = []
    maxjob = 0
    for i in range(0, 2000):
        job_number = 0
        for v in job_dict.itervalues():
            if float(v["start"]) < timepoint and timepoint < float(v["end"]):
                job_number = job_number + 1
        if job_number > maxjob:
            maxjob = job_number
        job_numbers.append(job_number)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, job_numbers, color = "red")
    ax.set_ylim(0, maxjob + maxjob*0.1, color = "red")

    ax.set_xlim( min_start, max_end )
    time_total = max_end - min_start
    inteval = time_total / 10
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
    ax.set_xticklabels(labels, rotation = 25, fontsize = 11)
    ax.set_xlabel('Time')
    ax.grid(True)
    
    if savefile:
        savefile += "-jobs-running.png"
    else:
        savefile = "schedshow-jobs-running.png"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()

def draw_waiting_jobs(job_dict, min_start, max_end, savefile=None):     
    """ draw waiting jobs""" 
    print "plotting: waiting jobs"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("number waiting jobs")
    inteval = (max_end-min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    wait_numbers = []
    maxwait = 0
    for i in range(0, 2000):
        wait_number = 0
        for spec in job_dict.itervalues():
            if float(spec["qtime"]) < timepoint \
			    and timepoint < float(spec["start"]):
                wait_number = wait_number + 1
        if wait_number > maxwait:
            maxwait = wait_number
        wait_numbers.append(wait_number)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, wait_numbers, color = 'red')
    ax.set_ylim(0, maxwait+maxwait * 0.1, color = 'red')

    ax.set_xlim( min_start , max_end )
    time_total = max_end-min_start
    inteval = time_total / 10
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
    ax.set_xticklabels(labels, rotation = 25, fontsize = 11)
    ax.set_xlabel('Time')
    ax.grid(True)
    
    if savefile:
        savefile += "-jobs-waiting.png"
    else:
        savefile = "schedshow-jobs-waiting.png"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()

def draw_running_nodes(job_dict, min_start, max_end, savefile = None):
    '''draw number of busy nodes'''
    print "plotting: system utilization-busy nodes"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("busy nodes")
    inteval = (max_end - min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    job_nodes = []
    maxjobnode = 0
    for i in range(0, 2000):
        job_node = 0
        for spec in job_dict.itervalues():
            if float(spec["start"]) < timepoint \
			    and timepoint < float(spec["end"]):
                job_node = job_node + int(spec["Resource_List.nodect"])
        if job_node > maxjobnode:
            maxjobnode = job_node
        job_nodes.append(job_node)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, job_nodes, color = "red")
    ax.set_ylim(0, maxjobnode + maxjobnode*0.1, color = "red")
    # plot for x axes and its labels
    ax.set_xlim(min_start, max_end)
    time_total = max_end - min_start
    inteval = time_total / 10
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
    ax.set_xticklabels(labels, rotation = 25, fontsize = 11)
    ax.set_xlabel('Time')
    ax.grid(True)
    
    if savefile:
        savefile += "-sysutil-busy.png"
    else:
        savefile = "schedshow-sysutil-busy.png"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
   
def draw_waiting_nodes(job_dict, min_start, max_end, savefile=None):  
    """ show requested nodes"""
    print "plotting: system utilization-requested"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("waiting nodes")
    inteval = (max_end - min_start)/2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    wait_nodes = []
    maxwaitnode = 0
    for i in range(0, 2000):
        wait_node = 0
        for spec in job_dict.itervalues():
            if float(spec["qtime"]) < timepoint \
			    and timepoint < float(spec["start"]):
                wait_node = wait_node + int(spec["Resource_List.nodect"])
        if wait_node > maxwaitnode:
            maxwaitnode = wait_node
        wait_nodes.append(wait_node)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, wait_nodes, color = 'red')
    ax.set_ylim(0, maxwaitnode + maxwaitnode * 0.1)
    # x axess 
    ax.set_xlim(min_start , max_end)
    time_total = max_end - min_start
    inteval = time_total / 10
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
    ax.set_xticklabels(labels, rotation = 25, fontsize = 11)
    ax.set_xlabel('Time')
    ax.grid(True)
    
    if savefile:
        savefile += "-sysutil-requested.png"
    else:
        savefile = "schedshow-sysutil-requested.png"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
   
metric_header = [" ", "Avg", "Avg99", "Max", "99th", "90th", "80th",\
      "Median", "Min"]

def print_header():
    for item in metric_header:
        print item, '\t',

happy_dict = {} #temp

def happy_job(job_dict):
    '''show if the job is a happy job or not'''
    count = 0
    for val in job_dict.itervalues():
        jobid = val["jobid"]
        qtime = float(val["qtime"])
        stime = float(val["start"])
        size1 = int(val["exec_host"].split("-")[-1])
        prrty1 = (1/float(val["walltime"])) ** 3 * float(size1)
        end = []
        for val in job_dict.itervalues():
            if qtime >= float(val["qtime"]) and jobid != val["jobid"]:
                waittime = qtime - float( val["qtime"])
                size = int(val["exec_host"].split("-")[-1])
                prrty2 = ((1+waittime)/float(val["walltime"])) ** 3 * float(size)
                if prrty2 > prrty1:
                    end.append(val["end"])
        end.sort()
        if len(end) == 0:
            happy_dict[jobid] = val
            count = count + 1
        elif stime <= end[len(end)-1]:
            happy_dict[jobid] = val
            count = count + 1
    print "The number of happy jobs : ", count
    
def count_happy_job(job_dict):
    '''show if the job is a happy job or not'''
    count = 0
    specs = []
    for spec in job_dict.itervalues():
		specs.append(spec)
	
    def _subtimecmp(spec1, spec2):
		return cmp(spec1.get('qtime'), spec2.get('qtime'))

    specs.sort(_subtimecmp)

    for spec in specs:
		jobid = spec['jobid']
		qtime = float(spec['qtime'])
		stime = float(spec['start'])
		earlier_job_ends = [] 

		for spec2 in specs:
			if spec2['qtime'] < spec['qtime']:
				earlier_job_ends.append(float(spec2['end']))
			else:
				break
			
		if len(earlier_job_ends) == 0:
			count += 1
		else:
			if stime <= max(earlier_job_ends):
				count += 1
			
    print "happy job count: %s, ratio: %s" % (count, float(count)/len(specs))
                  
# some globle arguments

vs_dict = {}
s_dict = {}
l_dict = {}
vl_dict = {}

def show_size(job_dict):
    """ show all metrics"""
    for val in job_dict.itervalues():
        jobid = val["jobid"]
        host = val["exec_host"]
        if host[0] == 'A': #intrepid
            size = int(host.split("-")[-1])
            if size <= 512:
                vs_dict[jobid] = val
            elif 512 < size and size <= 2048:
                s_dict[jobid] = val
            elif 2048 < size and size <= 8192:
                l_dict[jobid] = val
            elif 8192 < size:
                vl_dict[jobid] = val
                    #print "Job category number"
                    
    print "Very Small: %s  Small: %s  Large: %s  Very Large: %s\n" \
        % (len(vs_dict.keys()), len(s_dict.keys()), len(l_dict.keys()), len(vl_dict.keys()) )

def show_resp(job_dict):
    '''calculate response time'''
    value_list = []
    
    total = 0.0
    for spec in job_dict.itervalues():
        temp  = (float(spec["end"]) - float(spec["qtime"])) / 60
        total += temp
        value_list.append(round(temp, 1))
    
    average = round(total/float(len(value_list)), 2)
    
    value_list.sort()
    index = int(len(value_list) * 0.99)
    avg_99 = round(sum(value_list[0:index]) / len(value_list[0:index]), 2)    
    maximum = value_list[len(value_list) - 1]
    median = value_list[len(value_list) / 2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]

    print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" \
     % (average, avg_99, maximum, percentile_99, \
	percentile_90, percentile_80, median, minimum)

def show_all_resp(dictionary):
    print "Resp Time (min):"
    print_header()
    print "\nAll\t",
    show_resp(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_resp(s_dict)
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_resp(vs_dict)
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_resp(l_dict)
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_resp(vl_dict)
    print '\n'
    
def show_wait(job_dict):
    '''calculate waiting time'''
    value_list = []
    total = 0.0
    for spec in job_dict.itervalues():
        temp = (float(spec["start"]) - float(spec["qtime"])) / 60
        total += temp
        value_list.append(round(temp, 1))

    average = round(total/float(len(value_list)), 2)
    
    value_list.sort()
    index = int(len(value_list) * 0.99)
    avg_99 = round(sum(value_list[0:index]) / len(value_list[0:index]), 2)  
    maximum = value_list[len(value_list) - 1]
    median = value_list[len(value_list) / 2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]
    
    if not opts.test:
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (average, avg_99,\
	      maximum, percentile_99, \
	      percentile_90, percentile_80, median, minimum)
    else:
        print "wait,  slowdown, and uwait "
        print average
        print avg_99
        print maximum
        print percentile_99
        print percentile_90
        print percentile_80
        print median
        print minimum
        print "\r"

def show_all_wait(dictionary):
    print "Wait time (min):" 
    print_header()
    print "\nAll\t",
    show_wait(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_wait(s_dict)
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_wait(vs_dict)
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_wait(l_dict)
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_wait(vl_dict)
    print '\r'
    
def show_utility_wait(job_dict, log_file_name):
    '''show average wait weighted by utility scores when job starts'''
    debug_file_name = log_file_name[:-4] + "-debug.log"
    
    dbgfile = open(debug_file_name, "r")
    total_utility_wait = 0
    total_utility = 0
    total_job = 0
    total_top_job = 0
    total_backfill_job = 0
    total_wait = 0
   
    jobid_list = []
    for line in dbgfile:
        line = line.strip('\n')
        line = line.strip('\r')
        fields = line.split(';')
        if len(fields) > 1 and fields[1] == "S":
            total_job += 1
            jobid = fields[2]
            jobid_list.append(jobid)
            job_pos = fields[3]
            job_utility = float(fields[3]) / 1000
            spec = job_dict[jobid]
            wait = (float(spec["start"]) - float(spec["qtime"]))
            total_utility_wait += job_utility * wait
            total_utility += job_utility
            total_wait += wait
            if job_pos == '0':
                total_backfill_job += 1
            if job_pos == '1':
                total_top_job += 1
    print "total_utility=", total_utility
    print "total_top_job=", total_top_job
                
    avg_wait = total_wait / total_job
    avg_utility_wait = total_utility_wait / total_utility
    
    jobids = job_dict.keys()
    
    list1 = set([])
    waitlist = list([])
    for id in jobids:
        if id not in jobid_list:
            list1.add(id)
            spec = job_dict[id]
            temp = (float(spec["start"]) - float(spec["qtime"])) / 60
            waitlist.append(temp)
    print "job in job_dict but not in debug log:", len(list1)
    #print waitlist
    
    print "total_jobs: ", total_job
    print "avg wait (min): ", avg_wait / 60
    print "avg. utility weighted wait (min): ",  avg_utility_wait / 60
    print "proportion of top job: ", float(total_top_job) / total_job
    print "proportion of backfilled job: ", float(total_backfill_job) / total_job
    print "wwait:", avg_utility_wait / 60, round(float(total_backfill_job) / total_job, 3), round(float(total_top_job) / total_job, 3)
 
def show_slowdown(job_dict):
    '''calculate slowdown'''
    value_list = []
    total = 0.0
    for spec in job_dict.itervalues():
        temp1 = float(spec["start"]) - float(spec["qtime"])
        temp2 = float(spec["end"]) - float(spec["start"])
        temp = (temp1 + temp2) / temp2
        total += temp
        value_list.append(round(temp, 1))
    
    average = round(total/float(len(value_list)), 2)
    
    value_list.sort()
    index = int(len(value_list) * 0.99)
    avg_99 = round(sum(value_list[0:index]) / len(value_list[0:index]), 2)
      
    maximum = value_list[len(value_list) - 1]
    median = value_list[len(value_list) / 2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]
    
    if not opts.test:
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % \
    	(average, avg_99, maximum, percentile_99, percentile_90, percentile_80, median, minimum)
    else:
        print average
        print avg_99
        print maximum
        print percentile_99
        print percentile_90
        print percentile_80
        print median
        print minimum
        print "\r"

def show_all_slowdown(dictionary):
    
    print "Bounded slowdown:"
    print_header()
    print "\nAll\t",
    show_slowdown(dictionary)
    
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_slowdown(s_dict)
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_slowdown(vs_dict)
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_slowdown(l_dict)
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_slowdown(vl_dict)
    print '\n' 
   
def show_slowdown_alt(job_dict):
    '''calculate slowdown'''
    value_list = []
    total = 0.0
    for spec in job_dict.itervalues():
        temp1 = float(spec["start"]) - float(spec["qtime"])
        temp2 = float(spec["end"]) - float(spec["start"])
        temp = (temp1) / temp2
        total += temp
        value_list.append(round(temp, 1))
    
    average = round(total/float(len(value_list)), 2)
    value_list.sort()
    index = int(len(value_list) * 0.99)
    avg_99 = round(sum(value_list[0:index]) / len(value_list[0:index]), 2)  
    maximum = value_list[len(value_list)-1]
    median = value_list[len(value_list)/2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]

    print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" \
     % (average, avg_99, maximum, percentile_99, \
    percentile_90, percentile_80, median, minimum)
      
def show_all_slowdown_alt(dictionary):
    print "Slowdown alternate:"
    print_header()
    print "\nAll\t",
    show_slowdown_alt(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_slowdown_alt(s_dict)
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_slowdown_alt(vs_dict)
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_slowdown_alt(l_dict)
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_slowdown_alt(vl_dict)
    print '\r'
 
def show_uwait(job_dict):
    '''calculate unitless wait'''
    value_list = []
    total = 0.0
    for spec in job_dict.itervalues():
        wait = float(spec["start"]) - float(spec["qtime"])
        walltime_sec = 60 * float(spec['walltime'])
        uwait = wait / walltime_sec
        total += uwait
        value_list.append(round(uwait, 1))
    
    average = round(total/float(len(value_list)), 2)
    value_list.sort()
    index = int(len(value_list) * 0.99)
    avg_99 = round(sum(value_list[0:index]) / len(value_list[0:index]), 2)  
    maximum = value_list[len(value_list)-1]
    median = value_list[len(value_list)/2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]
    
    if not opts.test:
        print "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % \
		(average, avg_99, maximum, percentile_99, percentile_90, percentile_80, median, minimum)
    else:
        print average
        print avg_99
        print maximum
        print percentile_99
        print percentile_90
        print percentile_80
        print median
        print minimum
        print "\r"
        
def show_all_uwait(dictionary):
    print "Uwait:"
    print_header()
    print "\nAll\t",
    show_uwait(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_uwait(s_dict)
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_uwait(vs_dict)
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_uwait(l_dict)
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_uwait(vl_dict)
    print '\r'
 
def calculate_sys_util(job_dict, total_sec):
    '''calculate sys util'''

    busy_node_sec = 0
    for spec in job_dict.itervalues():
        runtime = float(spec["end"]) - float(spec["start"])
        host = spec["exec_host"]
        if host[0] == 'A': #intrepid
            nodes = int(host.split("-")[-1])
            total_nodes = 40960
        else:
            nodes = int(spec['nodes'])
            total_nodes = 100
        node_sec = nodes * runtime
        busy_node_sec += node_sec
        
    sysutil = busy_node_sec / (total_sec * total_nodes)
    return sysutil
    

def show_sys_util(job_dict, total_sec):
    """ print sys util"""
    sysutil = calculate_sys_util(job_dict, total_sec)
    print "\nsystem utilization_rate = ", sysutil
    print "makes span (min):", total_sec / 3600
    print '\n'
    

def loss_of_capacity(job_dict):
    """ Show loss of capacity. Two sub fuction is used: 
    get_idle_midplanes(), job_waiting()  """
    event_times = []
    for val in job_dict.itervalues():
        event_times.append(float(val["qtime"]))
    event_times.sort()
    # previous code may merge into parse part.
    total_wasted = 0
    wasted_node_hour = 0
    for i in range(1, len(event_times)):
        for val in job_dict.values():
            if (if_job_waiting(event_times[i])):
                wasted_node_hour = get_idle_midplanes(event_times[i]) * \
                512 * (event_times[i] - event_times[i-1]) 
            else:
                wasted_node_hour = 0
        total_wasted += wasted_node_hour
    loss_of_cap = total_wasted*1.0 / (80.0 * 512 * \
                  (float(event_times[len(event_times)-1]) - \
                  float(event_times[0])))
    print "loss of capacity = ", loss_of_cap
    print "\n"

def get_idle_midplanes(time):
    """ return idle midplane number """
    midplanes = 80
    for i in range(0, len(rec_list)):
        if rec_list[i].get_3 < time and time < rec_list[i].get_4:
            midplanes -= (rec_list[i].get_1 - rec_list[i].get_2)
            print rec_list[i].get_1 - rec_list[i].get_2
    return midplanes
 
def if_job_waiting(time):
    """ return if exist a waiting job at a specific time """
    flag = False 
    for val in job_dict.itervalues():
        if float(val["qtime"]) < time and time < float(val["start"]):
            flag = True
    return flag
    
def show_cosched_metrics(job_dict, total_sec):
        '''calculate coscheduling metrics.'''
        total_hold_time = 0
        total_hold_job = 0
        total_overhead_time = 0
        total_overhead_job = 0
        wasted_node_hour = 0
        hold_list = []
        overhead_list = []

        total_nodes = 1

        for spec in job_dict.itervalues():
                holding = float(spec["hold"])
                overhead = float(spec.get("overhead", 0))
                if holding > 0:
                        total_hold_time += holding / 60
                        total_hold_job += 1
                        hold_list.append(holding / 60)

                        host = spec["exec_host"]
                        if host[0] == 'A': #intrepid
                                nodes = int(host.split("-")[-1])
                                total_nodes = 40960
                        elif host[0] == 'n':
                                nodes = len(host.split(':'))
                                total_nodes = 100
                        wasted_node_hour += (nodes * holding) / 3600

                if overhead > 0:
                        total_overhead_time += overhead / 60
                        total_overhead_job += 1
                        overhead_list.append(overhead / 60)
                        
        waisted_sys_util = wasted_node_hour / (total_sec * total_nodes / 3600)

        if total_hold_job > 0:
                hold_list.sort()
                print "total holding job:", total_hold_job
                print "average holding time (min):", total_hold_time / total_hold_job
                print "median holding time (min):", hold_list[total_hold_job/2]
                print "maximum holding time (min):", max(hold_list)
                print "total waisted node-hour:", wasted_node_hour
                print "total waisted sysutil:", waisted_sys_util

        if total_overhead_job > 0:
                overhead_list.sort()
                print "total sync-up job:", total_overhead_job
                print "average overhead time (min):", total_overhead_time / total_overhead_job
                print "median overhead time (min):", overhead_list[total_overhead_job/2]
                print "maximum overhead time (min):", max(overhead_list)

        
if __name__ == "__main__":
    p = OptionParser()
    p.add_option("-l", dest = "logfile", type = "string", 
                    help = "path of log file (required)")
    p.add_option("-a", "--alloc", dest = "alloc", \
		    action = "store_true", \
		    default = False, \
		    help="plot bars represent for individual jobs ")
    p.add_option("-j", "--jobs", dest = "jobs", \
		    action = "store_true", \
		    default = False, \
		    help = "show number of waiting & running jobs")
    p.add_option("--wj", dest = "waiting_jobs", \
		    action = "store_true", \
                    default = False, \
                    help = "show waiting jobs")
    p.add_option("--rj", dest = "running_jobs", \
		    action = "store_true", \
                    default = False, \
                    help = "show running jobs")
    p.add_option("-n", "--nodes", dest = "nodes", \
		    action = "store_true", \
		    default = False, \
                    help = "show number of waiting $ running nodes")
    p.add_option("--wn", dest = "waiting_nodes", \
		    action = "store_true", \
                    default = False, \
                    help = "show busy nodes")
    p.add_option("--rn", dest = "running_nodes", \
		    action = "store_true", \
                    default = False, \
                    help = "show requested jobs")
    p.add_option("-r", dest = "response", action = "store_true", \
		    default = False, \
                    help = "print response time to terminal")
    p.add_option("-c", dest = "cosched", action = "store_true", \
		    default = False, \
                    help = "print coscheduling metrics")
    p.add_option("-m", "--metrics", action = "store_true", \
	            default = False, \
		    help = "print statistics of all metrics")    
    p.add_option("-b", dest = "slowdown", action = "store_true", \
		    default = False, \
                    help = "print bounded slowdown to terminal")
    p.add_option("--happy", dest = "happy", action = "store_true", \
		    default = False, \
		    help = "print the number of happy job")
    p.add_option("-w", dest = "wait", action = "store_true", \
		    default = False, \
                    help = "print wait time to terminal")
    p.add_option("-u", dest = "uwait", action = "store_true", \
                    default = False, \
                    help = "print unitless wait (waittime/walltime) ")
    p.add_option("-o", dest = "savefile", default = "schedshow", \
                    help = "feature string of the output files")
    p.add_option("-s", dest = "show", action = "store_true", \
		    default = False,
                    help = "show plot on the screen")
    p.add_option("--loss", dest = "loss_of_cap", \
		    action = "store_true", \
                    default = False, help = "show loss_of_cap")
    p.add_option("--alt", dest = "alt", type = "string", \
                    help = "write log in alternative form. A filename needed")
    p.add_option("--util", dest = "util_alt", type = "string", \
                    help = "write new log accroding to new util rate")
    p.add_option("-A", "--All", dest = "run_all", action = "store_true", \
                    default = False,  help = "run all functions")
    p.add_option("-t", "--test", dest = "test", action = "store_true", \
                    default = False,  help = "test option, adaptive to user needs")
    p.add_option("-d", "--debuglog", dest = "debuglog", action="store_true", \
					default = False,  help = "parse in debug log path to get extra info")

    (opts, args) = p.parse_args()
    
    if not opts.logfile:
        print "please specify path of log file"
        p.print_help()
        exit()
          
    if opts.run_all:
        opts.alloc = opts.jobs = opts.nodes = opts.response = \
        opts.slowdown = opts.wait = opts.uwait = opts.happy = opts.loss_of_cap = True
        
    if opts.metrics and not opts.test:
        opts.response = opts.slowdown = opts.wait = opts.uwait = True
    if opts.jobs:
        opts.running_jobs = opts.waiting_jobs = True 
    if opts.nodes:
        opts.running_nodes = opts.waiting_nodes = True
    if opts.savefile:
        savefilename = opts.savefile
    else:
        savefilename = "schedshow"
        
    if opts.show:
        SHOW = True

    starttime_sec = time.time()
        
    (job_dict, first_submit, first_start, last_submit, last_end) = \
        parseLogFile(opts.logfile)
    
    print "Total number of jobs:", len(job_dict.keys())
    print "First submit: ", sec_to_date(first_submit)
    print "Last end: ", sec_to_date(last_end)
   
    show_size(job_dict)
    
    if opts.response:
        show_all_resp(job_dict)
    if opts.wait:
        show_all_wait(job_dict)
    if opts.slowdown:
        show_all_slowdown(job_dict)
        show_all_slowdown_alt(job_dict)
    if opts.uwait:
        show_all_uwait(job_dict)
    if opts.cosched:
        show_cosched_metrics(job_dict, last_end - first_submit)
    if opts.metrics:
        show_sys_util(job_dict, last_end - first_submit)
    if opts.loss_of_cap:
        loss_of_capacity(job_dict) 
    if opts.happy:
        count_happy_job(job_dict)
        
    if opts.debuglog:
        show_utility_wait(job_dict, opts.logfile)   
    
    if opts.test:
        show_wait(job_dict)
        show_slowdown(job_dict)
        show_uwait(job_dict)
        show_sys_util(job_dict, last_end - first_submit)

    if opts.alt:
        write_alt(job_dict, opts.alt)
    if opts.util_alt:
        write_util_alt(job_dict, last_end - first_submit, opts.util_alt)
#print color_bars
    if opts.alloc:
        draw_job_allocation(job_dict, first_submit, last_end, savefilename)
#print running & waiting jobs
    if opts.waiting_jobs:
        draw_waiting_jobs(job_dict, first_submit, last_end, savefilename)
    if opts.running_jobs:
        draw_running_jobs(job_dict, first_submit, last_end, savefilename) 
# print running & waiting nodes
    if opts.waiting_nodes:
        draw_waiting_nodes(job_dict, first_submit, last_end, savefilename)
    if opts.running_nodes:
        draw_running_nodes(job_dict, first_submit, last_end, savefilename) 

    endtime_sec = time.time()
    print "---Analysis and plotting are finished,", \
          "please check saved figures if any---"
    print "Tasks accomplished in %s seconds" \
		    % (int(endtime_sec - starttime_sec))
