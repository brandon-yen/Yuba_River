import simpy
import threading
import sys
from pydispatch import dispatcher
from random import seed, randint

seed()

TRANSFER_TOTAL_DURATION = 1000
TRANSFER_TIME_SLOTS = 100

RECEIVER_TOTAL_DURATION = 900
RECEIVER_WAKE_UP_DURATION = 9
RECEIVER_SLEEP_DURATION = RECEIVER_TOTAL_DURATION - RECEIVER_WAKE_UP_DURATION

RECEIVER_SIGNAL = 'receiver_signal'
RECEIVER_SENDER = 'receiver_sender'
TRANSFER_SIGNAL = 'transfer_signal'
TRANSFER_SENDER = 'transfer_sender'

#threadLock = threading.Lock()

class advertising(object):
    def __init__(self, env, threadID, name):
	self.env = env
        self.threadID = threadID
        self.name = name
	# Start the run process everytime an instance is created.
	self.action = env.process(self.run())

    def run(self):
	while True:
            if (self.env.now < 50):
                print('%s (thread %d): Start advertising at %d' %(self.name,
                    self.threadID, self.env.now))
	    advertising_duration = TRANSFER_TOTAL_DURATION / TRANSFER_TIME_SLOTS
	    # We yield the process that process() returns
	    # to wait for it to finish
            if (self.env.now < 50):
                print('%s (thread %d): Sending Message at %d\n' %(self.name, 
                    self.threadID, self.env.now))
            dispatcher.send(message='message from Transfer', signal=TRANSFER_SIGNAL, 
                    sender=TRANSFER_SENDER)
	    yield self.env.process(self.advertising(advertising_duration))

    def advertising(self, duration):
	yield self.env.timeout(duration)

class transfer():
    def __init__(self, threadID, name):
        self.threadID = threadID
        self.name = name
        dispatcher.connect(self.transfer_dispatcher_receive, signal=RECEIVER_SIGNAL, 
                sender=RECEIVER_SENDER)
        self.run()
    
    def transfer_dispatcher_receive(self, message):
        print('Transfer has received message: {}\n'.format(message))

    def run(self):    
        env = simpy.Environment()
        advertising(env, self.threadID, self.name)
        env.run(until=TRANSFER_TOTAL_DURATION)

class receiverWakeupAndSleep(object):
    def __init__(self, env, threadID, name):
	self.env = env
        self.threadID = threadID
        self.name = name
	self.action = self.env.process(self.run())
        self.getMessage = False

    def run(self):
	while True:
            print('%s (thread %d): Wake up at %d\n' %(self.name, 
                self.threadID, self.env.now))
                
            randWakeup = randint(1, RECEIVER_WAKE_UP_DURATION)
            self.messageHandler(randWakeup)
            yield self.env.timeout(randWakeup)

            yield self.env.timeout(RECEIVER_WAKE_UP_DURATION + 1 - randWakeup)
            print('%s (thread %d): Sleep at %d\n' %(self.name, 
                self.threadID, self.env.now))
            dispatcher.disconnect(self.handler, signal=TRANSFER_SIGNAL, 
                    sender=TRANSFER_SENDER)
	    yield self.env.timeout(RECEIVER_SLEEP_DURATION)

    def messageHandler(self, randWakeup):
        print("randWakeup = %d at %d\n" %(randWakeup, self.env.now))
        dispatcher.connect(self.handler, signal=TRANSFER_SIGNAL, 
                sender=TRANSFER_SENDER)
    
    def handler(self, message):
        print('receiver has received message: %s at %d' %(message, self.env.now))

def receiveAdvertising(env, receiverWakeup):
    yield env.timeout(1)
    receiverWakeup.action.interrupt()

class receiver():
    def __init__(self, threadID, name):
        self.threadID = threadID
        self.name = name
        self.run()

    def run(self):
        env = simpy.Environment()
        receiverWakeup = receiverWakeupAndSleep(env, self.threadID, self.name)
        #env.process(receiveAdvertising(env, receiverWakeup))
        env.run(until=RECEIVER_TOTAL_DURATION)

class myThread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        if threadID == 1 :
            threading.Thread(target=transfer)
        elif threadID == 2 :     
            threading.Thread(target=receiver)
             
        self.threadID = threadID
        self.name = name
    
    def run(self):
        print "********** Starting thread %d **********\n" %(self.threadID)
        if self.threadID == 1 :
            transfer(self.threadID, self.name)
        elif self.threadID == 2 :
            receiver(self.threadID, self.name)

def main():
    threads = [] 

    # Create new threads
    thread1 = myThread(1, "transfer", )
    thread2 = myThread(2, "receiver", )
    
    # Strat new threads
    thread1.start()
    thread2.start()

    # Add threads to thread list
    threads.append(thread1)
    threads.append(thread2)
    
    for thread in threads :
        thread.join()
    print "Exiting Main Thread\n" 

if __name__ == '__main__':
    main()

