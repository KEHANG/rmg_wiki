from rmgpy.data.rmg import database
from rmgpy.rmg.model import getFamilyLibraryObject
from rmgpy.kinetics import KineticsData
from rmgpy.data.kinetics.family import TemplateReaction
from rmgpy.rmg.model import Species

def pathwayGenerator(reactants, products, rmg, only_families):
	genRxn = database.kinetics.generateReactionsFromFamilies

	# LOOP starts
	newReactions = []
	rxt_mol_mutation_num = 1
	pdt_mol_mutation_num = 1
	for reactant in reactants:
		rxt_mol_mutation_num *= len(reactant.molecule)
	for product in products:
		pdt_mol_mutation_num *= len(product.molecule)

	for mutation_i in range(rxt_mol_mutation_num):
		rxts_mol = [spc.molecule[mutation_i%(len(spc.molecule))] for spc in reactants]
		for mutation_j in range(pdt_mol_mutation_num):
			pdts_mol = [spc.molecule[mutation_j%(len(spc.molecule))] for spc in products]

	        newReactions.extend(genRxn(reactants=rxts_mol,\
	            products=pdts_mol, only_families=only_families))

	rmg.reactionModel.newSpeciesList = []
	rmg.reactionModel.newReactionList = []
	rmg.reactionModel.processNewReactions(newReactions, reactants)

	# gen thermo and transport for new species
	for spec in rmg.reactionModel.newSpeciesList:
	    if not spec.hasThermo():
	        spec.generateThermoData(database)
	        spec.generateTransportData(database)

	for reaction in rmg.reactionModel.newReactionList:
	    family = getFamilyLibraryObject(reaction.family)

	    # If the reaction already has kinetics (e.g. from a library),
	    # assume the kinetics are satisfactory
	    if reaction.kinetics is None:
	        # Set the reaction kinetics
	        kinetics, source, entry, isForward = rmg.reactionModel.generateKinetics(reaction)
	        reaction.kinetics = kinetics
	        # Flip the reaction direction if the kinetics are defined in the reverse direction
	        if not isForward:
	            reaction.reactants, reaction.products = reaction.products, reaction.reactants
	            reaction.pairs = [(p,r) for r,p in reaction.pairs]
	        if family.ownReverse and hasattr(reaction,'reverse'):
	            if not isForward:
	                reaction.template = reaction.reverse.template
	            # We're done with the "reverse" attribute, so delete it to save a bit of memory
	            delattr(reaction,'reverse')

	# For new reactions, convert ArrheniusEP to Arrhenius, and fix barrier heights.
	# self.newReactionList only contains *actually* new reactions, all in the forward direction.
	for reaction in rmg.reactionModel.newReactionList:
	    # convert KineticsData to Arrhenius forms
	    if isinstance(reaction.kinetics, KineticsData):
	        reaction.kinetics = reaction.kinetics.toArrhenius()
	    #  correct barrier heights of estimated kinetics
	    if isinstance(reaction,TemplateReaction) or isinstance(reaction,DepositoryReaction): # i.e. not LibraryReaction
	        reaction.fixBarrierHeight() # also converts ArrheniusEP to Arrhenius.

	    if rmg.reactionModel.pressureDependence and reaction.isUnimolecular():
	        # If this is going to be run through pressure dependence code,
	        # we need to make sure the barrier is positive.
	        reaction.fixBarrierHeight(forcePositive=True)

def loadSpeciesDictionary(path):
    """
    Very similar method with `loadSpeciesDictionary` in RMG-Py. Here this method
    doesn't generateResonanceIsomers for the created species, will just keep it 
    as it is.
    """
    speciesDict = {}
    
    inerts = [Species().fromSMILES(inert) for inert in ('[He]', '[Ne]', 'N#N', '[Ar]')]
    with open(path, 'r') as f:
        adjlist = ''
        for line in f:
            if line.strip() == '' and adjlist.strip() != '':
                # Finish this adjacency list
                species = Species().fromAdjacencyList(adjlist)
                label = species.label
                for inert in inerts:
                    if inert.isIsomorphic(species):
                        species.reactive = False
                        break
                speciesDict[label] = species
                adjlist = ''
            else:
                if "InChI" in line:
                    line = line.split()[0] + '\n'
                if '//' in line:
                    index = line.index('//')
                    line = line[0:index]
                adjlist += line

    return speciesDict

def loadInput(filename):
	reactants_list = []
	products_list = []
	family_list = []
	with open(filename, 'rb') as input_file:
		lines = input_file.readlines()
		for line in lines:
			if line != '\n' and not line.startswith("!"):
				if 'PATHWAY' in line:
					pass
				elif 'END' in line:
					break
				else:
					rhs = line.strip().split("==")[0]
					lhs = line.strip().split("==")[1]

					family = rhs.strip().split(":")[0]
					reactants_tokens = rhs.strip().split(":")[1].split()
					products_tokens = lhs.strip().split()

					reactants = filter(lambda item:item!='+', reactants_tokens)
					products = filter(lambda item:item!='+', products_tokens)

					family_list.append(family)
					reactants_list.append(reactants)
					products_list.append(products)
	return family_list, reactants_list, products_list
