import tcdf
import torch
import pandas as pd
import numpy as np
import networkx as nx
import pylab
import copy
import matplotlib.pyplot as plt
import os
import sys

# os.chdir(os.path.dirname(sys.argv[0])) #uncomment this line to run in VSCode
class Causations():
    """Class responsible for causation finding with TCDF
    """

    def __init__(self,options,seed=111,cuda=False):
        self.kernel_size = int(options[2])
        self.levels = int(options[1])
        self.nrepochs = int(options[7])
        self.learningrate = float(options[6])
        self.optimizername = options[0]
        self.dilation_c = int(options[4])
        self.loginterval = int(options[5])
        self.seed=seed
        self.cuda=cuda
        self.significance=float(options[3])

    def getextendeddelays(self, gtfile, columns):
        """Collects the total delay of indirect causal relationships."""
        gtdata = pd.read_csv(gtfile, header=None)

        readgt=dict()
        effects = gtdata[1]
        causes = gtdata[0]
        delays = gtdata[2]
        gtnrrelations = 0
        pairdelays = dict()
        for k in range(len(columns)):
            readgt[k]=[]
        for i in range(len(effects)):
            key=effects[i]
            value=causes[i]
            readgt[key].append(value)
            pairdelays[(key, value)]=delays[i]
            gtnrrelations+=1
        
        g = nx.DiGraph()
        g.add_nodes_from(readgt.keys())
        for e in readgt:
            cs = readgt[e]
            for c in cs:
                g.add_edge(c, e)

        extendedreadgt = copy.deepcopy(readgt)
        
        for c1 in range(len(columns)):
            for c2 in range(len(columns)):
                paths = list(nx.all_simple_paths(g, c1, c2, cutoff=2)) #indirect path max length 3, no cycles
                
                if len(paths)>0:
                    for path in paths:
                        for p in path[:-1]:
                            if p not in extendedreadgt[path[-1]]:
                                extendedreadgt[path[-1]].append(p)
                                
        extendedgtdelays = dict()
        for effect in extendedreadgt:
            causes = extendedreadgt[effect]
            for cause in causes:
                if (effect, cause) in pairdelays:
                    delay = pairdelays[(effect, cause)]
                    extendedgtdelays[(effect, cause)]=[delay]
                else:
                    #find extended delay
                    paths = list(nx.all_simple_paths(g, cause, effect, cutoff=2)) #indirect path max length 3, no cycles
                    extendedgtdelays[(effect, cause)]=[]
                    for p in paths:
                        delay=0
                        for i in range(len(p)-1):
                            delay+=pairdelays[(p[i+1], p[i])]
                        extendedgtdelays[(effect, cause)].append(delay)

        return extendedgtdelays, readgt, extendedreadgt

    def runTCDF(self, df_data):
        """Loops through all variables in a dataset and return the discovered causes, time delays, losses, attention scores and variable names."""
        allcauses = dict()
        alldelays = dict()
        allreallosses=dict()
        allscores=dict()

        columns = list(df_data)
        for c in columns:
            idx = df_data.columns.get_loc(c)
            causes, causeswithdelay, realloss, scores = TCDF.findcauses(c, cuda=self.cuda, epochs=self.nrepochs, 
            kernel_size=self.kernel_size, layers=self.levels, log_interval=self.loginterval, 
            lr=self.learningrate, optimizername=self.optimizername,
            seed=self.seed, dilation_c=self.dilation_c, significance=self.significance, data=df_data)

            allscores[idx]=scores
            allcauses[idx]=causes
            alldelays.update(causeswithdelay)
            allreallosses[idx]=realloss

        return allcauses, alldelays, allreallosses, allscores, columns

    @staticmethod
    def plotgraph(alldelays,columns):
        """Plots a temporal causal graph showing all discovered causal relationships annotated with the time delay between cause and effect.

        Parameters
        ----------
            alldelays : `List[List[int]]`
                delays between each two variables
            columns : `List[str]`
                List with all variable names
        """
        G = nx.DiGraph()
        for c in columns:
            G.add_node(c)
        for pair in alldelays:
            p1,p2 = pair
            nodepair = (columns[p2], columns[p1])

            G.add_edges_from([nodepair],weight=alldelays[pair])
        
        edge_labels=dict([((u,v,),d['weight'])
                        for u,v,d in G.edges(data=True)])
        
        pos=nx.circular_layout(G)
        fig2, new_ax = plt.subplots()
        nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_labels, ax=new_ax)
        nx.draw(G,pos, node_color = 'white', edge_color='black',node_size=1000,with_labels = True, ax=new_ax)
        new_ax.collections[0].set_edgecolor("#000000") 

        fig2.show()

    def get_causation(self,datafiles):
        """ Finds causations between all variables in datafiles

            Parameters
            ----------
                alldelays : `pandas.DataFrame`
                    DataFrame containing all time series to be considered
            Returns
            -------
            `(List[List[int]], List[str])`
                All delays and variable names
        """
        # run TCDF
        allcauses, alldelays, allreallosses, allscores, columns = self.runTCDF(datafiles) #results of TCDF containing indices of causes and effects

        for pair in alldelays:
            print(columns[pair[1]], "causes", columns[pair[0]],"with a delay of",alldelays[pair],"time steps.")

        return alldelays, columns
