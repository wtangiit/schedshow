#!/usr/bin/env python
'''Schedshow is a integrated program which will analyse the out \
        put file from Qsim. This program is written in python, \
        which utilizes an external library -- "matplotlib". '''

import time
import sys

__helpmsg__ = "Usage: statplot2.py <log-file-1> [<log-file-2> <log-file-3> ... ...]"

WARMUPJOBS = 0
SLOWDOWN_BOUND = 10
metricdict = {}

metric_list = ['wait_avg', 'wait_avg99pct', 'wait_max', 'wait_99pct', 'wait_80pct', 'space',
             'slowdown_avg', 'slowdown_avg99pct', 'slowdown_max', 'slowdown_99pct', 'slowdown_80pct', 'space',
             'uwait_avg', 'uwait_avg99pct', 'uwait_max', 'uwait_99pct', 'uwait_80pct',
             ]

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
                spec['walltime'] = str(int(segs[0]) * 60 + int(segs[1]))
            else:  #invalid job entry, discard
                continue
            
            job_dict[jobid] = spec 
    wlf.close()
                                     
    return job_dict

def make_statistic(bins):
    
    wait_dict = {}
    slowdown_dict = {}
    uwait_dict = {}
    
    statistic = {}
    for metric in metric_list:
        statistic[metric] = []
    statistic['space'] = "\n"
    
    for k in bins:
        wait_list = []
        slowdown_list = []
        uwait_list = []
        
        for j in bins[k]:
            #all in second
            start = float(j['start'])
            qtime = float(j['qtime'])
            end = float(j['end'])
            walltime = float(j['walltime']) * 60
            
            wait = (start - qtime) / 60
            slowdown = (end - qtime) / (end - start)
            uwait = (start - qtime) / walltime
            
            wait_list.append(wait)
            slowdown_list.append(slowdown)
            uwait_list.append(uwait)
        
        wait_dict[k] = wait_list
        slowdown_dict[k] = slowdown_list
        uwait_dict[k] = uwait_list
        
        total = len(wait_list)
        
        #wait
        statistic['wait_avg'].append(sum(wait_list) / total)
        wait_list.sort()
        index = int(len(wait_list) * 0.99)
        statistic['wait_avg99pct'].append(sum(wait_list[0:index]) / len(wait_list[0:index]))
        statistic['wait_max'].append(wait_list[-1])
        statistic['wait_99pct'].append(wait_list[index])
        index = int(len(wait_list) * 0.80)
        statistic['wait_80pct'].append(wait_list[index])
        
        #slowdown
        statistic['slowdown_avg'].append(sum(slowdown_list) / total)
        slowdown_list.sort()
        index = int(len(slowdown_list) * 0.99)
        statistic['slowdown_avg99pct'].append(sum(slowdown_list[0:index]) / len(slowdown_list[0:index]))
        statistic['slowdown_max'].append(slowdown_list[-1])
        statistic['slowdown_99pct'].append(slowdown_list[index])
        index = int(len(wait_list) * 0.80)
        statistic['slowdown_80pct'].append(slowdown_list[index])
        
        #uwait
        statistic['uwait_avg'].append(sum(uwait_list) / total)
        uwait_list.sort()
        index = int(len(uwait_list) * 0.99)
        statistic['uwait_avg99pct'].append(sum(uwait_list[0:index]) / len(uwait_list[0:index]))
        statistic['uwait_max'].append(uwait_list[-1])
        statistic['uwait_99pct'].append(uwait_list[index])
        index = int(len(uwait_list) * 0.80)
        statistic['uwait_80pct'].append(uwait_list[index])
        
    print_statistic(statistic)
    
def print_statistic(statistic):
    for metric in metric_list:
        if metric == "space":
            print "\n"
        else:
            avg = round(sum(statistic[metric]) / len(statistic[metric]), 2)
            minimum = round(min(statistic[metric]), 2)
            maximum = round(max(statistic[metric]), 2)
            print "%s, %s, %s, %s" % (metric, avg, minimum, maximum)    

if __name__ == '__main__':    
    if len(sys.argv) == 1:
        print __helpmsg__
        sys.exit(1)
        
    bins = {}
    lognames = []
    
    for i in range(1, len(sys.argv)):
        lognames.append(sys.argv[i])
        
    for logpath in lognames:
        jobdict = parseLogFile(logpath)
        if not bins.has_key(logpath):
            bins[logpath] = []
        if jobdict:
            for key in jobdict.keys():
                bins[logpath].append(jobdict[key])
        metricdict[logpath] = [0,0,0,0,0,0]
        print "logfile=", logpath, " number of jobs=", len(bins[logpath])
    print "--------------------------"        
    
    make_statistic(bins)
        