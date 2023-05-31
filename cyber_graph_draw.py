import graphviz
import simplejson as json
from optparse import OptionParser
import sys


class Draw:
  def __init__(self, options):
    self.in_file = options.in_file
    self.output = options.output if options.output != "" else options.in_file + '.png'
    self.engine = options.engine
    self.gd_title = options.graph_title
    self.gd = graphviz.Digraph(self.gd_title, filename=(self.gd_title + ".cv"), engine=self.engine, format='png',\
              graph_attr={"fontsize": '16'}, \
              node_attr={"fontsize": '10'}, 
              edge_attr={"fontsize": '10'})
    self.color = [
      "antiquewhite4", "aquamarine3", "azure3", "bisque2", "blue",
      "blueviolet", "brown4", "burlywood4", "cadetblue4", "chartreuse4",
      "chocolate4", "coral4", "cornsilk3", "cyan2", "darkgoldenrod",
      "darkolivegreen", "darkorange", "darkorchid", "darkseagreen3", 
      "darkslategray2", "darkviolet", "deeppink4", "deepskyblue4", "dodgerblue2", "firebrick2",
       "gold2", "goldenrod2"]
    self.channels = []
    self.channel2color = dict()
  def Load(self):
    with open(self.in_file, "r") as f:
      graph = json.load(f)
    self.nodes = graph["nodes"]
    for n in self.nodes:
      self.channels.extend(n["readers"])
      self.channels.extend(n["writers"])
    self.channels = list(set(self.channels))
    self.channels.sort()
    for i, c in enumerate(self.channels):
      self.channel2color[c] = self.color[i % len(self.color)]
    self.edges = graph["edges"]

  def CyberNode2Gnode(self):
    for cnode in self.nodes:
      name = cnode['node_name']
      readers = cnode['readers']
      writers = cnode['writers']
      self.gd.attr('node', shape='ellipse', style='filled', color='gold')
      self.gd.node(name)
      self.gd.attr('node', shape='box', style='filled', color='deepskyblue')
      for c in readers:
        self.gd.edge(c, name, color=self.channel2color[c])
      for c in writers:
        if c in self.edges.keys():
          edge = self.edges[c]
          if name == edge["node"]:
            continue
        self.gd.edge(name, c, color=self.channel2color[c])

  def AddEdges(self):
    self.gd.attr('node', shape='box', style='filled', color='deepskyblue')
    for edge_name, info in self.edges.items():
      desb = "bw: " + info["bw"] + " Hz: " + info["Hz"]
      self.gd.edge(info["node"], info["channel"], label=desb, color=self.channel2color[info["channel"]],
        fontcolor=self.channel2color[info["channel"]])

  def Run(self):
    self.Load()
    self.CyberNode2Gnode()
    self.AddEdges()
    self.gd.attr(overlap='false')
    self.gd.attr(label=self.gd_title + "\nEllipse is cyber node, box is channel name. The arrow‘s direction is the data flowing direction.\n"
        "If a channel(wirtted by a node , rather than readed by a node) "
        "doesn't have a label, means not received any message from this channel.\n"
        "")
    print(f"\n**** Save result to: {self.output} ****")
    self.gd.render(self.output, cleanup=True)

if __name__ == "__main__":
    parser = OptionParser(
        usage="usage: cyber_graph [OPTIONS... [VALUE] ]")
    parser.add_option("-i", "--in_file",
                      dest="in_file", default="/apollo/cyber_graph.json",
                      type="string",
                      help="Input file path. Default is /apollo/cyber_graph.json")

    parser.add_option("-o", "--output", type="string",
                  default="", dest="output",
                  help="The output file. Example /apollo/cyber_graph, the postfix will add automatically.")
    
    parser.add_option("-e", "--engine", type="string",
                  default="dot", dest="engine",
                  help="Draw engine: dot, circo")

    parser.add_option("-t", "--title", type="string",
                  default="cyber_graph", dest="graph_title",
                  help="The output file")

    (options, args) = parser.parse_args()
    draw = Draw(options)
    draw.Run()
