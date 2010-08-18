#!/usr/bin/env python
'''Schedshow is a integrated program which will analyse the out \
		put file from Qsim. This program is written in python, \
		which utilizes an external library -- "matplotlib". '''

import time
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
    temp_color = []
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
        line_data["submitTime"] = first_parse[0]
    line_data["jobid"] = first_parse[2]
    substr = first_parse.pop()
    if len(substr) > 0:
        second_parse = substr.split(" ")
        for item in second_parse:
            tup = item.partition("=")
            if not line_data.has_key(tup[0]):
                line_data[tup[0]] = tup[2]
    return line_data                                      

def parseLogFile(filename):
    '''parse the whole work load file'''
    line_data = {}
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
                
    job_dict = {}
    min_qtime = sys.maxint
    min_start = sys.maxint
    max_end = 0
    for jobid, spec in raw_job_dict.iteritems():
        if spec.has_key("end") and spec.has_key("submitTime"):
            qtime_sec = date_to_sec(spec['submitTime'])
            if qtime_sec < min_qtime:
                min_qtime = qtime_sec
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
                walltime_minuntes = int(segs[0]) * 60 + int(segs[1])
                spec['walltime'] = str(int(segs[0]) * 60 + int(segs[1]))
            else:  #invalid job entry, discard
                continue
            
            job_dict[jobid] = spec 
    wlf.close()
                                     
    return job_dict, min_qtime, min_start, max_end

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
        qtime = "qtime=" + value["qtime"]
        start = "start=" + value["start"]
        end = "end=" + value["end"]
        host = "exec_host=" + value["exec_host"]
        nodes = "nodes=" + value["Resource_List.nodect"]
        walltime ="walltime=" + value["Resource_List.walltime"]
        #nodes = "nodes=" + val[]
        line = "%s;%s;%s;%s;%s;%s;%s\n" \
			% (jobid, qtime, start, end, host, \
            nodes, walltime)
        FILE.write(line)
    FILE.close() 

def write_util_alt(job_dict, total_sec, util = None):
    filename = str(util) + "-util-alt.log"
    FILE = open(filename, "w")
    fraction = calculate_sys_util(job_dict, total_sec) / float(util)
    print "fraction is: ", fraction
    sorted_value_list = sort_dict_qtime(job_dict)
    alt_value_list = tune_workload(sorted_value_list, fraction)
    for value in alt_value_list: 
        jobid = "jobid=" + value["jobid"]
        qtime = "qtime=" + str(value["qtime"])
        start = "start=" + value["start"]
        end = "end=" + value["end"]
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
    for k, v in job_dict.iteritems():
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
        savefile += "-alloc.eps"
    else:
        savefile = "schedshow-alloc.eps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
    
