def extractPolycyclicGroups(molecule):
    """
    Extract polycyclic functional groups from a real molecule
    """
    struct = molecule.copy(deep=True)
    # Saturate the structure if it is a radical
    if struct.isRadical():
        struct.saturate()
    struct.deleteHydrogens()
    
    polyRings = struct.getPolycyclicRings()
    groups = [convertCycleToGroup(ring) for ring in polyRings]
    
    return groups
                
def convertCycleToGroup(cycle):
    """
    This function converts a list of atoms in a cycle to a functional Group object
    """
    from rmgpy.molecule.group import GroupAtom, GroupBond, Group
    
    # Create GroupAtom object for each atom in the cycle, label the first one in the cycle with a *
    groupAtoms = {}
    bonds = []
    for atom in cycle:
        groupAtoms[atom] = GroupAtom(atomType=[atom.atomType],
                                     radicalElectrons=[0],
                                     label='*' if cycle.index(atom)==0 else '')
                
    group = Group(atoms=groupAtoms.values())            
    
    # Create GroupBond for each bond between atoms in the cycle, but not outside of the cycle
    for atom in cycle:
        for bondedAtom, bond in atom.edges.iteritems():
            if bondedAtom in cycle:
                # create a group bond with the same bond order as in the original molecule,
                # if it hasn't already been created
                if not group.hasBond(groupAtoms[atom],groupAtoms[bondedAtom]):
                    group.addBond(GroupBond(groupAtoms[atom],groupAtoms[bondedAtom],order=[bond.order]))
            else:
                pass
        
    group.update()
    
    return group

def displayThermo(thermoData):
    print 'H298 = {0} kcal/mol'.format(thermoData.H298.value_si/4184)
    print 'S298 = {0} cal/mol*K'.format(thermoData.S298.value_si/4.184)
def compareThermoData(thermoData1, thermoData2):
    delH = thermoData1.H298.value_si - thermoData2.H298.value_si
    print 'Difference in H298 = {0} kcal/mol'.format(delH/4184)
    delS = thermoData1.S298.value_si - thermoData2.S298.value_si
    print 'Difference S298 = {0} cal/mol*K'.format(delS/4.184)
    #Tdata = [300,500,1000,2000]
    #for T in Tdata:
    #    delCp = thermoData1.getHeatCapacity(T) - thermoData2.getHeatCapacity(T)
    #    print 'Difference in Cp at {0} = {1} cal/mol*K'.format(T, delCp/4.184)