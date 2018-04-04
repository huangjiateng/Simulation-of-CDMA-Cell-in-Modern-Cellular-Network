import math as m
import numpy as np


r = 10 #km Users are all within 10km Radius around the basestation
bw_c = 1.25 #MHz  Carrier Bandwidth
r_bit = 12.5 #kbps  Bit Rate
SINR_min = 6 #dB  Required SINR
min_pilotRSL = -107 #dBm  Minimum Pilot RSL
number_tc = 56 #Number of Available Traffic Channels
#The properties of users
r_call = 6 #per hour  Call Arrival Rate
t_call = 1/60 #hour  Average Call Duration




def Attemptedcalls(t):   #set up the location and other parameters for attempted users
    i = 0
    while i < number_users:
        j = np.random.randint(0, 600) #uniformly choose a number between 0(inclusive) and 600(exclusive), and when j == 300, this user becomes an attempted user
        if j == 300:
            theta = np.random.random()*2*m.pi #randomly choose an angle
            k = np.random.uniform(0, 1)
            x_user = m.sin(theta) * m.sqrt(k) * 10 #km
            y_user = m.cos(theta) * m.sqrt(k) * 10 #km
            connection_fail = 3
            list_attemptedusers.append([x_user, y_user, t, connection_fail])
            i += 1
        else:
            i += 1
    return list_attemptedusers



def Compute_RSL(d,S, EIRP, F):   #compute the RSL 
    h_bs = 50 #m  Basestation Height
    f_c = 1900 #MHz  Carrier Frequency
    PL = 46.3 +33.9 * m.log(f_c, 10) - 13.82 * m.log(h_bs, 10) +(44.9 - 6.55 * m.log(h_bs, 10)) * m.log(d, 10) #dB  parameter d is in km and will vary with different users
    RSL = EIRP - PL + S + F #dB
    return RSL


   
def Compute_SINR(RSL, number_channelinuse):   #compute the SINR
    PG = 20 #dB  Processor Gain
    Noise_Level = -110 #dBm  Noise Level
    Signal_Level = RSL + PG
    if number_channelinuse == 1:   #when there is only one active user(number of channel in use = 1), there is no interference from other users, so the interference level = 0
        Interference_Level = 0
        NI_Level = 10 * m.log(0 + pow(10, -110/10), 10)
        SINR = Signal_Level - NI_Level
    else:
        Interference_Level = RSL + 10 * m.log(number_channelinuse - 1, 10)
        NI_Level = 10 * m.log(pow(10, Interference_Level/10) + pow(10, -110/10), 10)
        SINR = Signal_Level - NI_Level  #dB
    return SINR





#compute shadowing value S for each 10m by 10m square, assume the location of the basestation is (0,0).
#This starts from the top left corner, and move along the x-axis for 10m each time with the same y coordinate
#When x_max = 10000, it will moves to the next row and keep doing until it reaches the down right corner
x_min = -10000 #m   10km
x_max = -9990 #m
y_max = 10000 #m
y_min = 9990 #m
list_shadowing = [] 
S = np.random.normal(0,2)
list_shadowing.append([x_min, x_max, y_min, y_max, S])
while y_max >= -10000:
    while x_max < 10000:
        x_min += 10
        x_max += 10
        S = np.random.normal(0,2)
        list_shadowing.append([x_min, x_max, y_min, y_max, S])
    if x_max == 10000 and y_min == -10000:
        break
    if y_max >-10000:
        y_max -= 10
        y_min -= 10
        x_min = -10000
        x_max = -9990
        S = np.random.normal(0,2)
        list_shadowing.append([x_min, x_max, y_min, y_max, S])

       

number_attemptedcalls = 0 # Number of attempted calls without retries
number_attemptedcallsR = 0 # Number of attempted calls including retries
number_completedcalls = 0 #Number of completed calls
number_channelinuse = 0 # Number of channel in use
number_droppedcalls = 0 # Number of dropped calls
number_bcss = 0 # Number of blocked calls due to signal strength
number_bccc = 0 # Number of blocked calls due to channel capacity
list_attemptedusers = [] # [x_user, y_user, t, connection_fail]
list_activeusers = [] # [x_user, y_user, t, call_duration, droptime]
list_t = [] # Temporary List

t = 1 # current time
i = 0 # control pointer in list_activeusers
j = 0 # control pointer in list_shadowing
maxp_bs = 42 #dbm 15.85W  Basestation Maximum Transmitter Power
l_lc =2.1 #dB  Line and Connector Losses
g_a = 12.1 #dB  Antenna Gain

# admission control parameters
C_d = 57
C_i = 0
number_users = 1000 #Number of Users


EIRP = maxp_bs - l_lc + g_a #dBm
EIRP_Pilot = 52 #dB

