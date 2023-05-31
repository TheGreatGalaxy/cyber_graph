#!/usr/bin/env python3
# ****************************************************************************
# Copyright 2019 The Apollo Authors. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ****************************************************************************

import math
import os
import sys
import time
import threading
from threading import Thread
from typing import Tuple
import socket


from optparse import OptionParser
import simplejson as json

from cyber.python.cyber_py3 import cyber_time
from cyber.python.cyber_py3 import cyber
from cyber.proto.role_attributes_pb2 import RoleAttributes

class HostIp:
  def __init__(self):
    self.ips = []
    ip0 = socket.gethostbyname(socket.gethostname())
    self.ips.append(ip0)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip1 = s.getsockname()[0]
    self.ips.append(ip1)
    print("Gather local machine ip: \n", self.ips)


class ChannelListener(object):
  def __init__(self, node_name,channel_name, window_size=10):
    self.lock = threading.Lock()
    self.node_name = node_name
    self.channel_name = channel_name
    self.bytes = []
    self.times = []
    self.window_size = window_size
  
  def CallBack(self, raw_data):
    with self.lock:
      t = time.time()
      self.times.append(t)
      self.bytes.append(len(raw_data))
      assert(len(self.times) == len(self.bytes))

      if len(self.times) > self.window_size:
          self.times.pop(0)
          self.bytes.pop(0)

  def GetResults(self) -> Tuple[bool, dict]:
    with self.lock:
      n = len(self.times)
      if n < self.window_size:
        return (False, "")
      else:
        tn = time.time()
        t0 = self.times[0]
        total = sum(self.bytes)
        dura = tn - t0
        bytes_per_s = total / dura
        if bytes_per_s < 1000:
            bw = f'{bytes_per_s:.2f}B/s'
        elif bytes_per_s < 1000000:
            bw = f'{bytes_per_s / 1000:.2f}KB/s'
        else:
            bw = f'{bytes_per_s / 1000000:.2f}MB/s'
        hz = f'{(n / dura):.2f}Hz'
        res = {"node": self.node_name, "channel": self.channel_name, "bw": bw, "Hz": hz, "count": n}
        print("\nGather channel info: \n", res)
        return (True, res)

class Gather:
  def __init__(self, options):
    self.options = options
    self.listeners = dict()
    self.host_ip = HostIp()
    self.nodes_info = []
    self.edges_info = dict()


  def GatherChannels(self):
      lnode = cyber.Node("listener_node")
      for nf in self.nodes_info:
        n_name = nf["node_name"]
        writing_channels = nf["writers"]
        if len(writing_channels) <= 0:
          continue
        for channel in writing_channels:
          if channel in self.listeners.keys():
            print("WARNING: There is a same channel name: ", channel)
            continue
          lis = ChannelListener(n_name, channel, self.options.window_size)
          lnode.create_rawdata_reader(channel, lis.CallBack)
          self.listeners[channel] = lis
          # print("reader to [%s]" % channel)
      
      st = time.time()
      delta_t = 0
      while delta_t < self.options.duration and len(self.listeners.keys()) > 0:
        now = time.time()
        delta_t = now - st
        channels, listeners = list(self.listeners.keys()), list(self.listeners.values())
        for c, l in zip(channels, listeners):
          done, res = l.GetResults()
          if done:
            self.edges_info[c] = res
            self.listeners.pop(c)
        time.sleep(1.0)
      print("\nWARNING: The following channels received none message: \n", self.listeners.keys())
      et = time.time()
      print(f"\ncollected {et - st:.3f}s data.")


  def GatherNodes(self):
      nodes = cyber.NodeUtils.get_nodes()
      for node_name in nodes:
        raw_data = cyber.NodeUtils.get_node_attr(node_name, sleep_s=0)
        try:
            msg = RoleAttributes()
            msg.ParseFromString(raw_data)
            assert(node_name == msg.node_name)
        except:
            print("RoleAttributes ParseFromString failed. size is ",
                  len(raw_data))
            return
        # print("node info: \n", msg)
        reading_channels = sorted(cyber.NodeUtils.get_readersofnode(node_name, 0))
        writing_channels = sorted(cyber.NodeUtils.get_writersofnode(node_name, 0))
        info = dict()
        info["node_name"]=node_name
        info["host_name"]=msg.host_name
        info["host_ip"]=msg.host_ip
        info["process_id"]=msg.process_id
        info["readers"]=reading_channels
        info["writers"]=writing_channels
        if self.options.local_nodes and (msg.host_ip not in self.host_ip.ips):
          continue
        self.nodes_info.append(info)

  def DumpNodesInfo2Json(self):
    file = self.options.output
    print(f'\n**** Will save to file: {file} ****')
    with open(file, "w") as f:
      json.dump({"nodes": self.nodes_info, "edges":self.edges_info}, f)


  def Run(self):
    self.GatherNodes()
    self.GatherChannels()
    self.DumpNodesInfo2Json()

if __name__ == '__main__':
    parser = OptionParser(
        usage="usage: cyber_graph [OPTIONS... [VALUE] ]")
    parser.add_option("-l", "--local",
                      dest="local_nodes", default=False,
                      action="store_true",
                      help="Only get nodes running in local machine. Defaule is false")

    parser.add_option("-o", "--output", type="string",
                  default="/apollo/cyber_graph.json", dest="output",
                  help="The output file. Default is /apollo/cyber_graph.json")
    
    parser.add_option("-w", "--window_size", type="int",
                  dest="window_size", default=10,
                  help="The window size for claculating bandwidth and hertz.")

    parser.add_option("-d", "--duration", type="int",
                  dest="duration", default=30,
                  help="Max seconds for getting at least window_size frames of all channel. Default is 30s.")    

    (options, args) = parser.parse_args()
    cyber.init()
    gather = Gather(options)
    gather.Run()
    cyber.shutdown()
