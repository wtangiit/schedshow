#!/usr/bin/env python

import sys
import time
from datetime import datetime
from optparse import OptionParser
import optparse

__helpmsg__ = "Usage: "

def date_to_sec(fmtdate, dateformat = "%m/%d/%Y %H:%M:%S"):
    '''convert date into seconds'''
    t_tuple = time.strptime(fmtdate, dateformat)
    sec = time.mktime(t_tuple)
    return sec

def sec_to_date(sec, dateformat="%m/%d/%Y %H:%M:%S"):
    tmp = datetime.fromtimestamp(sec)
    fmtdate = tmp.strftime(dateformat)
    return fmtdate

def datetime_strptime (value, format):
    """Parse a datetime like datetime.strptime in Python >= 2.5"""
    return datetime(*time.strptime(value, format)[0:6])

class Option (optparse.Option):
    
    """An extended optparse option with cbank-specific types.
    
    Types:
    date -- parse a datetime from a variety of string formats
    """
    
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%y-%m-%d",
        "%y-%m-%d %H:%M:%S",
        "%y-%m-%d %H:%M",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%y",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%Y%m%d",
    ]
    
    def check_date (self, opt, value):
        """Parse a datetime from a variety of string formats."""
        for format in self.DATE_FORMATS:
            try:
                dt = datetime_strptime(value, format)
            except ValueError:
                continue
            else:
                # Python can't translate dates before 1900 to a string,
                # causing crashes when trying to build sql with them.
                if dt < datetime(1900, 1, 1):
                    raise optparse.OptionValueError(
                        "option %s: date must be after 1900: %s" % (opt, value))
                else:
                    return dt
        raise optparse.OptionValueError(
            "option %s: invalid date: %s" % (opt, value))
    
    TYPES = optparse.Option.TYPES + ( "date", )
    

    TYPE_CHECKER = optparse.Option.TYPE_CHECKER.copy()
    TYPE_CHECKER['date'] = check_date
              
def parseLine(line):
    '''parse a line into dictionary form:
     line_data[jobid:xxx, date:xxx, start_time:xxx, mjobidplane:xxx, etc.]
    '''
    line_data = {}
    first_parse = line.split(";")
    line_data["eventType"] = first_parse[1]  
    
    # EventTypes: Q - submitting time, S - starting time, E - ending time
    
    if line_data["eventType"] == "Q":
        line_data["submittime"] = first_parse[0]
    line_data["jobid"] = first_parse[2]
    substr = first_parse.pop()
    if len(substr) > 0:
        second_parse = substr.split(" ")
        for item in second_parse:
            tup = item.partition("=")
            if not line_data.has_key(tup[0]):
                line_data[tup[0]] = tup[2]
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
    submittime_date = sec_to_date(submittime_sec)
    temp['submittime'] = submittime_date
    start_date = temp['start']
    start_sec = date_to_sec(start_date, "%Y-%m-%d %H:%M:%S")
    temp['start'] = start_sec
    end_date = temp['end']
    end_sec = date_to_sec(end_date, "%Y-%m-%d %H:%M:%S")
    temp['end'] = end_sec

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
    max_end = 0
    for jobid, spec in raw_job_dict.iteritems():
        if spec.has_key("end") and spec.has_key("submittime"):
            qtime_sec = date_to_sec(spec['submittime'])
            if qtime_sec < min_qtime:
                min_qtime = qtime_sec
            if float(spec['start']) < min_start:
                min_start = float(spec['start'])
            if float(spec['end']) > max_end:
                max_end = float(spec['end'])
                
            spec['submittime'] = qtime_sec
            #exclude deleted jobs which runtime is 0
            if float(spec["end"]) - float(spec["start"]) <= 0:
                continue
            
#            format_walltime = spec.get('Resource_List.walltime')
#            spec['walltime'] = 0
#            if format_walltime:
#                segs = format_walltime.split(':')
#                spec['walltime'] = str(int(segs[0]) * 60 + int(segs[1]))
#            else:  #invalid job entry, discard
#                continue

            if spec.get('Resource_List.nodect'):
                spec['nodes'] = spec.get('Resource_List.nodect')
                if int(spec['nodes']) == 40960:
                    continue                    
            else:  #invalid job entry, discard
                continue
            
            job_dict[jobid] = spec 
    wlf.close()
                                     
    return job_dict, min_qtime, min_start, max_end

