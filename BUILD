load("@rules_python//python:defs.bzl", "py_binary")
load("//tools/install:install.bzl", "install", "install_files")

package(
    default_visibility = ["//visibility:public"],
)

py_binary(
    name = "cyber_graph",
    srcs = ["cyber_graph.py"],
    deps = [
        "//cyber/proto:role_attributes_py_pb2",
        "//cyber/python/cyber_py3:cyber",
        "//cyber/python/cyber_py3:cyber_time",
    ],
)

py_binary(
    name = "cyber_graph_draw",
    srcs = ["cyber_graph_draw.py"],
    deps = [
    ],
)

install_files(
    name = "install",
    files = [
        ":cyber_graph.py",
        ":cyber_graph_draw.py",
    ],
)
