#!/usr/bin/env python
''' tools to process Intrepid job log database (used for walltime prediction journal paper)'''

import MySQLdb
import sys
import time
from datetime import datetime
from optparse import OptionParser
import numpy as np
import matplotlib.pyplot as plt
from pylab import *

def date_to_epoch(datestr, format='%Y-%m-%d %H:%M:%S'):
    return int(time.mktime(time.strptime(datestr, format)))

def epoch_to_date(epoch, format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(epoch))

__helpmsg__ = "Usage: dbjobs <function>"


linestyles1 = ['-+', '--', '-r', '-1k', '-2m', '-', '-', '-', '-', '-']
linestyles2 = ['--b', '-r', '-.k', '-,m', ':g', '-', '-', '-', '-', '-']
linestyles = ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
#markstyles = ['*', '+', '.', '*' , '+ ', '' , ' ', ' ', ' ']
TRIP = 0

GRID_LINEWIDTH = 0.6
GRID_ALPHA = 0.3
PLOTWIDTH = 1.4

cdfyticks = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

legend_dict ={'all_jobs': "Original",
'predict_by_triple_50_w1':"Median",
'predict_by_triple_85_w1':"85th Percentile",
'predict_by_triple_100_w1':"Maximum",
'predict_by_double_50_w1':"Median",
'predict_by_double_85_w1':"85th Percentile",
'predict_by_double_100_w1':"Maximum",
}


PERCENTILE_PRED = 80
PREDICT_TABLE_NAME = "predict_by_double"
PREDICT_FILE_NAME = PREDICT_TABLE_NAME + ".csv"

def plotline(ax, output, linestyles):
    lines = ax.plot(output, linestyles, linewidth=PLOTWIDTH, markeredgewidth=1, markersize=8)
    return lines
        

fig = plt.figure()

def sec_to_date(sec, format="%m/%d/%Y %H:%M:%S"):
    tmp = datetime.fromtimestamp(sec)
    fmtdate = tmp.strftime(format)
    return fmtdate    
                      
def date_to_sec(fmtdate, format="%m/%d/%Y %H:%M:%S"):
    t_tuple = time.strptime(fmtdate, format)
    sec = time.mktime(t_tuple)
    return sec
    
def calc_ave_response(jobdict):
    jobids = jobdict.keys()
    jobnumber = len(jobids)
    total = 0
    for jobid in jobids:
        temp = jobdict[jobid]
        resp = float(temp['end']) - float(temp['qtime'])
        total += resp
    ave = total / jobnumber
    return ave
       
def make_job_list(db):

    cur = db.cursor()
    
    sql_stmt = " SELECT distinct jobid, project, user, walltime, runtime, ratio, qtime, start, end, queue, nodes FROM all_jobs"
    print "executing sql_stmt: ", sql_stmt
    cur.execute(sql_stmt)
        
    result_set = cur.fetchall()
    
    joblist = []
    
    for row in result_set:
        temp_job = {}
        temp_job['jobid'] = int(row[0])
        temp_job['project'] = row[1]
        temp_job['user'] = row[2]
        temp_job['walltime'] = float(row[3])
        temp_job['runtime'] = float(row[4])
        temp_job['ratio'] = float(str(row[5]))
        temp_job['qtime'] = str(row[6])
        temp_job['start'] = str(row[7])
        temp_job['end'] = str(row[8])
        temp_job['queue'] = row[9]
        temp_job['nodes'] = int(row[10])
        temp_job['prediction'] = 0
        temp_job['accuracy'] = 0
        joblist.append(temp_job)
        
    print "total job count:", len(joblist)
    return joblist
    