while t <= 7200:
    cell_radius = 0
    i = 0
    # first, we need to check if those active users should be dropped or have already completed, and then check if the SINR can meet the requirement
    while i < len(list_activeusers):
        if t == list_activeusers[i][4]:   #list_activeusers[i][4] is droptime which is a parameter that has been set up to -1 when the user set up the call
            del list_activeusers[i]   #but when t == list_activeusers[i][4], it means that this is the time that this call should be dropped and the channel can be freed
            number_droppedcalls += 1
            number_channelinuse -= 1
            
        elif t >= list_activeusers[i][2] + list_activeusers[i][3]:   # list_activeusers[i][2] is t which is the time when this call being set up and list_activeusers[i][3] is call duration
            del list_activeusers[i]   #this it the time when the call should have completed
            number_completedcalls += 1
            number_channelinuse -= 1
            
        else:
            if list_activeusers[i][0] >= 0:   # this is used to locate which area the user in and what is the S for that area
                j = 1000 + int(list_activeusers[i][0] * 100)
                if list_activeusers[i][1] <= 0:
                    j += 2000 * int((10000 - list_activeusers[i][1] * 1000) / 10)
                else:
                    j += 2000 * int((10000 - list_activeusers[i][1] * 1000) / 10)
            else:
                j = int((10000 - abs(list_activeusers[i][0]) * 1000) / 10)
                if list_activeusers[i][1] <= 0:
                    j += 2000 * int((10000 - list_activeusers[i][1] * 1000) / 10)
                else:
                    j += 2000 * int((10000 - list_activeusers[i][1] * 1000) / 10)
            S = list_shadowing[j][4]
            d = m.sqrt(pow(list_activeusers[i][0], 2) + pow(list_activeusers[i][1], 2)) # compute the distance between the basestation and the user
            cell_radius = max(d, cell_radius)
            F = 20 * m.log(np.random.rayleigh(), 10) # compute the fading value for this user at this location at this time
            EIRP = maxp_bs - l_lc + g_a #dBm
            RSL = Compute_RSL(d, S, EIRP, F)
            SINR = Compute_SINR(RSL, number_channelinuse)
            
            if SINR < SINR_min and list_activeusers[i][4] == -1:   # filter out those calls which do not meet the SINR_min but have already been marked in the 4th parameter
                list_activeusers[i][4] = t + 3 # let this call drop after 3 seconds
                i += 1
            else:
                i += 1

                
    # Next, it is time to generate the attempted calls by using the function Attemptedcalls(t) which has shown above
    number_oldattemptedcalls = len(list_attemptedusers)
    list_attemptedusers = Attemptedcalls(t)
    number_attemptedcalls += len(list_attemptedusers) - number_oldattemptedcalls
    number_attemptedcallsR += len(list_attemptedusers)
    i = 0
    j = 0

    #this is the admission control which happens every second
    if number_channelinuse > C_d and EIRP_Pilot > 30:
        EIRP_Pilot -= 0.5
    elif number_channelinuse < C_i and EIRP_Pilot < maxp_bs - l_lc + g_a:
        EIRP_Pilot += 0.5
        
    # Finally, we need to check if those attempted calls can be successfully connected
    while i < len(list_attemptedusers):
        if list_attemptedusers[i][3] <= 0:   # list_attemptedusers[i][3] is connection_fail which has been set to 3 at the beginning
            del list_attemptedusers[i] # when the connection fails 3 times in a row, the it should be blocked due to signal strengh
            number_bcss += 1
            continue

        d = m.sqrt(pow(list_attemptedusers[i][0], 2) + pow(list_attemptedusers[i][1], 2))
        if list_attemptedusers[i][0] >= 0:   # again, this is used to locate which area the user in and what is the S for that area
            j = 1000 + int(list_attemptedusers[i][0] * 100)
            if list_attemptedusers[i][1] <= 0:
                j += 2000 * int((10000 - list_attemptedusers[i][1] * 1000) / 10)
            else:
                j += 2000 * int((10000 - list_attemptedusers[i][1] * 1000) / 10)
        else:
            j = int((10000 - abs(list_attemptedusers[i][0]) * 1000) / 10)
            if list_attemptedusers[i][1] <= 0:
                j += 2000 * int((10000 - list_attemptedusers[i][1] * 1000) / 10)
            else:
                j += 2000 * int((10000 - list_attemptedusers[i][1] * 1000) / 10)
        S = list_shadowing[j][4]
        F = 20 * m.log(np.random.rayleigh(), 10)
        RSL = Compute_RSL(d,S,EIRP_Pilot, F)
        
        if RSL < min_pilotRSL:
            list_attemptedusers[i][3] -= 1 # if the RSL of the pilot channel does not meet the min_pilotRSL, then we will allow this user to retry in the next second
            i += 1
        else:
            if number_channelinuse < 56: # if the RSL of the pilot channel meets the min_pilotRSL, then we need to check if there is available channel to use
                call_duration = np.random.exponential(60) #s
                droptime = -1
                list_t = list_attemptedusers[i] # what I do is just put the list of this connected user to a temporary list, and modify that temporary list, and put it into the list of active users
                del list_t[3]
                list_t[2] = t
                list_t.append(call_duration)
                list_t.append(droptime)
                list_activeusers.append(list_t)
                number_channelinuse += 1
                del list_attemptedusers[i]
                continue
            else:
                del list_attemptedusers[i] # if there is no available channel to use, then the attempted call will be blocked due to channel capacity
                number_bccc += 1
                continue

    number_failedcalls = number_droppedcalls + number_bcss + number_bccc # Number of failed calls
    if t % 120 == 0 and t != 0:
        print('t =', t, 's')
        print('C_d = ', C_d, 'C_i = ', C_i, 'The number of users = ', number_users)
        print('The number of attempted calls without retries = ', number_attemptedcalls)
        print('The number of attempted calls including retries = ', number_attemptedcallsR)
        print('The number of completed calls = ', number_completedcalls)
        print('The number of channel in use = ', number_channelinuse)
        print('The number of dropped calls = ', number_droppedcalls)
        print('The number of blocked calls due to signal strength = ', number_bcss)
        print('The number of blocked calls due to channel capacity = ', number_bccc)
        print('The number of failed calls = ', number_failedcalls)
        print('Current cell radius = ', cell_radius, '\n')
        t += 1
    else:
        t += 1





   






    
