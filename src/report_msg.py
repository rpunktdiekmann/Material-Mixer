import bpy

def report_error(self,msg):
    self.report({'ERROR'},msg)

def report_warning(self,msg):
    self.report({'WARNING'},msg)