def draw_running_jobs(job_dict, min_start, max_end, savefile=None):
    '''plot number of waiting jobs and running jobs'''
    print "plotting: running jobs"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("running jobs")
    inteval = (max_end-min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    job_numbers = []
    maxjob = 0
    for i in range(0, 2000):
        job_number = 0
        for k, v in job_dict.iteritems():
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
        savefile += "-jobs-running.eps"
    else:
        savefile = "schedshow-jobs-running.eps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()

def draw_waiting_jobs(job_dict, min_start, max_end, savefile=None):     
    """ draw waiting jobs""" 
    print "plotting: waiting jobs"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("waiting jobs")
    inteval = (max_end-min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    wait_numbers = []
    maxwait = 0
    for i in range(0, 2000):
        wait_number = 0
        for k, spec in job_dict.iteritems():
            if float(spec["qtime"]) < timepoint \
			    and timepoint < float(spec["start"]):
                wait_number = wait_number + 1
        if wait_number > maxwait:
            maxwait = wait_number
        wait_numbers.append(wait_number)
        timepoints.append(timepoint)
        timepoint = inteval + timepoint
    ax.plot(timepoints, wait_numbers, color = 'red')
    ax.set_ylim(0, maxwait+maxwait*0.1, color = 'red')

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
        savefile += "-jobs-waiting.eps"
    else:
        savefile = "schedshow-jobs-waiting.eps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()

def draw_running_nodes(job_dict, min_start, max_end, savefile = None):
    '''draw number of busy nodes'''
    print "plotting: system utilization-busy nodes"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.title("running nodes")
    inteval = (max_end - min_start) / 2000.0   # this may modified 
    timepoint = min_start
    timepoints = []
    job_nodes = []
    maxjobnode = 0
    for i in range(0, 2000):
        job_node = 0
        for k, spec in job_dict.iteritems():
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
        savefile += "-sysutil-busy.eps"
    else:
        savefile = "schedshow-sysutil-busy.eps"
    
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
        for k, spec in job_dict.iteritems():
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
        savefile += "-sysutil-requested.eps"
    else:
        savefile = "schedshow-sysutil-requested.eps"
    
    plt.savefig(savefile)
    
    if SHOW:
        plt.show()
   
 
   
metric_header = [" ", "Avg", "Max", "99th", "90th", "80th",\
      "Median", "Min"]

def print_header():
    for item in metric_header:
        print item, '\t',

happy_dict = {} #temp

def happy_job(job_dict):
    '''show if the job is a happy job or not'''
    count = 0
    for k, val in job_dict.iteritems():
        jobid = val["jobid"]
        qtime = float(val["qtime"])
        stime = float(val["start"])
        size1 = int(val["exec_host"].split("-")[-1])
        prrty1 = (1/float(val["walltime"])) ** 3 * float(size1)
        end = []
        for k, val in job_dict.iteritems():
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
	          
# some globle arguments

vs_dict = {}
s_dict = {}
l_dict = {}
vl_dict = {}

def show_size(job_dict):
    """ show all metrics"""
    for k, val in job_dict.iteritems():
        jobid = val["jobid"]
        host = val["exec_host"].rsplit("-")
        if len(host) == 4:
            size = host[3]
        else:
            size = host[2]
        if size == "512":
            vs_dict[jobid] = val
        elif "1024" <= size and size <= "2048":
            s_dict[jobid] = val
        elif "4096" <= size and size <= "8192":
            l_dict[jobid] = val
        elif "16384" <= size and size <= "32768":
            vl_dict[jobid] = val
    #print "Job category number"
    print "VS: %s  S: %s  L: %s  VL: %s\n" % (len(vs_dict.keys()), \
          len(s_dict.keys()), len(l_dict.keys()), \
          len(vl_dict.keys()) )

def show_resp(job_dict):
    '''calculate response time'''
    value_list = []
    
    total = 0.0
    for k, spec in job_dict.iteritems():
        temp  = (float(spec["end"]) - float(spec["qtime"])) / 60
        total += temp
        value_list.append(round(temp, 1))
    
    average = round(total/float(len(value_list)), 2)

    value_list.sort()
    maximum = value_list[len(value_list) - 1]
    median = value_list[len(value_list) / 2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]

    print "%s\t%s\t%s\t%s\t%s\t%s\t%s" \
     % (average, maximum, percentile_99, \
	percentile_90, percentile_80, median, minimum)

def show_all_resp(dictionary):
    print "Resp Time:"
    print_header()
    print "\nAll\t",
    show_resp(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_resp(s_dict)
    else:
        print "No Very Small jobs"
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_resp(vs_dict)
    else:
        print "No Small jobs"
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_resp(l_dict)
    else:
        print "No Large jobs"
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_resp(vl_dict)
    else:
        print "No Very Large jobs\n"
    
def show_wait(job_dict):
    '''calculate waiting time'''
    value_list = []
    total = 0.0
    for k, spec in job_dict.iteritems():
        temp = (float(spec["start"]) - float(spec["qtime"])) / 60
        total += temp
        value_list.append(round(temp, 1))

    average = round(total/float(len(value_list)), 2)
    
    value_list.sort()
    maximum = value_list[len(value_list) - 1]
    median = value_list[len(value_list) / 2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]

    print "%s\t%s\t%s\t%s\t%s\t%s\t%s" \
	 % (average, maximum, percentile_99, \
	percentile_90, percentile_80, median, minimum)

def show_all_wait(dictionary):
    print "Wait time:" 
    print_header()
    print "\nAll\t",
    show_wait(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_wait(s_dict)
    else:
        print "No Very Small jobs"
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_wait(vs_dict)
    else:
        print "No Small jobs"
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_wait(l_dict)
    else:
        print "No Large jobs"
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_wait(vl_dict)
    else:
        print "No Very Large jobs\n"
 
def show_slowdown(job_dict):
    '''calculate slowdown'''
    value_list = []
    total = 0.0
    for k, spec in job_dict.iteritems():
        temp1 = float(spec["start"]) - float(spec["qtime"])
        temp2 = float(spec["end"]) - float(spec["start"])
        temp = (temp1 + temp2) / temp2
        total += temp
        value_list.append(round(temp, 1))
    
    for item in value_list:
        total += item
    average = round(total/float(len(value_list)), 2)
    value_list.sort()
    maximum = value_list[len(value_list) - 1]
    median = value_list[len(value_list) / 2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]

    print "%s\t%s\t%s\t%s\t%s\t%s\t%s" \
	 % (average, maximum, percentile_99, \
	percentile_90, percentile_80, median, minimum)

def show_all_slowdown(dictionary):
    
    print "Bounded slowdown:"
    print_header()
    print "\nAll\t",
    if len(s_dict.keys()) != 0:
        show_slowdown(dictionary)
        print "VS\t",
        show_slowdown(s_dict)
    else:
        print "No Very Small jobs"
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_slowdown(vs_dict)
    else:
        print "No Small jobs"
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_slowdown(l_dict)
    else:
        print "No Large jobs"
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_slowdown(vl_dict)
    else:
        print "No Very Large jobs\n"
 
   
def show_slowdown_alt(job_dict):
    '''calculate slowdown'''
    value_list = []
    total = 0.0
    for k, spec in job_dict.iteritems():
        temp1 = float(spec["start"]) - float(spec["qtime"])
        temp2 = float(spec["end"]) - float(spec["start"])
        temp = (temp1) / temp2
        total += temp
        value_list.append(round(temp, 1))
    
    for item in value_list:
        total += item
    average = round(total/float(len(value_list)), 2)
    value_list.sort()
    maximum = value_list[len(value_list)-1]
    median = value_list[len(value_list)/2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]

    print "%s\t%s\t%s\t%s\t%s\t%s\t%s" \
	 % (average, maximum, percentile_99, \
	percentile_90, percentile_80, median, minimum)
  
def show_all_slowdown_alt(dictionary):
    print "Slowdown alternate:"
    print_header()
    print "\nAll\t",
    show_slowdown_alt(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_slowdown_alt(s_dict)
    else:
        print "No Very Small jobs"
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_slowdown_alt(vs_dict)
    else:
        print "No Small jobs"
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_slowdown_alt(l_dict)
    else:
        print "No Large jobs"
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_slowdown_alt(vl_dict)
    else:
        print "No Very Large jobs\n"
 
def show_uwait(job_dict):
    '''calculate unitless wait'''
    value_list = []
    total = 0.0
    for k, spec in job_dict.iteritems():
        wait = float(spec["start"]) - float(spec["qtime"])
        walltime_sec = 60 * float(spec['walltime'])
        uwait = wait / walltime_sec
        total += uwait
        value_list.append(round(uwait, 1))
    
    average = round(total/float(len(value_list)), 2)
    value_list.sort()
    maximum = value_list[len(value_list)-1]
    median = value_list[len(value_list)/2]
    index = int(len(value_list) * 0.99)
    percentile_99 = value_list[index]
    index = int(len(value_list) * 0.90)
    percentile_90 = value_list[index]
    index = int(len(value_list) * 0.80)
    percentile_80 = value_list[index]
    minimum = value_list[0]
    
    print "%s\t%s\t%s\t%s\t%s\t%s\t%s" % \
	 (average, maximum, percentile_99, \
	percentile_90, percentile_80, median, minimum)
    
def show_all_uwait(dictionary):
    print "Uwait:"
    print_header()
    print "\nAll\t",
    show_uwait(dictionary)
    if len(s_dict.keys()) != 0:
        print "VS\t",
        show_uwait(s_dict)
    else:
        print "No Very Small jobs"
    if len(vs_dict.keys()) != 0:
        print "S\t",
        show_uwait(vs_dict)
    else:
        print "No Small jobs"
    if len(l_dict.keys()) != 0:
        print "L\t",
        show_uwait(l_dict)
    else:
        print "No Large jobs"
    if len(vl_dict.keys()) != 0:
        print "VL\t",
        show_uwait(vl_dict)
    else:
        print "No Very Large jobs\n"
 
def calculate_sys_util(job_dict, total_sec):
    '''calculate sys util'''
    value_list = []
    total = 0.0
    busy_node_sec = 0
    for k, spec in job_dict.iteritems():
        runtime = float(spec["end"]) - float(spec["start"])
        host = spec["exec_host"]
        if host[0] == 'A': #intrepid
            nodes = int(host.split("-")[-1])
            total_nodes = 40960
        elif host[0] == 'n':
            nodes = len(host.split(':'))
            total_nodes = 100
        node_sec = nodes * runtime
        #print "jobid=%s, nodes=%s, runtime=%s, 
	#location=%s" % (spec['jobid'], nodes, 
	#runtime, spec['exec_host'])
        busy_node_sec += node_sec
        
    sysutil = busy_node_sec / (total_sec * total_nodes)
    return sysutil
    

def show_sys_util(job_dict, total_sec):
    """ print sys util"""
    sysutil = calculate_sys_util(job_dict, total_sec)
    print "\nsystem utilization rate = ", sysutil
    print '\n'
    

def loss_of_capacity(job_dict):
    """ Show loss of capacity. Two sub fuction is used: 
    get_idle_midplanes(), job_waiting()  """
    event_times = []
    for key, val in job_dict.iteritems():
        if val["eventType"] == "Q" or val["eventType"] == "E":
            event_times.append(date_to_sec(val["submitTime"]))
    event_times.sort()
    # previous code may merge into parse part.
    total_wasted = 0
    wasted_node_hour = 0
    for i in range(1, len(event_times)):
        for key, val in job_dict.iteritems():
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
            midplannes -= (rec_list[i].get_1 - rec_list[i].get_2)
            print rec_list[i].get_1 - rec_list[i].get_2
    return midplanes
 
def if_job_waiting(time):
    """ return if exist a waiting job at a specific time """
    flag = False 
    for key, val in job_dict.iteritems():
        if float(val["qtime"]) < time and time < float(val["start"]):
            flag = True
    return flag
    
def show_cosched_metrics(job_dict, total_sec):
        '''calculate coscheduling metrics.'''
        total_hold_time = 0
        total_hold_job = 0
        total_yield_time = 0
        total_yield_job = 0
        wasted_node_hour = 0
        hold_list = []
        yield_list = []
	
        total_nodes = 1
	
        for k, spec in job_dict.iteritems():
                holding = float(spec["hold"])
                yielding = float(spec.get("yield", 0))
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
						 
                if yielding > 0:
                        total_yield_time += yielding / 60
                        total_yield_job += 1
                        yield_list.append(yielding / 60)
	
        waisted_sys_util = wasted_node_hour / (total_sec * total_nodes / 3600)
	
        if total_hold_job > 0:
                hold_list.sort()
                print "total holding job:", total_hold_job
                print "average holding time (min):", \
				total_hold_time / total_hold_job
                print "median holding time (min):", \
				hold_list[total_hold_job/2]
                print "maximum holding time (min):", max(hold_list)
                print "total waisted node-hour:", wasted_node_hour
                print "total waisted sysutil:", waisted_sys_util
	
        if total_yield_job > 0:
                yield_list.sort()
                total_yield_time /= 60
                print "total yield job:", total_yield_job
                print "average yield time (min):", \
				total_yield_time / total_yield_job
                print "median yield time (min):", \
				yield_list[total_yield_job/2]
                print "maximum yield time (min):", max(yield_list)

        
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

    (opts, args) = p.parse_args()
    
    if not opts.logfile:
        print "please specify path of log file"
        p.print_help()
        exit()
        
    if opts.run_all:
        opts.alloc = opts.jobs = opts.nodes = opts.response = \
        opts.slowdown = opts.wait = opts.uwait = opts.happy = \
	opts.loss_of_cap = True
        
    if opts.metrics:
        opts.response = opts.slowdown = opts.wait = \
        opts.uwait = True
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
        
    (job_dict, first_submit, first_start, last_end) = \
        parseLogFile(opts.logfile)
    
    print "Total number of jobs:", len(job_dict.keys())
   
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
	happy_job(job_dict)

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

