#!/usr/bin/env python3

import networkx as nx
import csv
import matplotlib.pyplot as plt

def get_genus_species(name='common'):
    if name == 'common':
        filename = 'hollybirds-com.txt'
    elif name == 'sci':
        filename = 'hollybirds.txt'
    with open(filename) as f:
        species = f.readlines()
    species = [s.strip() for s in species]
    return species

def get_order_family(name='common'):
    """Return dict with key=species, value=[family, order]"""
    taxonomy = {}
    with open('../reference/eBird_Taxonomy_v2017_18Aug2017.csv', newline='', encoding='windows-1252') as f:
        csvreader = csv.DictReader(f)
        for row in csvreader:
            if name == 'common':
                species = row['PRIMARY_COM_NAME']
            elif name == 'sci':
                species = row['SCI_NAME']
            family = row['FAMILY']
            order = row['ORDER1']
            if row['CATEGORY'] in ('spuh', 'slash', 'hybrid', 'intergr', 'form'):
                continue
            taxonomy[species] = [family, order]

    return taxonomy


def main():
    G = nx.Graph()

    G.add_node("Aves")

    name = 'common'
    species_list = get_genus_species(name)
    taxonomy = get_order_family(name)

    for species in species_list:
        try:
            family, order = taxonomy[species]
        except KeyError:
            print('skipping', species)
            continue
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

    # Using matplotlib & twopi
    pos=nx.nx_agraph.graphviz_layout(G, prog='twopi', args='')
    plt.figure(figsize=(20,20))
    nx.draw(G,
        pos,
        **options
    ) # node_size=20,alpha=0.5,node_color="blue", with_labels=False)
    plt.axis('equal')
    plt.savefig('file.png')
    plt.show()

if __name__ == '__main__':
    main()