###################################
# Script:  MaxAdjacencyDetermination2.py
# Author:  CJuice
# Date Created:  09/06/2017
# Purpose:  Determines the maximum adjacency at a primary and secondary level. Primary is all polygons that share a line segment with the feature of focus. Every feature is iterated over and evaluated. A secondary adjacency is determined by examinging the primary adjacent features for each feature of focus. Each secondary feature is iterated over and it is determined how many of the other secondary features are adjacent to the secondary feature of focus. Both values are written to their own unique field, created during the script.
# Inputs:  Workspace, Scratch Workspace, Feature Layer of Interest
# Outputs:  None but messages to the geoprocessing window and an edited feature class.
# Modifications: Amended the previous version to use in_memory storage for the tempFC rather than writing it to a
#                   geodatabase. Creating a new feature class is time consumptive.
###################################
import arcpy, sys
import AdjacentSelectionClass

arcpy.env.overwriteOutput = True

#Establish Variables
strFirstLevelAdjacencyFieldName = "FirstLevelAdjacency"
strSecondLevelAdjacencyFieldName = "SecondLevelAdjacency"
lsLayerUniqueIDField = ['OBJECTID','OID']
intFeatureCount = 0
strWorkspace = arcpy.GetParameter(0)
strScratchWorkspace = arcpy.GetParameter(1)
strMasterFeatureClass = arcpy.GetParameter(2)
arcpy.env.workspace = strWorkspace

#Add fields to master feature class
arcpy.AddField_management(in_table=strMasterFeatureClass,field_name=strFirstLevelAdjacencyFieldName,field_type="SHORT",
                          field_precision=None,field_scale=None,field_length=None,field_alias=None,
                          field_is_nullable=None,field_is_required=None,field_domain=None)
arcpy.AddMessage(strFirstLevelAdjacencyFieldName + " field added")
arcpy.AddField_management(in_table=strMasterFeatureClass,field_name=strSecondLevelAdjacencyFieldName,field_type="SHORT",
                          field_precision=None,field_scale=None,field_length=None,field_alias=None,
                          field_is_nullable=None,field_is_required=None,field_domain=None)
arcpy.AddMessage(strSecondLevelAdjacencyFieldName + " field added")

#Make a feature layer of the master, and make a copy to serve as the duplicate
lyrMaster = arcpy.MakeFeatureLayer_management(in_features=strMasterFeatureClass,
                                              out_layer="Master",
                                              where_clause=None,
                                              workspace=strScratchWorkspace,
                                              field_info=None)
lyrDuplicate = arcpy.MakeFeatureLayer_management(in_features=strMasterFeatureClass,
                                                 out_layer="Duplicate",
                                                 where_clause=None,
                                                 workspace=strScratchWorkspace,
                                                 field_info=None)

#Iterates through features in master, selecting all adjacent, return selection
lsObjectID = []
try:
    with arcpy.da.SearchCursor(lyrMaster, lsLayerUniqueIDField[0]) as cursor:
        for row in cursor:
            lsObjectID.append(row[0])
except:
    arcpy.AddWarning("(1) Feature layer may not contain the field " + lsLayerUniqueIDField[0])
    sys.exit()

