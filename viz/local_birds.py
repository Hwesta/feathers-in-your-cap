#!/usr/bin/env python3

import networkx as nx
import csv
import matplotlib.pyplot as plt

def get_genus_species():
    with open('hollybirds.txt') as f:
        species = f.readlines()
    species = [s.strip() for s in species]
    return species

def get_order_family():
    """Return dict with key=species, value=[family, order]"""
    taxonomy = {}
    with open('../reference/eBird_Taxonomy_v2016_9Aug2016-from-ods.csv', newline='') as f:
        csvreader = csv.DictReader(f)
        for row in csvreader:
            species = row['SCI_NAME']
            family = row['FAMILY']
            order = row['ORDER']
            taxonomy[species] = [family, order]

    return taxonomy


def main():
    G = nx.Graph()

    G.add_node("Aves")

    species_list = get_genus_species()
    taxonomy = get_order_family()

    shell1=['Aves']
    shell2=[]
    shell3=[]
    shell4=[]

    for species in species_list:
        family, order = taxonomy[species]
        shell2.append(order)
        shell3.append(family)
        shell4.append(species)
        G.add_edge(species, family)
        G.add_edge(family, order)
        G.add_edge(order, "Aves")

    options = {
        'with_labels': True,
        'node_color': 'black',
        'node_size': 10,
        'node_shape': '8',
        'width': 1,
        'edge_color': 'green',
        'font_size': 6,
    }

    # Using pygraphviz
    # A = nx.nx_agraph.to_agraph(G)
    # A.node_attr['shape'] = 'none'
    # A.node_attr['fontsize'] = 6
    # A.node_attr['labelloc'] = 'c'
    # A.node_attr['fillcolor'] = 'transparent'
    # A.edge_attr['color'] = 'green'

    # A.layout('twopi')
    # A.draw("file.png")

    # Using matplotlib & shell
    # nx.draw_shell(G,
    #     nlist=[shell1,shell2,shell3,shell4],
    #     **options
    # )
    # plt.show()
    # plt.savefig('file.png')

    pos=nx.nx_agraph.graphviz_layout(G, prog='twopi', args='')
    plt.figure(figsize=(8,8))
    nx.draw(G,
        pos,
        **options
    ) # node_size=20,alpha=0.5,node_color="blue", with_labels=False)
    plt.axis('equal')
    # plt.savefig('circular_tree.png')
    plt.show()

if __name__ == '__main__':
    main()