def tune_workload(specs, frac=1, anchor=0):
    '''tune workload heavier or lighter, and adjust the start time to anchor, specs should be sorted by submission time'''
  
    #calc intervals (the first job's interval=0, the i_th interval is sub_i - sub_{i-1}
    lastsubtime = 0
    for spec in specs:
        if (lastsubtime==0):
            interval = 0
        else:
            interval = spec['submittime'] - lastsubtime
        lastsubtime =  spec['submittime']
        spec['interval'] = interval
    
    #if anchor is specified, set the first job submission time to anchor
    if anchor:
        specs[0]['submittime'] = anchor
    else:
        pass
        
    last_newsubtime = specs[0].get('submittime')    
    for spec in specs:
        interval = spec['interval']
        newsubtime = last_newsubtime + frac * interval
        spec['submittime'] = newsubtime
        spec['interval'] = frac * interval
        last_newsubtime = newsubtime
        
def cut_workload(jobdict, starttime, endtime):
    '''output the job trace within the specified time window'''
    new_jobdict  ={}
    for key, val in jobdict.iteritems():
        qtime = val['submittime']
        if qtime > starttime and qtime < endtime:
            new_jobdict[key] = val
    return new_jobdict

def subtimecmp(spec1, spec2):
    return cmp(spec1.get('submittime'), spec2.get('submittime'))

def match_workload(jobdict1, jobdict2):
    '''return a new job dict, whose qtime matches jobdict1 and other attributes uses values in jobdict2'''
    
    specs1 = jobdict1.values()
    specs1.sort(subtimecmp)
        
    specs2 = jobdict2.values()
    specs2.sort(subtimecmp)
    
    if len(specs2) < len(specs1):
        return None
    
    i = 0
    new_joblist = []
    for spec in specs1:
        qtime = spec['submittime']
        new_qtime = qtime + 120
        new_spec = specs2[i]
        new_spec['submittime'] = new_qtime
        new_spec['qtime'] = sec_to_date(new_qtime, "%Y-%m-%d %H:%M:%S")
        
        #construct new "start" and "end" time, which don't make sense and are used only in calculating utilization rate
        runtime = float(new_spec['end']) - float(new_spec['start'])
        new_start = new_qtime
        new_end = new_start + runtime
        new_spec['start'] = sec_to_date(new_start, "%Y-%m-%d %H:%M:%S")
        new_spec['end'] = sec_to_date(new_end, "%Y-%m-%d %H:%M:%S")
        
        new_joblist.append(new_spec)
        i += 1
        
    if new_joblist:
        new_file = open("newfile.log", "w")
        for spec in new_joblist:
            line = ""
            for key, val in spec.iteritems():
                line += "%s=%s;" % (key, val)
            line += "\n"
            print line
            new_file.write(line)
        new_file.close()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

    
def tune_workload_by_runtime(jobdict, N, outputfile):
    '''tune the workload by multiple N on each job runtime'''
    
    specs = jobdict.values()
    specs.sort(subtimecmp)
        
    for spec in specs:
        #construct new "start" and "end" time, making runtime N times than the original 
        start = spec['start']
        if is_number(start):
            start = float(start)
            end = float(spec['end'])
            spec['start'] = sec_to_date(start, "%Y-%m-%d %H:%M:%S")
        else:
            start = date_to_sec(start)
            end = date_to_sec(spec['end'])
            
        if is_number(spec['qtime']):
            spec['qtime'] = sec_to_date(float(spec['qtime']), "%Y-%m-%d %H:%M:%S")
            
        if not is_number(spec['Resource_List.walltime']):
            format_walltime = spec.get('Resource_List.walltime')
            segs = format_walltime.split(':')
            walltime_sec = str(int(segs[0]) * 3600 + int(segs[1]) * 60 + int(segs[2]))
            spec['Resource_List.walltime'] = walltime_sec
            
        runtime = end - start
        new_end = start + runtime * N
        spec['end'] = sec_to_date(new_end, "%Y-%m-%d %H:%M:%S")
                
    if outputfile:
        new_file = open(outputfile, "w")
    else:
        new_file = open("newfile_tuned.log", "w")
    for spec in specs:
        line = ""
        for key, val in spec.iteritems():
            line += "%s=%s;" % (key, val)
        line += "\n"
        print line
        new_file.write(line)
    new_file.close()
        
    