def make_ratio_dict(db, scheme):
    print "entered make_ratio_dict, scheme=", scheme
    ratio_dict = {}
    
    cur = db.cursor()
  
    sql_stmt = ""
    if scheme == 0:
        sql_stmt = "SELECT distinct user FROM all_jobs"
    if scheme == 1:
        sql_stmt = "SELECT distinct project FROM all_jobs"
    if scheme == 2:
        sql_stmt = "SELECT distinct user, project FROM all_jobs"
    if scheme == 3:
        sql_stmt = "SELECT distinct user, project, walltime FROM all_jobs"
    
    print "executing sql_stmt: ", sql_stmt
    cur.execute(sql_stmt)
    field_names = []
    result_set = cur.fetchall()
    for row in result_set:
        rec = []
        for col in row:
            rec.append(col) 
        field_names.append(rec)
    
    for item in field_names:
        sql_stmt = ""
        key = ""
        if scheme == 0:
            sql_stmt = "SELECT ratio, end FROM all_jobs WHERE user=\"%s\" order by end" % (item[0])
            key = item[0]
        elif scheme == 1:
            sql_stmt = "SELECT ratio, end FROM all_jobs WHERE project=\"%s\" order by end" % (item[0])
            key = item[0]
        elif scheme == 2:
            sql_stmt = "SELECT ratio, end FROM all_jobs WHERE user=\"%s\" and project=\"%s\" order by end" % (item[0], item[1])
            key = "%s:%s" % (item[0], item[1])
        elif scheme == 3:
            sql_stmt = "SELECT ratio, end FROM all_jobs WHERE user=\"%s\" and project=\"%s\" and walltime=\"%s\" order by end"  % (item[0], item[1], item[2])
            key = "%s:%s:%s" % (item[0], item[1], int(item[2]))
        else:
            pass
        
        print "executing sql_stmt: ", sql_stmt
        cur.execute(sql_stmt)
        
        result_set = cur.fetchall()
        
        ratio_list = [] 
        for row in result_set:
            ratio_value = row[0]
            end_time = str(row[1])
            ratio_list.append((ratio_value, end_time))
            
        ratio_dict[key] = ratio_list
        
    return ratio_dict

def get_predicted_ratio(ratio_dict, key, qtime, percentile, timewindow_month=None):
    '''find in the ratio_dict the x-percentile of the ratio of the same key before qtime'''    
    window_open_date = "2009-01-01 00:00:00"
    if timewindow_month:
        qtime_sec = date_to_epoch(qtime) 
        window_size_sec = timewindow_month * 30 * 24 * 3600
        window_open_date = epoch_to_date(qtime_sec - window_size_sec) 
    
    predicted_ratio = 1
    ratio_rec_list = ratio_dict[key]
    ratio_list = []
    for rec in ratio_rec_list:
        if rec[1] > window_open_date and rec[1] < qtime:
            ratio_list.append(rec[0])
    all_count = len(ratio_list)
    ratio_list.sort()
    if all_count >= 10:
        index = all_count * percentile / 100 - 1
        predicted_ratio = ratio_list[index]
    if predicted_ratio < 0.5:
        predicted_ratio = 0.5
    return predicted_ratio
    
def update_predicted_walltime(db, scheme, percentile, timewindow=None):
    
    print "entered update_predicted_walltime"
    
    key = ""
    predict_table_name = PREDICT_TABLE_NAME
       
    if scheme == 0:
        predict_table_name = "predict_by_user_"
    elif scheme == 1:
        predict_table_name = "predict_by_proj_"
    elif scheme == 2:
        predict_table_name = "predict_by_double_"
    elif scheme == 3:
        predict_table_name = "wapr_"
        
    predict_table_name += str(percentile)
    
    #if timewindow:
    #   predict_table_name += "_m"
    #  predict_table_name += str(timewindow)
                   
    predict_file_name = predict_table_name + ".csv"
    
    outfile = open(predict_file_name, "w")
    
    cur = db.cursor()
    
    sql_stmt = "CREATE TABLE if not exists %s (jobid INT, qtime datetime, walltime INT, runtime FLOAT, ratio FLOAT, project VARCHAR(25), user VARCHAR(10), nodes INT, prediction INT, accuracy FLOAT);" % predict_table_name

    print "executing sql_stmt: ", sql_stmt
    
    cur.execute(sql_stmt)
    
    sql_stmt = "TRUNCATE TABLE %s" % predict_table_name
    
    print "executing sql_stmt: ", sql_stmt
        
    cur.execute(sql_stmt)
    
    #percentile = PERCENTILE_PRED
    
    job_list = make_job_list(db)
    ratio_dict = make_ratio_dict(db, scheme)
    

    
    #sql_insert_stmt = "INSERT INTO %s values" % PREDICT_TABLE_NAME
    
    for job in job_list:
        jobid = job['jobid']
        user = job['user']
        project = job['project']
        walltime = int(job['walltime'])
        qtime = job['qtime']
        runtime = job['runtime']
        key = ""
        if scheme == 0:
            key = user
        elif scheme == 1:
            key = project
        elif scheme == 2:
            key = "%s:%s" % (user, project)
        elif scheme == 3:
            key ="%s:%s:%s" % (user, project, walltime)
        
        pred_ratio = get_predicted_ratio(ratio_dict, key, qtime, percentile, timewindow)
        pred_ratio =1
        predicted_walltime = walltime * pred_ratio
        
        job['prediction'] = predicted_walltime
        
        if predicted_walltime >= runtime:
            accuracy = runtime / predicted_walltime
        else:
            accuracy = predicted_walltime / runtime
        
        job['accuracy'] = accuracy
        
        line = ("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n") % (jobid, qtime, walltime, runtime, job['ratio'], project, user, job['nodes'], predicted_walltime, accuracy )
        
        #value_rec = "(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")" % (jobid, qtime, walltime, runtime, job['ratio'], project, user, job['nodes'], predicted_walltime, accuracy )
        #sql_insert_stmt += value_rec
        #sql_insert_stmt += ","
        outfile.write(line)
        
    
    print "finished writing file"
    
    sql_stmt = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'" % (predict_file_name, predict_table_name) 
         
        #sql_stmt = "INSERT INTO predict_by_proj values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (jobid, qtime, walltime, runtime, job['ratio'], project, user, job['nodes'], predicted_walltime, accuracy )
    print "executing sql_stmt: ", sql_stmt
    
    #sql_insert_stmt = sql_insert_stmt[:-1]
    #cur.execute(sql_stmt)
    outfile.close()
    
    

