# 文档说明
获取apollo cyberRT 发布/订阅者关系，生成json文件，并绘制关系图（apollo 6.0中测试通过）。
## 安装依赖
apollo docker 终端内：
> sudo apt update  

安装依赖:  
> pip install graphviz  
> pip install simplejson 


## 编译
将两个python文件放入apollo内，
> bazel build {code-path}/cyber_graph/...

## 运行  
第一步，必须运行在docker内，收集通道信息，生成节点，通道关系json文件：  
> {bin-path}/cyber_graph  [-h]  


第二步，只是利用json文件绘制关系图，只需有python环境就可以：  
> {bin-path}/cyber_graph_draw  [-h]  

或者docker外
> python cyber_graph_draw.py -h

附带测试数据：
> python cyber_graph_draw.py -i data/cyber_graph.json -o data/test