def write_new_mached_workload(jobdict1, jobdict2):
    new_joblist = match_workload(jobdict1, jobdict2)
    if new_joblist:
        new_file = open("newfile_mached.log", "w")
        line = ""
        for spec in new_joblist:
            for key, val in spec.iteritems():
                line += "%s=%s;" % (key, val)
            line += "\n"
            new_file.write(line)
        new_file.close()
        
            
if __name__ == '__main__':    
    if len(sys.argv) == 1:
        print __helpmsg__
        sys.exit(1)
        
    p = OptionParser()
    p.add_option("-j", dest = "bgjob", type = "string", 
                    help = "path of log file (required)")
    p.add_option("-c", dest = "cjob", type = "string", 
                    help = "path of log file (required)")
    p.add_option("-m", "--match", dest = "match", \
            action = "store_true", \
            default = False, \
            help="plot bars represent for individual jobs ")
    p.add_option(Option("-S", "--Start",
        dest="bg_trace_start", type="date",
        help="bg job submission times (in job trace) should be after 12.01am on this date.\
        By default it equals to the first job submission time in job trace 'bgjob'"))
    p.add_option(Option("-E", "--End",
        dest="bg_trace_end", type="date",
        help="bg job submission time (in job trace) should be prior to 12.01am on this date \
        By default it equals to the last job submission time in job trace 'bgjob'"))
    p.add_option(Option("-s", "--start",
        dest="c_trace_start", type="date",
        help="cluster job submission times (in job trace) should be after 12.01am on this date. \
        By default it equals to the first job submission time in job trace 'cjob'"))
    p.add_option(Option("-e", "--end",
        dest="c_trace_end", type="date",
        help="cluster job submission time (in job trace) should be prior to 12.01am on this date \
        By default it equals to the last job submission time in job trace 'cjob'"))
    p.add_option(Option("-p", "--prolong",
        dest="prolong", type="float",
        help="generate a new jobtrace which prolong the runtime of each job by 'prolong' times compared with the original job trace"))
    p.add_option("-o", "--output", dest="outputlog", type="string",
        help="output file name")
    
    
    opts, args = p.parse_args()
    
    bgstart = bgend = cstart = cend = 0
                
    if opts.bg_trace_start:
        print "bg trace start date=", opts.bg_trace_start
        t_tuple = time.strptime(str(opts.bg_trace_start), "%Y-%m-%d %H:%M:%S")
        opts.bg_trace_start = time.mktime(t_tuple)
  
    if opts.bg_trace_end:
        print "bg trace end date=", opts.bg_trace_end
        t_tuple = time.strptime(str(opts.bg_trace_end), "%Y-%m-%d %H:%M:%S")
        opts.bg_trace_end = time.mktime(t_tuple)

    if opts.c_trace_start:
        print "cluster trace start date=", opts.c_trace_start
        t_tuple = time.strptime(str(opts.c_trace_start), "%Y-%m-%d %H:%M:%S")
        opts.c_trace_start = time.mktime(t_tuple)
        
    if opts.c_trace_end:
        print "cluster trace end date=", opts.c_trace_end
        t_tuple = time.strptime(str(opts.c_trace_end), "%Y-%m-%d %H:%M:%S")
        opts.c_trace_end = time.mktime(t_tuple)

    if not opts.bgjob and not opts.cjob:
        print "please specify path of log file"
        p.print_help()
        exit()
        
    if opts.bgjob:
        (job_dict_i, first_submit_i, first_start_i, last_end_i) = parseLogFile(opts.bgjob)
        if opts.bg_trace_start and opts.bg_trace_end:
            job_dict_i = cut_workload(job_dict_i, opts.bg_trace_start, opts.bg_trace_end)
        print "total_job_i=", len(job_dict_i.keys())
        
    if opts.cjob:
        (job_dict_c, first_submit_c, first_start_c, last_end_c) = parseLogFile(opts.cjob)
        if opts.c_trace_start and opts.c_trace_end:
            job_dict_c = cut_workload(job_dict_c, opts.c_trace_start, opts.c_trace_end)
        print "total_job_c=", len(job_dict_c.keys())
        
    if opts.match:
        match_workload(job_dict_i, job_dict_c)
        
    if opts.prolong:
        tune_workload_by_runtime(job_dict_c, opts.prolong, opts.outputlog)
      
    