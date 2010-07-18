"""
1-- P    P
 
2-- P    P
    |    |
    3    4
"""
import random
class Rect:

    #constructor
    def __init__(self,p1,p2,p3,p4,color): 
        self.p1=p1
        self.p2=p2
        self.p3=p3
        self.p4=p4
        self.color=color
    #get_Methods
    def get1(self):
        return self.p1
    def get2(self):
        return self.p2
    def get3(self):
        return self.p3
    def get4(self):
        return self.p4
    def getColor(self):
        return self.color
# End of Class

# Second Part Start:

l=[]  # a list contains all the rectangles.
colorList=['b','g','r','c','m','y','gray']  # 7 color are used here

def add(a1,a2,a3,a4,color):
    temp=Rect(a1,a2,a3,a4,color) 
    l.append(temp)  

def getColor(t1,t2,t3,t4,thresholdx,thresholdy):   #test the point and return a color    
    tempColor=[]
    tempColor=colorList[:]
    if len(l)==0:
        return random.choice(tempColor)
    else:
        for i in range(0,len(l)):
            if abs( t3-l[i].get3() )<=thresholdx and abs( t4-l[i].get4() )<=thresholdx and abs( t1-l[i].get2() )<=thresholdy: 
 		#print '!!!!!!!!! shang'   
                if l[i].getColor() in tempColor:
                    tempColor.remove(l[i].getColor())
            if abs( t3-l[i].get3() )<=thresholdx and abs( t4-l[i].get4() )<=thresholdx and abs( t2-l[i].get1() )<=thresholdy:
 		#print '!!!!!!!!! xia'   
                if l[i].getColor() in tempColor:
                    tempColor.remove(l[i].getColor())
            if abs( t1-l[i].get1() )<=thresholdy and abs( t2-l[i].get2() )<=thresholdy and abs( t4-l[i].get3() )<=thresholdx:
 		#print '!!!!!!!!!! you'   
                if l[i].getColor() in tempColor:
                    tempColor.remove(l[i].getColor())
            if abs( t1-l[i].get1() )<=thresholdy and abs( t2-l[i].get2() )<=thresholdy and abs( t3-l[i].get4() )<=thresholdx:
 		#print '!!!!!!!!!! zuo'  
                #print ' the zuo color is',l[i].getColor() 
                if l[i].getColor() in tempColor:
                    tempColor.remove(l[i].getColor())
                #print 'tempColorlist is ',tempColor
    return random.choice(tempColor)

             


            
                   

