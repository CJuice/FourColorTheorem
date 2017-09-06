###################################
# Script:  AdjacentSelectionClass.py
# Author:  Conrad Schaefer
# Date Created:  09/06/2017
# Purpose:  This class gets imported into the main script. It defines a method that returns a layer with adjacent polygons selected.
# Inputs:  
# Outputs:  
# Modifications: 
###################################
class AdjacentSelectionClass(object):
    '''This class contains a function to be reused by the main script'''
    def __init__(self, masterFeatureLayer, duplicateFeatureLayer, fieldName):
        self.masterFeatureLayer = masterFeatureLayer
        self.duplicateFeatureLayer = duplicateFeatureLayer
        self.fieldName = fieldName

    def selectAdjacent(self):
        import arcpy.management
        #For each feature, select all adjacent features in duplicate that share a line segment
        selection = arcpy.SelectLayerByLocation_management(in_layer=self.duplicateFeatureLayer,
                                               overlap_type="SHARE_A_LINE_SEGMENT_WITH",
                                               select_features=self.masterFeatureLayer,search_distance=None,
                                               selection_type="NEW_SELECTION",
                                               invert_spatial_relationship=None)
        #Remove the feature identical to the selecting feature
        selection = arcpy.SelectLayerByLocation_management(in_layer=selection,
                                               overlap_type="ARE_IDENTICAL_TO",
                                               select_features=self.masterFeatureLayer, search_distance=None,
                                               selection_type="REMOVE_FROM_SELECTION",
                                               invert_spatial_relationship=None)

        return selection
