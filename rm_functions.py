#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Purpose
-------

This module is used by the Chewie-NS to delete data.


Expected input
--------------

It is necessary to specify the execution mode through the
following argument:

- ``-m``, ``mode`` :

    - e.g.: ``schema`` or ``loci`` or ``alleles`` or ``splinks`` or ``sclinks``

Code documentation
------------------
"""


import os
import sys
import csv
import json
import pickle
import shutil
import logging
import argparse
import subprocess
import datetime as dt
from SPARQLWrapper import SPARQLWrapper

from config import Config
from app.utils import sparql_queries as sq
from app.utils import auxiliary_functions as aux
from app.utils import PrepExternalSchema


logfile = './log_files/rm_functions.log'
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    filename=logfile) 


def determine_date(schema_uri, local_sparql, virtuoso_graph):
    """ Gets the last modification date for a schema.

        Parameters
        ----------
        schema_uri : str
            The URI of the schema in the Chewie-NS.

        Returns
        --------
        insertion_date : str
        	The insertion date in the format YYYY-MM-DDTHH:MM:SS.f.
    """

    # get schema last modification date
    date_result = aux.get_data(SPARQLWrapper(local_sparql),
                               (sq.SELECT_SPECIES_SCHEMA.format(virtuoso_graph, schema_uri)))

    schema_info = date_result['results']['bindings'][0]

    insertion_date = schema_info['dateEntered']['value']

    return insertion_date


def get_species(local_sparql, virtuoso_graph):
    """ Gets the list of species in the Chewie-NS.

        This function has no arguments but expects
        that the SPARQL endpoint and default Virtuoso
        Graph be set as OS environment variables.

        Returns
        -------
        species_list : dict
        A dictionary with species URIs as keys and species
        names as values. None if species has no schemas.
    """

    # get the list of species in NS
    species_result = aux.get_data(SPARQLWrapper(local_sparql),
                                  (sq.SELECT_SPECIES.format(virtuoso_graph,
                                                            ' typon:name ?name. ')))

    species = species_result['results']['bindings']
    if len(species) == 0:
        species_list = None
    else:
        species_list = {s['species']['value']: s['name']['value']
                        for s in species}

    return species_list


def species_schemas(species_uri, schemas, local_sparql, virtuoso_graph):
    """ Gets the list of schemas for a species.

        Parameters
        ----------
        species_uri : str
            The URI of the species in the Chewie-NS.
        schemas : dict
            An empty dictionary to store schemas' data.

        Returns
        -------
        A list with the following variables:

        - status (int): status code of the response.
        - schemas (dict): A dictionary with the species
          URI as key and a list of tuples as value.
          Each tuple has a schema URI and the name of
          that schema.
    """

    result = aux.get_data(SPARQLWrapper(local_sparql),
                          (sq.SELECT_SPECIES_SCHEMAS.format(virtuoso_graph,
                                                            species_uri)))

    try:
        ns_schemas = result['results']['bindings']
        if len(ns_schemas) > 0:
            for schema in ns_schemas:
                schemas.setdefault(species_uri, []).append((schema['schemas']['value'],
                                                            schema['name']['value']))
    except Exception:
        logging.warning('Could not retrieve schemas for '
                        '{0}. Exception:\n{1}'.format(species_uri, result))

    return schemas


def extract_triples(message):
	"""
	"""

	triples = message.split(';, ')[-1].split(' ')[0]

	return triples


def single_delete(statement, uris, virtuoso_graph, local_sparql,
	              virtuoso_user, virtuoso_pass):
	"""
	"""

	query = (statement.format(virtuoso_graph, *uris))

	result = aux.send_data(query, local_sparql, virtuoso_user, virtuoso_pass)

	return [result.status_code, result.text]


def multiple_delete(statement, uris, virtuoso_graph,
	                local_sparql, virtuoso_user, virtuoso_pass):
	"""
	"""

	deleted = 0
	triples = 0
	stderr = {}
	noeffect = []
	total_uris = len(uris)
	for u in uris:
		status_code, message = single_delete(statement, u,
			                                 virtuoso_graph, local_sparql,
			                                 virtuoso_user, virtuoso_pass)
		if status_code in [200, 201]:
			deleted_triples = int(extract_triples(message))
			if deleted_triples == 0:
				noeffect.append(u)
			else:
				deleted += 1
				triples += deleted_triples
				print('\r', '{0}/{1}'.format(deleted, total_uris), end='')
		else:
			stderr.setdefault(message, []).append(u)

	return [deleted, stderr, noeffect, triples]


def log_results(stdout_text, stderr, noeffect):
	"""
	"""

	print('\n'+stdout_text)
	logging.info(stdout_text)
	if len(stderr) > 0:
		print('Failed for {0} loci.'.format(sum([len(v) for k, v in stderr.items()])))
		stderr_text = '\n'.join(['Failed for {0}\nError:\n{1}'
			                     ''.format(v, k) for k, v in stderr.items()])
		logging.info(stderr_text)
	if len(noeffect) > 0:
		print('Could not delete triples for: {0}'.format(noeffect))
		logging.info('Could not delete triples for: {0}'.format(noeffect))


def collapse_loci(loci_uris, virtuoso_graph, local_sparql,
	              virtuoso_user, virtuoso_pass):
	"""
	"""

	deleted_triples = 0

	# delete alleles for all loci
	print('Deleting alleles...')
	loci_uris = [[uri] for uri in loci_uris]
	deleted, stderr, noeffect, triples = \
		multiple_delete(sq.DELETE_LOCUS_ALLELES, loci_uris, virtuoso_graph,
			local_sparql, virtuoso_user, virtuoso_pass)

	deleted_triples += triples
	total_alleles = int(triples/8)
	stdout_text = ('Deleted alleles for {0} loci ({1} alleles, {2} '
		           'triples).'.format(deleted, total_alleles, triples))
	log_results(stdout_text, stderr, noeffect)

	# delete all loci
	print('Deleting loci...')
	deleted, stderr, noeffect, triples = \
		multiple_delete(sq.DELETE_LOCUS, loci_uris, virtuoso_graph,
			local_sparql, virtuoso_user, virtuoso_pass)

	deleted_triples += triples
	total_loci = int(triples/8)
	stdout_text = ('Deleted {0} loci ({1} triples).'
		           ''.format(deleted, triples))
	log_results(stdout_text, stderr, noeffect)

	# delete loci links to species
	print('Deleting loci links to the species...')
	deleted, stderr, noeffect, triples = \
		multiple_delete(sq.DELETE_SPECIES_LOCUS, loci_uris, virtuoso_graph,
			local_sparql, virtuoso_user, virtuoso_pass)

	deleted_triples += triples
	total_splinks = int(triples)
	stdout_text = 'Deleted {0} links to species ({1} triples).'.format(deleted, triples)
	log_results(stdout_text, stderr, noeffect)

	# delete loci links to schema
	print('Deleting loci links to the schema...')
	deleted, stderr, noeffect, triples = \
		multiple_delete(sq.DELETE_SCHEMA_LOCUS, loci_uris, virtuoso_graph,
			local_sparql, virtuoso_user, virtuoso_pass)

	deleted_triples += triples
	total_sclinks = int(triples/4)
	stdout_text = 'Deleted {0} links to schema ({1} triples).'.format(deleted, triples)
	log_results(stdout_text, stderr, noeffect)

	return [deleted_triples, total_alleles, total_loci, total_splinks, total_sclinks]


def rm_schema(identifier, species_id, virtuoso_graph, local_sparql,
	          base_url, virtuoso_user, virtuoso_pass):
	"""
	"""

	total_triples = 0

	# create schema URI
	schema_uri = ('{0}species/{1}/schemas/{2}'
	              '').format(base_url, species_id, identifier)

	logging.info('Started rm process for schema {0}.'.format(schema_uri))

	# check if schema exists
	schema_result = aux.get_data(SPARQLWrapper(local_sparql),
                                 (sq.ASK_SCHEMA.format(schema_uri)))

	if schema_result['boolean'] is not True:
		logging.info('Could not find schema.\n')
		sys.exit('\nThere is no schema with specified ID.')

	print('\nDeleting loci and alleles for schema: {0}'.format(schema_uri))

	# get schema's loci
	schema_result = aux.get_data(SPARQLWrapper(local_sparql),
                                 (sq.SELECT_SCHEMA_LOCI.format(virtuoso_graph, schema_uri)))

	schema_result = schema_result['results']['bindings']

	results = [0, 0, 0, 0, 0]
	if len(schema_result) == 0:
		logging.info('{0} has no loci.'.format(schema_uri))
	else:
		loci_uris = [l['locus']['value'] for l in schema_result]

		print('Loci to delete: {0}\n'.format(len(loci_uris)))
		logging.info('{0} loci to delete'.format(len(loci_uris)))

		# collapse all loci (sequences are not deleted)
		results = collapse_loci(loci_uris, virtuoso_graph, local_sparql,
	                            virtuoso_user, virtuoso_pass)
		total_triples += results[0]

	# delete description
	#schema_desc = aux.get_data(SPARQLWrapper(local_sparql),
    #                            (sq.SELECT_SCHEMA_DESCRIPTION.format(virtuoso_graph, schema_uri)))

	#schema_desc = schema_desc['results']['bindings'][0]['description']['value']
	#desc_file = '{0}/{1}'.format(Config.PRE_COMPUTE, schema_desc)
	#if os.path.isfile(desc_file) is True:
	#	subprocess.call(['rm', desc_file])

	# delete compressed version
	zip_file = [f for f in os.listdir(Config.SCHEMAS_ZIP) if f.startswith('{0}_{1}'.format(species_id, identifier))]
	if len(zip_file) > 0:
		zip_file = '{0}/{1}'.format(Config.SCHEMAS_ZIP, zip_file[0])
		subprocess.call(['rm', zip_file])
		print('Deleted compressed version ({0})'.format(zip_file))
		logging.info('Deleted compressed version ({0})'.format(zip_file))

	# delete pre-computed files
	length_files = '{0}/{1}_{2}_lengths'.format(Config.PRE_COMPUTE, species_id, identifier)
	if os.path.isdir(length_files) is True:
		subprocess.call(['rm', '-rf', length_files])
		print('Deleted directory with length values ({0})'.format(length_files))
		logging.info('Deleted directory with length values ({0})'.format(length_files))

	annotation_file = '{0}/annotations_{1}_{2}.json'.format(Config.PRE_COMPUTE, species_id, identifier)
	if os.path.isfile(annotation_file) is True:
		subprocess.call(['rm', annotation_file])
		print('Deleted pre-computed annotations ({0})'.format(annotation_file))
		logging.info('Deleted pre-computed annotations ({0})'.format(annotation_file))

	mode_file = '{0}/mode_{1}_{2}.json'.format(Config.PRE_COMPUTE, species_id, identifier)
	if os.path.isfile(mode_file) is True:
		subprocess.call(['rm', mode_file])
		print('Deleted pre-computed modes ({0})'.format(mode_file))
		logging.info('Deleted pre-computed modes ({0})'.format(mode_file))

	boxplot_file = '{0}/boxplot_{1}_{2}.json'.format(Config.PRE_COMPUTE, species_id, identifier)
	if os.path.isfile(boxplot_file) is True:
		subprocess.call(['rm', boxplot_file])
		print('Deleted pre-computed boxplot values ({0})'.format(boxplot_file))
		logging.info('Deleted pre-computed boxplot values ({0})'.format(boxplot_file))

	# remove schema data from pre-computed files
	loci_file = '{0}/loci_{1}.json'.format(Config.PRE_COMPUTE, species_id)
	if os.path.isfile(loci_file) is True:
		with open(loci_file, 'r') as json_file:
			json_data = json.load(json_file)

		schemas = json_data['message']
		schemas = [s for s in schemas if s['schema'] != schema_uri]
		json_data['message'] = schemas
		with open(loci_file, 'w') as json_outfile:
			json.dump(json_data, json_outfile)
		print('Deleted pre-computed values from file with loci values ({0})'.format(loci_file))
		logging.info('Deleted pre-computed values from file with loci values ({0})'.format(loci_file))

	totals_file = '{0}/totals_{1}.json'.format(Config.PRE_COMPUTE, species_id)
	if os.path.isfile(totals_file) is True:
		with open(totals_file, 'r') as json_file:
			json_data = json.load(json_file)

		schemas = json_data['message']
		schemas = [s for s in schemas if s['uri'] != schema_uri]
		json_data['message'] = schemas
		with open(totals_file, 'w') as json_outfile:
			json.dump(json_data, json_outfile)
		print('Deleted pre-computed values from file with schema totals ({0})'.format(totals_file))
		logging.info('Deleted pre-computed values from file with schema totals ({0})'.format(totals_file))

	# delete schema
	status_code, message = single_delete(sq.DELETE_SCHEMA, [schema_uri],
		                                  virtuoso_graph, local_sparql,
		                                  virtuoso_user, virtuoso_pass)

	schema_triples = int(extract_triples(message))
	schema_del = 0
	if status_code in [200, 201]:
		if schema_triples > 0:
			schema_del = 1
			print('Deleted {0}'.format(schema_uri))
			logging.info('Deleted {0}'.format(schema_uri))
			total_triples += schema_triples
		else:
			print('Could not delete triples for {0}'.format(schema_uri))
			logging.info('Could not delete triples for {0}'.format(schema_uri))
	else:
		print('Failed to delete schema: {0}'.format(schema_uri))
		logging.info('Failed to delete {0}'.format(schema_uri))
		logging.info('Failed stderr:\n{0}'.format(message))

	print('\nDeleted a total of {0} triples.'.format(total_triples))
	print('({0} loci, {1} species links, {2} schema links, '
		  '{3} alleles)'.format(results[2], results[3],
		  	                    results[4], results[1]))

	return_dict = {'schema': schema_del,
				   'loci': results[2],
				   'splinks': results[3],
				   'sclinks': results[4],
				   'alleles': results[1],
				   'total_triples': total_triples}

	return return_dict


def rm_loci(identifier, virtuoso_graph, local_sparql,
	        base_url, virtuoso_user, virtuoso_pass):
	"""
	"""

	total_triples = 0

	# check input type
	if os.path.isfile(identifier) is False:
		if ',' in identifier:
			loci_ids = identifier.split(',')
		else:
			loci_ids = [identifier]
	else:
		with open(identifier, 'r') as ids:
			loci_ids = [l.strip() for l in ids.readlines()]

	# create loci URIs
	loci_uris = ['{0}loci/{1}'.format(base_url, i) for i in loci_ids]

	logging.info('Started rm process for loci: {0}.'.format(loci_ids))

	# check if loci exist
	invalid = []
	for locus in loci_uris:
		locus_result = aux.get_data(SPARQLWrapper(local_sparql),
	                                (sq.ASK_LOCUS.format(locus)))

		if locus_result['boolean'] is not True:
			invalid.append(locus)
			logging.info('Could not find locus {0}.\n'.format(locus))

	# exclude invalid URIs
	loci_uris = [l for l in loci_uris if l not in invalid]

	print('\nLoci to delete: {0}\n'.format(loci_uris))

	results = collapse_loci(loci_uris, virtuoso_graph, local_sparql,
                            virtuoso_user, virtuoso_pass)
	total_triples += results[0]

	print('\nDeleted a total of {0} triples.'.format(total_triples))
	logging.info('Deleted a total of {0} triples.'.format(total_triples))
	print('({0} loci, {1} species links, {2} schema links, '
		  '{3} alleles)'.format(results[2], results[3],
		  	                    results[4], results[1]))
	logging.info('({0} loci, {1} species links, {2} schema links, '
		        '{3} alleles)'.format(results[2], results[3],
		  	                          results[4], results[1]))

	return_dict = {'loci': results[2],
				   'splinks': results[3],
				   'sclinks': results[4],
				   'alleles': results[1],
				   'total_triples': total_triples}

	return return_dict


def rm_alleles(identifier, locus_id, virtuoso_graph, local_sparql,
	           base_url, virtuoso_user, virtuoso_pass):
	"""
	"""

	# check input type
	if os.path.isfile(identifier) is False:
		if ',' in identifier:
			alleles_ids = {locus_id: identifier.split(',')}
		else:
			alleles_ids = {locus_id: [identifier]}
	else:
		with open(identifier, 'r') as ids:
			lines = [l.strip() for l in ids.readlines()]
			lines = [l.split(':') for l in lines]
			alleles_ids = {l[0]: l[1].split(',') for l in lines}

	# create URIs
	locus_template = '{0}loci/{1}'
	allele_template = '{0}loci/{1}/alleles/{2}'
	alleles_ids = {locus_template.format(base_url, k):
                   [allele_template.format(base_url, k, a) for a in v]
                   for k, v in alleles_ids.items()}

	# delete alleles
	uris = []
	for locus, alleles in alleles_ids.items():
		locus_uris = [[a, locus] for a in alleles]
		uris.extend(locus_uris)

	print('\nDeleting alleles...')
	deleted, stderr, noeffect, triples = \
		multiple_delete(sq.DELETE_ALLELE, uris, virtuoso_graph,
			local_sparql, virtuoso_user, virtuoso_pass)

	total_alleles = triples/8
	stdout_text = 'Deleted {0} alleles ({1} triples).'.format(deleted, triples)
	log_results(stdout_text, stderr, noeffect)

	return_dict = {'alleles': total_alleles,
				   'total_triples': triples}

	return return_dict


def rm_loci_links(mode, identifier, virtuoso_graph, local_sparql,
	           	  base_url, virtuoso_user, virtuoso_pass):
	"""
	"""

	total_triples = 0

	# check input type
	if os.path.isfile(identifier) is False:
		if ',' in identifier:
			loci_ids = identifier.split(',')
		else:
			loci_ids = [identifier]
	else:
		with open(identifier, 'r') as ids:
			loci_ids = [l.strip() for l in ids.readlines()]

	# create loci URIs
	loci_uris = ['{0}loci/{1}'.format(base_url, i) for i in loci_ids]

	logging.info('Started rm process to delete {0} for loci: {1}.'.format(mode, loci_uris))

	# check if loci exist
	invalid = []
	for locus in loci_uris:
		locus_result = aux.get_data(SPARQLWrapper(local_sparql),
	                                (sq.ASK_LOCUS.format(locus)))

		if locus_result['boolean'] is not True:
			invalid.append(locus)
			logging.info('Could not find locus {0}.\n'.format(locus))

	# exclude invalid URIs
	loci_uris = [[l] for l in loci_uris if l not in invalid]

	if mode == 'splinks':
		statement = sq.DELETE_SPECIES_LOCUS
	elif mode == 'sclinks':
		statement = sq.DELETE_SCHEMA_LOCUS

    # delete loci links to species
	print('Deleting loci {0}...'.format(mode))
	deleted, stderr, noeffect, triples = \
		multiple_delete(statement, loci_uris, virtuoso_graph,
			local_sparql, virtuoso_user, virtuoso_pass)

	total_links = int(triples) if mode == 'splinks' else int(triples/4)
	stdout_text = 'Deleted {0} {1} ({2} triples).'.format(deleted, mode, triples)
	log_results(stdout_text, stderr, noeffect)

	return_dict = {'{0}'.format(mode): total_links,
				   'total_triples': triples}

	return return_dict


def periodic_remover(time, virtuoso_graph, local_sparql,
	                 base_url, virtuoso_user, virtuoso_pass):
    """
    """

    # get date
    start_date = dt.datetime.now()
    start_date_str = dt.datetime.strftime(start_date, '%Y-%m-%dT%H:%M:%S')
    logging.info('Started global schema remover at: {0}'.format(start_date_str))

    # get list of species
    species_list = get_species(local_sparql, virtuoso_graph)
    if species_list is None:
        logging.warning('Could not retrieve any species from the NS.\n\n')
        sys.exit(0)
    else:
        logging.info('Species in NS: {0}'.format(','.join(list(species_list.values()))))

    # get list of schemas per species
    schemas = {}
    for species in species_list:
        schemas = species_schemas(species, schemas, local_sparql, virtuoso_graph)
        if len(schemas) > 0:
            current_schemas = schemas.get(species, None)
            if current_schemas is not None:
                current_schemas_strs = ['{0}, {1}'.format(s[0], s[1]) for s in current_schemas]
                logging.info('Found {0} schemas for {1} ({2}): {3}'.format(len(current_schemas),
                                                                           species,
                                                                           species_list[species],
                                                                           ';'.join(current_schemas_strs)))

    if len(schemas) == 0:
        logging.warning('Could not find schemas for any species.\n\n')
        sys.exit(0)

    # determine current date
    current_date = dt.datetime.now()

    # check insertion date of each schema and delete if
    # the schema has been up for a time period that equals
    # or exceeds defined limit
    deleted = {}
    for species in schemas:
        deleted[species] = 0
        sp_schemas = schemas[species]

        species_id = species.split('/')[-1]

        for schema in sp_schemas:
            schema_uri = schema[0]
            insertion_date = determine_date(schema_uri, local_sparql, virtuoso_graph)

            # convert date string to datetime object
            if insertion_date != 'singularity':
	            insertion_date = dt.datetime.strptime(insertion_date, '%Y-%m-%dT%H:%M:%S.%f')

	            # determine time difference
	            diff = current_date - insertion_date
	            seconds = diff.total_seconds()
	            hours = divmod(seconds, 3600)[0]

	            if hours >= time:
	                logging.info('Schema {0} has been up for longer than {1} hours. Will be deleted.'.format(schema_uri, time))
	                # remove schema
	                schema_id = schema_uri.split('/')[-1]
	                if schema_id != '1':
		                deleted_data = rm_schema(schema_id, species_id, virtuoso_graph,
							                     local_sparql, base_url, virtuoso_user,
							                     virtuoso_pass)
		                deleted[species] += 1

    for sp, scs in deleted.items():
        logging.info('Deleted {0} schemas for {1}'.format(scs, sp))


def parse_arguments():

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-m', type=str,
                        dest='mode', required=True,
                        choices=['schema', 'loci', 'alleles',
                        		 'splinks', 'sclinks'],
                        help='Execution mode.')

    parser.add_argument('-id', type=str, required=True,
                        dest='identifier',
                        help='A single, set of or file with identifiers. '
                             'The identifiers can be integers or full '
                             'URIs for the schemas, loci or alleles to '
                             'delete.')

    parser.add_argument('--sp', type=str, default=None,
                        dest='species_id', required=False,
                        help='The identifier of the species in the '
                             'Chewie-NS (only relevant for the "schemas" '
                             'mode).')

    parser.add_argument('--l', type=str, default=None,
                        dest='locus_id', required=False,
                        help='The identifier of the locus in the '
                             'Chewie-NS (only relevant for the "alleles" '
                             'mode).')

    parser.add_argument('--g', type=str,
                        dest='virtuoso_graph',
                        default=os.environ.get('DEFAULTHGRAPH'),
                        help='')

    parser.add_argument('--s', type=str,
                        dest='local_sparql',
                        default=os.environ.get('LOCAL_SPARQL'),
                        help='')

    parser.add_argument('--b', type=str,
                        dest='base_url',
                        default=os.environ.get('BASE_URL'),
                        help='')

    parser.add_argument('--u', type=str,
                        dest='virtuoso_user',
                        default=os.environ.get('VIRTUOSO_USER'),
                        help='')

    parser.add_argument('--p', type=str,
                        dest='virtuoso_pass',
                        default=os.environ.get('VIRTUOSO_PASS'),
                        help='')

    args = parser.parse_args()

    return [args.mode, args.identifier, args.species_id, args.locus_id,
            args.virtuoso_graph, args.local_sparql, args.base_url,
            args.virtuoso_user, args.virtuoso_pass]


def main(args):

	# get starting date
	start_date = dt.datetime.now()

	if args[0] == 'schema':
		results = rm_schema(args[1], args[2], args[4],
			                args[5], args[6], args[7],
			                args[8])
	elif args[0] == 'loci':
		results = rm_loci(args[1], args[4], args[5],
			              args[6], args[7], args[8])
	elif args[0] == 'alleles':
		results = rm_alleles(args[1], args[3], args[4],
			                 args[5], args[6], args[7],
			                 args[8])
	elif args[0] == 'splinks':
		results = rm_loci_links(args[0], args[1], args[4],
							 	args[5], args[6], args[7],
							 	args[8])
	elif args[0] == 'sclinks':
		results = rm_loci_links(args[0], args[1], args[4],
							 	args[5], args[6], args[7],
							 	args[8])

	end_date = dt.datetime.now()
	delta = end_date - start_date
	minutes, seconds = divmod(delta.total_seconds(), 60)
	print('Elapsed time: {0:.0f}m{1:.0f}s'.format(minutes, seconds))
	logging.info('Elapsed time: {0:.0f}m{1:.0f}s\n'.format(minutes, seconds))

	return results


if __name__ == '__main__':

	args = parse_arguments()

	main(args)
