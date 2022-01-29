# bully

Bully leader election algorithm implementation for distributed systems.

# run

numProc is the total number of nodes, numAlive is the number of nodes that are alive - online and numStarters are the number of nodes that will initiate the protocol. Timeout is determined as num_proc + 10 seconds experimentally. After broadcast message you should wait some time in accordance with number of processes due to handling terminate messages, but eventually the program terminates.

    python bully.py numProc numProc, numStarters


# bully leader election algorithm

In BLE algorithm, multiple nodes can start the leader election protocol simultaneously. When a node realizes that the leader is unavailable, it multicasts
a LEADER message to all nodes with higher IDs. If the receiver is online, it responds with a RESP message. Therefore, if the initiator receives a response, it understands that a node with a higher ID is alive and it becomes passive listener. When a node receives a LEADER message, it also multicasts another LEADER message to nodes with higher IDS. Similar to the initiator, if it receives a response, it understands that a node with higher ID is alive. Otherwise, it understands that it is the node with highest ID2 and it broadcasts a TERMINATE message with its own ID. When other nodes receive the TERMINATE message, they learn the new message and they finalize the protocol. 

# specifications

Please click [here](https://github.com/alaattinyilmaz/bully/blob/main/bully-election-specs.pdf) link to read all spesifications.