for ID in lsObjectID:
    intFeatureCount+=1
    #Select a feature based on its ObjectID
    featureOfFocus = arcpy.SelectLayerByAttribute_management(in_layer_or_view=lyrMaster,
                                                             selection_type="NEW_SELECTION",
                                                             where_clause=(lsLayerUniqueIDField[0] + '=' + str(ID)))

    #Initiate the object to access the method
    objPrimaryAdjacencyCheck_1 = AdjacentSelectionClass.AdjacentSelectionClass(featureOfFocus, lyrDuplicate, strFirstLevelAdjacencyFieldName)

    #Run the selectAdjacent() method to return a selection
    adjacentFeaturesSelection_1 = objPrimaryAdjacencyCheck_1.selectAdjacent()

    #Count the number of primary adjacent features and write the value to the field
    intPrimaryAdjacencyCount = arcpy.GetCount_management(adjacentFeaturesSelection_1)
    arcpy.AddMessage("Primary Adjacency Count: " + str(intPrimaryAdjacencyCount))
    arcpy.CalculateField_management(in_table=featureOfFocus,
                                    field=strFirstLevelAdjacencyFieldName,
                                    expression=intPrimaryAdjacencyCount,
                                    expression_type="PYTHON",
                                    code_block=None)

    #Capture the selected adjacent features in the duplicate layer and save them as a temporary feature class
    strTempFCName = "tempFC"
        #Using in_memory, instead of creating a feature class in a gdb, to speed up the process.
    arcpy.FeatureClassToFeatureClass_conversion(in_features=adjacentFeaturesSelection_1,
                                                out_path="in_memory",
                                                out_name=strTempFCName,
                                                where_clause=None,
                                                field_mapping=None,
                                                config_keyword=None)

        #The workspace environment defined at the start creates an issue. Change it to in_memory before running this next part.
    arcpy.env.workspace = "in_memory"
    if arcpy.Exists("tempFC"):
        lyrAdjacentFeaturesIsolatedMaster = arcpy.MakeFeatureLayer_management(in_features=strTempFCName,
                                                                              out_layer="SecondLevelMaster",
                                                                              where_clause=None,
                                                                              workspace=strScratchWorkspace,
                                                                              field_info=None)
        lyrAdjacentFeaturesIsolatedDuplicate = arcpy.MakeFeatureLayer_management(in_features=strTempFCName,
                                                                                 out_layer="SecondLevelDuplicate",
                                                                                 where_clause=None,
                                                                                 workspace=strScratchWorkspace,
                                                                                 field_info=None)
    else:
        arcpy.AddMessage("tempFC Does Not Exist")
        sys.exit()

    #Most feature classes have an 'OBJECTID' field. Some, including in_memory, have 'OID'. The code must account for this difference.
    desc = arcpy.Describe(strTempFCName)
    lsFields = desc.fields
    lsFieldNames = []
    for field in lsFields:
        lsFieldNames.append(field.name)
    strUniqueIDField = ""
    if lsLayerUniqueIDField[0] in lsFieldNames:
        strUniqueIDField = lsLayerUniqueIDField[0]
    elif lsLayerUniqueIDField[1] in lsFieldNames:
        strUniqueIDField = lsLayerUniqueIDField[1]
    else:
        arcpy.AddWarning("Neither OBJECTID nor OID exists.")
        sys.exit()

    #Make a list of the numeric values in the object ID field for later use in selectlayerbyattribute
    lsObjectID_2 = []
    try:
        with arcpy.da.SearchCursor(lyrAdjacentFeaturesIsolatedMaster, strUniqueIDField) as cursor2:
            for row in cursor2:
                lsObjectID_2.append(row[0])
    except:
        arcpy.AddWarning("(2) Feature layer may not contain the field " + strUniqueIDField)
        sys.exit()

    #Step through the list of id's and use them to select the master feature. The, select all that are adjacent. The data in this
    #   loop is the primary adjacent features, so it's a small subset of the entire feature class.
    lsSecondarySelectionCounts = []
    for ID2 in lsObjectID_2:
        featureOfFocus2 = arcpy.SelectLayerByAttribute_management(in_layer_or_view=lyrAdjacentFeaturesIsolatedMaster,
                                                                  selection_type="NEW_SELECTION",
                                                                  where_clause=(strUniqueIDField + '=' + str(ID2)))
        objPrimaryAdjacencyCheck_2 = AdjacentSelectionClass.AdjacentSelectionClass(featureOfFocus2,
                                                                                  lyrAdjacentFeaturesIsolatedDuplicate,
                                                                                  strSecondLevelAdjacencyFieldName)
        adjacentFeaturesSelection_2 = objPrimaryAdjacencyCheck_2.selectAdjacent()
        resultSecondaryAdjacencyCount = arcpy.GetCount_management(adjacentFeaturesSelection_2) #Note: returns a result object, not a value of type number or string
        strSecondaryAdjacencyCount = str(resultSecondaryAdjacencyCount)
        intSecondaryAdjacencyCount = int(strSecondaryAdjacencyCount)
        lsSecondarySelectionCounts.append(intSecondaryAdjacencyCount)

    intSecondaryAdjacencyCountMax = max(lsSecondarySelectionCounts)
    arcpy.AddMessage("Max Secondary Adjacency: " + str(intSecondaryAdjacencyCountMax))
    arcpy.CalculateField_management(in_table=featureOfFocus,
                                    field=strSecondLevelAdjacencyFieldName,
                                    expression=intSecondaryAdjacencyCountMax,
                                    expression_type="PYTHON",
                                    code_block=None)
    arcpy.AddMessage("Feature Count: " + str(intFeatureCount))
    arcpy.Delete_management("in_memory", data_type=None)
    arcpy.AddMessage("--------")


# TODO: Code breaking down after this point.