def plot_CDF(bins, name):
    print "bins=", bins.keys()
    output = {}
    #points = range(0, 601)
    points = [ 0.02*x for x in range(0, 51) ]
    sorted_keys = bins.keys()
    sorted_keys.sort()
    print "sorted_keys=", sorted_keys
    for m in points:
        for k in sorted_keys:
            num = 0.0
            if len(bins[k]) == 0:
                continue
            for j in bins[k]:
                #print j
                if j <= m:
                    num += 1
            if not output.has_key(k):
                output[k] = []
            frag = num/len(bins[k])
            output[k].append(frag)
    
    ind = np.arange(len(output.values()[0]), step=1)
    
    print "ind=", ind
    
    #ax = fig.add_subplot(231)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_ylabel("fraction")
    ax.set_xlabel("Accuracy Value (0--1)")
    ax.set_title("CDF of Acc. (before and after walltime prediction)")

    plot_things = []
    legend_labels = []
    i = 0
    for k in sorted_keys:
        plot_things.append(plotline(ax, output[k], linestyles1[i]))
        lgd = legend_dict.get(k, k)
        legend_labels.append(lgd)
        i += 1

    ax.legend( tuple(plot_things), tuple(legend_labels), loc=4)
    ax.set_xticks(ind)
    for idx in range(len(points)):
        if (idx % 5) == 0:
            pass
        else:
            points[idx] = ""
                         
#    print "points=", points
    ax.set_xticklabels(points)
    ax.set_ylim(ymin=0, ymax=1)
    ax.set_yticks(cdfyticks)
    ax.yaxis.grid(True, linestyle='-', which='major', alpha=GRID_ALPHA, linewidth=GRID_LINEWIDTH)
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.grid(True, linestyle='-', which='major', alpha=GRID_ALPHA, linewidth=GRID_LINEWIDTH)
    plt.savefig("cdf-%s" % name)


def draw_R_CDF(db, tables):
    print "entered draw_R_CDF"
    cur = db.cursor()
    print "table list: ", tables
    bins = {}
    for table in tables:
        if table=="all_jobs":
            sql_stmt = "SELECT ratio FROM %s" % (table)
        else:
            sql_stmt= "SELECT accuracy FROM %s" % (table)
        
        print "executing sql statement: ", sql_stmt
    
        cur.execute(sql_stmt)
        numrows = int(cur.rowcount)
    
        print "numrows=", numrows
    
        result_set = cur.fetchall()
    
        Rlist = []
    
        for row in result_set:
            ratio = float(row[0])
            Rlist.append(ratio)
        
        bins[table] = Rlist
    
    plot_CDF(bins, "cdf-figure")
    
def generate_csv(db, table_name):
    
    job_list = make_job_list(db)
    
    outfile = open(table_name + ".csv", "w")
    
    for job in job_list:    
        jobid = job['jobid']
        user = job['user']
        project = job['project']
        walltime = int(job['walltime'])
        qtime = job['qtime']
        runtime = job['runtime']
        ratio = job['ratio']
        if job.get('prediction', 0) > 0:
            prediction = job['prediction']
        else:
            prediction = walltime
        if job.get('accuracy', 0) > 0:
            accuracy = job['accuracy']
        else:
            accuracy = float(runtime) / walltime 
        
        line = ("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n") % (jobid, qtime, walltime, runtime, job['ratio'], project, user, job['nodes'], prediction, accuracy)
        outfile.write(line)
        
    outfile.close()
            
    
