#!/usr/bin/python

from uConst import *
import os
import re

MN_pkg = ('ppm', 'other')


class NativePackage:

    def __init__(self, name, nptype, host, where, name_x64=None):
        self.name = name  # Filename
        self.name_x64 = name_x64 or name
        self.type = nptype or "rpm"
        self.host = host
        self.where = where
        self.package_name = None


class HelmPackage(object):

    def __init__(self, name, chart, version=None, group=None, host=None, script=None):
        self.name = name
        self.chart = chart
        self.version = version
        self.group = group
        self.host = host
        self.script = script

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)

    def grabVersionFromChart(self):
        if not self.chart:
            return self
        data = re.search("(^.+)-(\d+.\d+.\d+$)", self.chart)
        if not data:
            return self
        self.chart, self.version = list(data.groups())
        return self

    def getChartRepoLess(self):
        if not self.chart:
            return None
        data = re.search("^.+/(.+$)", self.chart)
        if data:
            return data.group(1)
        else:
            return self.chart

    def key(self):
        return (self.name, self.getChartRepoLess())


class PkgInstallation:

    def _node_init__(self, node):
        self.name = node.getAttribute("name")
        self.ctype = node.getAttribute("ctype")
        where = node.getAttribute("host")
        if where == "mn" or where == "ui":
            self.where_pkg = MN_pkg
        elif where == "no":
            self.where_pkg = None
        else:  # upgrade
            self.where_pkg = (self.name, self.ctype)

    def _pkg_init__(self, name, ctype, where):
        self.name = name
        self.ctype = ctype
        self.where_pkg = where

    def __init__(self, node=None, name=None, ctype=None, where=None):
        if node:
            PkgInstallation._node_init__(self, node)
        else:
            PkgInstallation._pkg_init__(self, name, ctype, where)

    def node(self, doc):
        rv = doc.createElement("PACKAGE")
        rv.setAttribute("name", self.name)
        rv.setAttribute("ctype", self.ctype)
        if self.where_pkg == ('ppm', 'other'):
            rv.setAttribute("host", "mn")
        elif self.where_pkg == (self.name, self.ctype):
            rv.setAttribute("host", "upgrade")
        else:
            rv.setAttribute("host", "no")

        return rv


def parseNativePackageNode(node):
    host = node.getAttribute("host") or "all"
    name = node.getAttribute("name")
    name_x64 = node.getAttribute("name_x64") or name
    ptype = node.getAttribute("type") or "rpm"
    where = None  # None will mean everywhere.

    return NativePackage(name, ptype, host, where, name_x64)


def parseHelmPackageNode(root_dir, node):
    name = node.getAttribute('name')
    chart = node.getAttribute('chart')
    version = node.getAttribute('version') or 'latest'
    group = node.getAttribute('group') or HelmGroup.OPTIONAL
    host = node.getAttribute('host') or 'upgrade'
    script = node.getAttribute('script') or None
    if script:
        script = os.path.abspath(os.path.join(root_dir, 'helm', script))

    return HelmPackage(name, chart, version, group, host, script)


__all__ = ["PkgInstallation", "NativePackage", "HelmPackage", "MN_pkg", "parseNativePackageNode", "parseHelmPackageNode"]
