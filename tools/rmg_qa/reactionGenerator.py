from rmgpy.data.rmg import database
from rmgpy.rmg.model import getFamily
from rmgpy.kinetics import KineticsData
from rmgpy.data.kinetics.family import TemplateReaction

def pathwayGenerator(rxtA, rxtB, pdtC, rmg, only_families):
	genRxn = database.kinetics.generateReactionsFromFamilies

	# LOOP starts
	newReactions = []
	for moleculeA in rxtA.molecule:
	    for moleculeB in rxtB.molecule:
	        for moleculeC in pdtC.molecule:
	            newReactions.extend(genRxn(reactants=[moleculeA, moleculeB],\
	            products=None, only_families=only_families))

	rmg.reactionModel.newSpeciesList = []
	rmg.reactionModel.newReactionList = []
	rmg.reactionModel.processNewReactions(newReactions, rxtA)

	# gen thermo and transport for new species
	for spec in rmg.reactionModel.newSpeciesList:
	    if not spec.hasThermo():
	        spec.generateThermoData(database)
	        spec.generateTransportData(database)

	for reaction in rmg.reactionModel.newReactionList:
	    family = getFamily(reaction.family)

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