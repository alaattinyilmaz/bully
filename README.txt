# CS534 - HW4 - Emir Alaattin Yilmaz

# RUN

python bully.py numProc numProc, numStarters

# EXPLANATION

Timeout is determined as num_proc + 10 seconds experimentally. After broadcast message you should wait some time in accordance with number of processes due to handling terminate messages, but eventually the program terminates.