#! /usr/bin/python 

from mininet.net import Mininet
from mininet.net import Mininet,CLI
from mininet.node import OVSKernelSwitch, Host
from mininet.link import TCLink,Link
from mininet.log import setLogLevel, info

import time, os

import numpy as np


class MininetBackEnd(object):

    def init_params(self, mu, sigma, link_bw, sla_bw):
        self.mu = float(mu)
        self.sigma = float(sigma)
        self.sla_bw = float(sla_bw)

        self.link_bw = float(link_bw)
     
    def reset_links(self):
        self.current_link_failure = False
        self.previous_link_failure = False

        self.active_link = 0 # internet by default
        self.episode_over = False

        self.take_measurements()

    def __init__(self, mu, sigma, link_bw, sla_bw, seed):

        np.random.seed(seed)

        self.init_params(mu, sigma, link_bw, sla_bw)

        self.net = Mininet( topo=None, listenPort=6633, ipBase='10.0.0.0/8')

        self.h1 = self.net.addHost( 'host1', mac = '00:00:00:00:00:01', ip='10.0.0.1' )
        self.h2 = self.net.addHost( 'host2', mac = '00:00:00:00:00:02', ip='10.0.0.2' )
        self.h3 = self.net.addHost( 'noise1', mac = '00:00:00:00:00:03', ip='10.0.0.3' )
        self.h4 = self.net.addHost( 'noise4', mac = '00:00:00:00:00:04', ip='10.0.0.4' )
        self.s1 = self.net.addSwitch( 'edge1', cls=OVSKernelSwitch, protocols='OpenFlow13' )
        self.s2 = self.net.addSwitch( 'edge2', cls=OVSKernelSwitch, protocols='OpenFlow13' )
        self.s3 = self.net.addSwitch( 'core1', cls=OVSKernelSwitch, protocols='OpenFlow13' )
        self.s4 = self.net.addSwitch( 'core2', cls=OVSKernelSwitch, protocols='OpenFlow13' )
        self.net.addLink( self.h1, self.s1, cls=Link)
        self.net.addLink( self.h2, self.s2, cls=Link)
        self.net.addLink( self.h3, self.s1, cls=Link)
        self.net.addLink( self.h4, self.s2, cls=Link)
        self.net.addLink( self.s1, self.s3, cls=TCLink, bw=self.link_bw)
        self.net.addLink( self.s1, self.s4, cls=TCLink, bw=self.link_bw)
        self.net.addLink( self.s2, self.s3, cls=TCLink, bw=self.link_bw)
        self.net.addLink( self.s2, self.s4, cls=TCLink, bw=self.link_bw)

        self.net.start()


        # add flows

        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=20,ip,nw_dst=10.0.0.2,actions=output:4')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,ip,nw_dst=10.0.0.1,actions=output:1')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,ip,nw_dst=10.0.0.3,actions=output:2')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,arp,nw_dst=10.0.0.1,actions=output:1')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,arp,nw_dst=10.0.0.3,actions=output:2')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,arp,nw_dst=10.0.0.2,actions=normal')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,arp,nw_dst=10.0.0.4,actions=normal')
        self.s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=10,ip,nw_dst=10.0.0.4,actions=output:4')

        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=20,ip,nw_dst=10.0.0.1,actions=output:4')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,ip,nw_dst=10.0.0.2,actions=output:1')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,ip,nw_dst=10.0.0.4,actions=output:2')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,arp,nw_dst=10.0.0.2,actions=output:1')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,arp,nw_dst=10.0.0.4,actions=output:2')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,arp,nw_dst=10.0.0.1,actions=normal')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,arp,nw_dst=10.0.0.3,actions=normal')
        self.s2.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  edge2 priority=10,ip,nw_dst=10.0.0.3,actions=output:4')


        self.s3.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  core1 priority=10,in_port=1,actions=output:2')
        self.s3.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  core1 priority=10,in_port=2,actions=output:1')
        
        self.s4.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  core2 priority=10,in_port=1,actions=output:2')
        self.s4.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow  core2 priority=10,in_port=2,actions=output:1')

        #CLI(self.net)

        # start udp  traffic receiver - simulate other traffic
        self.h4.cmd("iperf  -u -s -i 1 >& /tmp/udp_server.log &")

        # start host tcp traffic receiver - simulate main flow
        self.h2.cmd("iperf  -s -i 1  >& /tmp/tcp_server.log &")

        self.reset_links()


    def cleanup(self):
        self.net.stop()


    def take_measurements(self):
        """ Send udp traffic and then take bandwidth measurement """

        # cleanup /tmp for logs

        os.system("rm /tmp/*.log")

        # send udp traffic  - simulate other flow
        ip = self.h4.IP()
        bw = np.random.normal(self.mu, self.sigma) 
        cmd = "iperf -u -c {0} -b  {1}M -t 10  >& /tmp/udp_client.log &".format(ip, bw)
        #info(cmd)
        self.h3.cmd(cmd)


        ## we measure  internet link only, MPLS link => full BW 
        if self.active_link == 0:   
            # send tcp  traffic  - main flow
            ip = self.h2.IP()
            cmd = "iperf -c {0} -t 5 >& /tmp/tcp_client.log &".format(ip)

            #info(cmd)
            self.h1.cmd(cmd)

        # wait for  traffic flow to settle
        # if you set this too low, output file will not be generated properly !!!!!!
        time.sleep(15)


        # always measure internet link available bw
        self.available_bw = float(self.link_bw) - float(self.read_udp_bw())

        if self.available_bw < 0.0:
            self.available_bw = 0.0

        ## we measure  internet link only, MPLS link => full BW 
        if self.active_link == 0:   
            self.current_bw = self.read_tcp_bw()
        else:
            self.current_bw = self.link_bw
        

        
    def read_tcp_bw(self):
        bw = ['None']
        with open('/tmp/tcp_client.log') as f:
            for line in f:
                #print ('line = ', line)
                if 'bits/sec' in line:
                    line = line.replace('-', ' ')
                    fields = line.strip().split()
                    # Array indices start at 0 unlike AWK

                    if len(fields) > 7:
                        bw.append(fields[7])

        #print(bw[-1])
        return(bw[-1])


    def read_udp_bw(self):
        bw = ['None']
        with open('/tmp/udp_client.log') as f:
            for line in f:
                #print ('line = ', line)
                if 'bits/sec' in line:
                    line = line.replace('-', ' ')
                    fields = line.strip().split()
                    # Array indices start at 0 unlike AWK
    
                    if len(fields) > 7:
                        bw.append(fields[7])

        #print(bw[-1])
        return(bw[-1])

    def switch_flows(self, action):
        if action == 0:
            channel = 4
        elif action == 1:
            channel = 3
        else:
            return

        cmd = "ovs-ofctl --protocols=OpenFlow13 add-flow  edge1 priority=20,ip,\
                    nw_dst=10.0.0.2,actions=output:{0}".format(channel)
        #info(cmd)
        self.s1.cmd(cmd)



    def switch_link(self, action):

        # if action specifies same link s before it is not a switch
        if action != self.active_link:
            self.switch_flows(action)
            

        ## action is 0 => link is internet
        ## action 1 => MPLS 
        self.active_link  = action

        self.take_measurements()

        ## Here is the logic that checks  two subsequent SLA failures
        self.current_link_failure = False

        # if current bandwidth less than SLA it is a failure
        if self.active_link == 0:
            if float(self.current_bw) < float(self.sla_bw):
                info ('current link failure')
                self.current_link_failure = True

                # if it failed in previous tick also, mark it a link failure
                if  self.previous_link_failure == True:
                    info ('previous link also failure, episode over')
                    self.episode_over = True
            
        # copy current to previous
        self.previous_link_failure = self.current_link_failure 
        
        return self.episode_over 

    def print_state(self):
        print ('active_link = ', be.active_link, 
                    'current_bw = ', be.current_bw,  'available bw = ', be.available_bw)
        

        
    
if __name__ == '__main__':
    setLogLevel( 'error' )
    be = MininetBackEnd(mu=5, sigma=2, link_bw=10, sla_bw=6, seed=100)
    be.print_state()

    be.switch_link(action=1)
    be.print_state()

    be.switch_link(action=0)
    be.print_state()

    be.switch_link(action=1)
    be.print_state()

    be.switch_link(action=0)
    be.print_state()

    be.cleanup()
 
