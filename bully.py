# Emir Alaattin Yilmaz - Bully Election Algorithm Implementation - 2021

import random
from multiprocessing import Process
import threading
import os
import time
import zmq
import sys

def leader(node_id, starter, num_proc, SHARED_THREAD_MSGS):

    pid = os.getpid()

    print("PROCESS STARTS: {} {} {}".format(pid, node_id, starter))
    
    listener_thread = threading.Thread(target=responder,args=(node_id, num_proc, SHARED_THREAD_MSGS,))
    listener_thread.start()

    # Creates a socket instance
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    port = 5550 + node_id
    socket.bind(f"tcp://127.0.0.1:{port}")

    SHARED_THREAD_MSGS[node_id]['PUB_SOCKET'] = socket

    # Waiting for the listener thread sockets to connect
    time.sleep(3)

    # If it is a starter node, election starts
    if(starter):
        SHARED_THREAD_MSGS[node_id]['LEADER_MULTICAST'] = True
    
    # Waiting until LEADER multicast trigger from listener thread by lower id nodes
    while(SHARED_THREAD_MSGS[node_id]['LEADER_MULTICAST'] == False):
        pass

    print("PROCESS MULTICASTS LEADER MSG: ", node_id)

    # Multicasting election starts, sending leader message to higher id nodes
    for receiver_id in range(num_proc):
        if(receiver_id > node_id):
            leader_msg = {"sender_id": node_id, "receiver_id": receiver_id, "status": True}
            socket.send_string("LEADER", flags=zmq.SNDMORE)
            socket.send_json(leader_msg)
            time.sleep(0.3)

    # Waiting for response for 10+num_proc seconds as a timeout
    timeout = 10 + num_proc
    timeout_start = time.time()
    while SHARED_THREAD_MSGS[node_id]['RESP_MESSAGE'] == False:
        if(time.time() > timeout_start + timeout):
            break
        
    # If response is not received in 10 + num_proc seconds, Broadcast a Terminate Signal
    if(SHARED_THREAD_MSGS[node_id]['RESP_MESSAGE'] == False):
        print("PROCESS BROADCASTS TERMINATE MSG: {}".format(node_id))
        for receiver_id in range(num_proc):
            status = {"sender_id": node_id, "receiver_id": receiver_id, "msg": True}
            socket.send_string("TERMINATE", flags=zmq.SNDMORE)
            socket.send_json(status)
            time.sleep(0.3)

    # Waiting for terminate message
    while(SHARED_THREAD_MSGS[node_id]['TERMINATE_MESSAGE'] == False):
        pass
    
    listener_thread.join()
    

def responder(node_id, num_proc, SHARED_THREAD_MSGS):
    pid = os.getpid()
    print("RESPONDER STARTS:{}".format(node_id))

    context = zmq.Context()
    
    # Generating subscriber sockets for each process
    subscriber_sockets = [k for k in range(num_proc)]
    for proc_node_id in range(num_proc):
        socket = context.socket(zmq.SUB)
        port = 5550 + proc_node_id
        socket.connect(f"tcp://127.0.0.1:{port}")
        socket.subscribe("LEADER")
        socket.subscribe("RESP")
        socket.subscribe("TERMINATE")
        subscriber_sockets[proc_node_id] = socket

    # Listening all nodes
    while not SHARED_THREAD_MSGS[node_id]['TERMINATE_MESSAGE']:
        for proc_node_id in range(num_proc):
            socket = subscriber_sockets[proc_node_id]
            try:
                socket.RCVTIMEO = 100
                msg_type = socket.recv_string()
                msg = socket.recv_json()

                # Notifies the main thread to terminate
                if(msg_type == "TERMINATE" and msg['receiver_id'] == node_id):
                    SHARED_THREAD_MSGS[node_id]['TERMINATE_MESSAGE'] = True
                    break

                elif(msg_type == "LEADER" and msg['receiver_id'] == node_id and msg['sender_id'] < node_id):
                    # Responding to sender to notify there is a node with a higher node id
                    print("RESPONDER RESPONDS {} {}".format(node_id, msg['sender_id']))
                    resp_msg = {"sender_id": node_id, "receiver_id": msg['sender_id'], "status": True}
                    SHARED_THREAD_MSGS[node_id]['PUB_SOCKET'].send_string("RESP", flags=zmq.SNDMORE)
                    SHARED_THREAD_MSGS[node_id]['PUB_SOCKET'].send_json(resp_msg)

                    # When a node gets a leader message, it also multicasts a leader message
                    SHARED_THREAD_MSGS[node_id]['LEADER_MULTICAST'] = True

                elif(msg_type == "LEADER" and msg['sender_id'] > node_id):
                    SHARED_THREAD_MSGS[node_id]['LEADER_MULTICAST'] = True

                elif(msg_type == "RESP" and msg['receiver_id'] == node_id):
                    SHARED_THREAD_MSGS[node_id]['LEADER_MULTICAST'] = True
                    SHARED_THREAD_MSGS[node_id]['RESP_MESSAGE'] = True

            except:
                pass
            
if __name__ == '__main__':

    quests = sys.argv
    if(len(quests) == 4):
        
        num_proc = int(sys.argv[1])
        num_alive = int(sys.argv[2])
        num_starters = int(sys.argv[3])

        alive_nodes = random.sample(range(0,num_proc),num_alive)
        starter_nodes = random.sample(alive_nodes, num_starters)

        # Test Cases
        #num_proc = 10
        #alive_nodes = [2, 4, 1, 9, 0]
        #starter_nodes = [9, 4, 2]

        #alive_nodes = [8, 9, 0, 3]
        #starter_nodes = [9, 3]
                    
        SHARED_THREAD_MSGS = [dict() for k in range(num_proc)]

        for k in range(num_proc):
            SHARED_THREAD_MSGS[k]['LEADER_MULTICAST'] = False
            SHARED_THREAD_MSGS[k]['TERMINATE_MESSAGE'] = False
            SHARED_THREAD_MSGS[k]['RESP_MESSAGE'] = False
            SHARED_THREAD_MSGS[k]['PUB_SOCKET'] = ""

        print("Alives: \n",alive_nodes)
        print("Starters: \n",starter_nodes)

        alive_processes = []
        for node_id in alive_nodes:
            if(node_id in starter_nodes):
                starter = True
            else:
                starter = False
            proc = Process(target=leader, args=(node_id, starter, num_proc, SHARED_THREAD_MSGS))
            alive_processes.append(proc)

        # Start alive node processes
        for ap in alive_processes:
            ap.start()
        
        # Join alive node processes
        for ap in alive_processes:
            ap.join()
