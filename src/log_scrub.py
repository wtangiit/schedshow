#!/usr/bin/env python

'''this script is to scrub user and account related information for PBS-style job log. Following fields are 
anonymized by natural numbers:
user
account (presenting project name)
args
exe
pwd

Usage: ./log_scrub.py -i input_log

the output file (i.e., the scrubbed job log) is named "input_log.scrub" and can be found in 
the same directory of input_log

'''

import sys
import time
from datetime import datetime
from optparse import OptionParser
import optparse

__helpmsg__ = "Usage: python log_scrub.py -i input_log_path"


    
def log_scrub(inputfile):
    '''scrub pbs style job trace, hidden fields: user, account(project name), 
    arg, pwd, exc (the later three contains user name in their path '''
    infile = open(inputfile, "r")
    outfile = open(inputfile+".scrub", "w")
    
    user_dict ={}
    project_dict = {}
    args_dict = {}
    cwd_dict = {}
    exe_dict = {}
            
    for line in infile:
        line = line.strip()
        
        line_data_dict = {}
        
        first_parse = line.split(";")
        eventType = first_parse[1]
        
        fields_string = first_parse.pop()
        
        newline = ";".join(first_parse) + ";"
        
        if len(fields_string) > 0:
            second_parse = fields_string.split(" ")
            
            for item in second_parse:
                tup = item.partition("=")
                    
                if tup[0] == "user":
                    user_name = tup[2]         
                    user_id = user_dict.get(user_name, -1)
                    if user_id == -1:
                        user_id =  len(user_dict) + 1
                        user_dict[user_name] = user_id                       
                    newline += " %s=%s" % (tup[0], user_id)
                    
                elif tup[0] == "account":
                    project_name = tup[2]
                    project_id = project_dict.get(project_name, -1)
                    if project_id == -1:
                        project_id = len(project_dict) + 1
                        project_dict[project_name] = project_id
                    newline += " %s=%s" % (tup[0], project_id)
                    
                elif tup[0] == "args":
                    args_name = tup[2]
                    args_id = project_dict.get(args_name, -1)
                    if args_id == -1:
                        args_id = len(args_dict) + 1
                        args_dict[project_name] = args_id
                    newline += " %s=%s" % (tup[0], args_id)
                    
                elif tup[0] == "exe":
                    exe_name = tup[2]
                    exe_id = project_dict.get(exe_name, -1)
                    if exe_id == -1:
                        exe_id = len(exe_dict) + 1
                        exe_dict[exe_name] = exe_id
                    newline += " %s=%s" % (tup[0], exe_id) 
                    
                elif tup[0] == "cwd":
                    cwd_name = tup[2]
                    cwd_id = project_dict.get(cwd_name, -1)
                    if cwd_id == -1:
                        cwd_id = len(cwd_dict) + 1
                        cwd_dict[cwd_name] = cwd_id
                    newline += " %s=%s" % (tup[0], cwd_id)
                    
                else:
                    newline += " %s=%s" % (tup[0], tup[2])
        newline += '\n'
        outfile.write(newline)
        
    infile.close()
    outfile.close()
        
            
if __name__ == '__main__':    
    if len(sys.argv) == 1:
        print __helpmsg__
        sys.exit(1)
        
    p = OptionParser()
    p.add_option("-i", dest = "inputfile", type = "string", 
                    help = "path of input log file (required)")
    
    opts, args = p.parse_args()
    
    if not opts.inputfile:
        print "please specify path of input log file (log to be anonymized"
        p.print_help()
        exit()
        
    log_scrub(opts.inputfile)