def ratio_statistics(db):
    #field could be user, project, etc 

    cur = db.cursor()
    
    cur.execute("""SELECT distinct user FROM all_jobs""")
    numrows = int(cur.rowcount)
    
    print "numrows=", numrows
    
    field_names = []
    result_set = cur.fetchall()
    
    for row in result_set:
        field_names.append(row[0])
    
    result_dict = {}
    
    for item in field_names:
        sql_stmt = "SELECT count(jobid), avg(ratio), std(ratio) FROM all_jobs WHERE user=\"%s\"" % (item)
        cur.execute(sql_stmt)
        
        result_set = cur.fetchall()
    
        for row in result_set:
            ct = int(row[0])
            avg = float(row[1])
            std = float(row[2])
            tmp = (ct, avg, std)
            result_dict[item] = tmp
            
    for item in result_dict.keys():
        tmp = result_dict[item]
        print "%s;%s;%s;%s" % (item, tmp[0], tmp[1], tmp[2]) 
    
def ratio_statistics2(db):
    #field could be user, project, etc 

    cur = db.cursor()
    
    cur.execute("""SELECT distinct user, project FROM all_jobs""")
    numrows = int(cur.rowcount)
    
    print "numrows=", numrows
    
    field_names = []
    result_set = cur.fetchall()
    
    for row in result_set:
        tmp = (row[0], row[1])
        field_names.append(tmp)
    
    def diffcmp(tuple1, tuple2):
        return -cmp(tuple1[2], tuple2[2])
    
    result_dict = {}
    
    for item in field_names:
        sql_stmt = "SELECT count(jobid), avg(ratio), std(ratio) FROM all_jobs WHERE user=\"%s\" and project=\"%s\"" % (item[0], item[1])
        cur.execute(sql_stmt)
        
        key=":".join([item[0], item[1]])
                
        result_set = cur.fetchall()
    
        for row in result_set:
            ct = int(row[0])
            avg = float(row[1])
            std = float(row[2])
            tmp = (ct, avg, std)
            result_dict[key] = tmp
            
    for item in result_dict.keys():
        tmp = result_dict[item]
        print "%s;%s;%s;%s" % (item, tmp[0], tmp[1], tmp[2]) 
        
def ratio_statistics3(db):
    #field could be user, project, etc 

    cur = db.cursor()
    
    cur.execute("""SELECT distinct user, project, walltime FROM all_jobs""")
    numrows = int(cur.rowcount)
    
    print "numrows=", numrows
    
    field_names = []
    result_set = cur.fetchall()
    
    for row in result_set:
        tmp = (row[0], row[1], row[2])
        field_names.append(tmp)
    
    result_dict = {}
    
    for item in field_names:
        sql_stmt = "SELECT count(jobid), avg(ratio), std(ratio) FROM all_jobs WHERE user=\"%s\" and project=\"%s\" and walltime=\"%s\"" % (item[0], item[1], item[2])
        #print "executing sql stmt: ", sql_stmt
        cur.execute(sql_stmt)
        
        key=":".join([item[0], item[1], str(item[2])])
                
        result_set = cur.fetchall()
    
        for row in result_set:
            ct = int(row[0])
            avg = float(row[1])
            std = float(row[2])
            tmp = (ct, avg, std)
            result_dict[key] = tmp
            
    for item in result_dict.keys():
        tmp = result_dict[item]
        print "%s;%s;%s;%s" % (item, tmp[0], tmp[1], tmp[2]) 
    



if __name__ == '__main__':
    
    p = OptionParser()
    
    p.add_option("--Rcdf", dest = "cdf_table", type = "string", 
                    help = "draw CDF of R value for specified table")
    
    p.add_option("--stat", dest = "stat", \
            action = "store_true", \
            default = False, \
            help="show statistics of R value ")
    
    p.add_option("--predict", dest = "scheme", type = "int", \
                    help = "walltime predict")
    
    p.add_option("--percentile", dest="percentile", type="int",\
                 help="confidence percentile used in prediction")
    
    p.add_option("--window", dest="window", type="int",\
                 help="historical time window used for prediction (month in int)")
    
    p.add_option("--table2csv", dest="csv_table" , type="string",
                 help = "draw CDF of R value for specified table")
    
    (opts, args) = p.parse_args()
    
    #connect with database
    try:
        db = MySQLdb.connect(host="localhost", user="root", db="wpjobs", passwd="root")
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
        
    print opts, args
        
        
    if opts.cdf_table:
        tables = opts.cdf_table.split(":")
        draw_R_CDF(db, tables)
        
    if opts.stat:
        ratio_statistics(db)
            
    if opts.scheme in [0,1,2,3] and opts.percentile > 0:
        timewindow = None
        if opts.window:
            timewindow = opts.window 
        print timewindow
        update_predicted_walltime(db, opts.scheme, opts.percentile, timewindow)
        
    if opts.csv_table:
        generate_csv(db, opts.csv_table)
            
    db.close()
    
