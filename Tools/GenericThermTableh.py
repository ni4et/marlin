#!/usr/bin/python3
''' DOC String
    This program generates a c/c++ header file to be used in the Marlin 3D printer control
    system to calculate temperature values from ADC readings.  The output is intended to
    replace all of the thermistortable_xxx.h files for 100k NTC thermistors where a point by
    point calibration is not needed, and where the beta value is known.
    When one of the generated headers is included by number in Configuration.h the beta is speciied there
    also.   The compiler calcuates the ADC to temperature table in the usual format at compile
    time using the macros.

    This file is  only a program generator.

    It can be adapted for other pullup/R0 values if so desired.

    If beta is not known, start with 3950.  If you can measure or estimate the temperature based on
    material performance by adjusting beta and re-compiling.  Higher betas result in higher operating
    temperature.

    In the case where tbl is zero all of the practical ADC values are output with the corresponding
    temperatures as a confidence building tool.  Values should correspond closely with existing tables.
'''

import numpy as np
import math as m
import sys


tbls=[600,601,0]  # Generates thermistortable_xxx.h

rRef=1e5  # Nominal NTC resistance at T0-25C
rPullup=4700 # Nominal pull up
tZero=273.15 # Constant C->K converson
adcFS=1023 # Full scale at the ADC representing Tthermistor=infinity

# Constants used to fake data so that reasonable data points can be selected.
maxTemp=300
minTemp=-15

# Trial and display beta values. Should cover the range of whats available.
TXBETA1=3380 # Reference value
TXBETA2=3950 # Arbitrary constant used to space out points kept in the table
TXBETA3=4500 # Reference value


# Functions:
def v2r(vr): # In adc Units to res
    vrs=vr/adcFS
    return ((vrs*rPullup)/(1-vrs))

def r2v(r): # Res to adc units
    return adcFS*r/(r+rPullup)


# Strings:


# Header file documetation
string1=r'''// Generic NTC table {tbl:1}
// Implements the Steinhart-Hart Equation with
//  Beta defined at compile time
// 1/T=1/T0+1/BETA*ln(R/R0)
// The voltage divider at the ADC input with the thermistor
// and the ln(R/R0) function is taken into account
// in the table that is generated.  The compiler does the math
// to generate the temperatures at selected points.


#ifndef BETA_{tbl:1}
#error Pease define BETA_{tbl:}  in configuration.h according to thermistor specs.
#endif // BETA_{tbl:}

#define T0_{tbl:1} (273.15)

#define TV_{tbl:1}(rval) (short)(1.0/(1.0/(25.0+T0_{tbl:1})+rval/BETA_{tbl:3})-T0_{tbl:3}+0.5)

// Values to the right are temperature value projections for beta values={b1:}, {b2:}, and {b3:}

const short temptable_{tbl:3}[][2] PROGMEM = '''

# format strings for one record in the table
stringInstance='   OV({adc:4.0f}),   TV_{tbl:}({rlvals:4.6f})'
instanceComment='  //  ({tx1:}, {tx2:}, {tx3:})'

# The range of ADC values to consider:
adcStart=20
adcStop=1020
numResult=adcStop-adcStart+1

adc=np.linspace(adcStart,adcStop,numResult)

rlvals=np.empty(numResult)

for i in range(0,numResult):
    rlvals[i]=np.log(v2r(adc[i])/rRef)
    
#fout=sys.stdout

for tbl in tbls:
    if (tbl==0):
        temperatureStepSize=0
    else:
        temperatureStepSize=(maxTemp-minTemp)/100 # Arbitrary spacing between temperature points given B=TXBETA


        
    fout=open('thermistortable_{tbl:1}.h'.format(tbl=tbl),'w')
    print(string1.format(tbl=tbl,b1=TXBETA1,b2=TXBETA2, b3=TXBETA3),'{',file=fout)

    oldTx=maxTemp # Bigger temperature values than this are not useful
    lines=0

    for i in range(0,numResult):
        tx1=1.0/(1.0/(25.0+tZero)+rlvals[i]/TXBETA1)-tZero+0.5 # Steinhart-Hart
        tx2=1.0/(1.0/(25.0+tZero)+rlvals[i]/TXBETA2)-tZero+0.5 # Steinhart-Hart
        tx3=1.0/(1.0/(25.0+tZero)+rlvals[i]/TXBETA3)-tZero+0.5 # Steinhart-Hart

        if tx2<oldTx: # Try to space out the temperatures so the bisect routine doesnt get a /0
            oldTx=oldTx-temperatureStepSize # Chosen by trial and error to yield <100 values
            print('{',stringInstance.format(adc=adc[i],rlvals=rlvals[i],tbl=tbl),'},',
                  instanceComment.format(tx1= m.floor(tx1) , tx2=m.floor(tx2) , tx3=m.floor(tx3) ),
                  file=fout)
            lines+=1
            
    print('};',file=fout)
    print("Liines output=",lines)
fout.close()


testThermistorTable='''
//C program to test generated tables

#include <stdio.h>
#define PROGMEM
#define OV(x) x


#define BETA_601 3950
#define BETA_602 4100

#include "thermistortable_601.h"
#include "thermistortable_602.h"

int main(int argc, char ** argv)
{
	int i;
	for (i=0;i<sizeof(temptable_601)/sizeof(temptable_601[0]);i++)
		printf("%d %d %d\n",i,temptable_601[i][0],
			temptable_601[i][1]);

	printf("\n\n\n");

	for (i=0;i<sizeof(temptable_602)/sizeof(temptable_602[0]);i++)
		printf("%d %d %d\n",i,temptable_602[i][0],
			temptable_602[i][1]);
	return 0;
}

'''
