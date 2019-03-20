#! /usr/bin/env python

'''
Tool to analyze cluster distribution on proxmox
nodes.
'''

from proxmoxer import ProxmoxAPI
from string import digits, ascii_letters
from settings import PROXMOX, STATIC_THRESHOLD
from settings import DYNAMIC_THRESHOLD
import logging
import coloredlogs
import argparse

proxmox = ProxmoxAPI(PROXMOX['HOST'], user=PROXMOX['USER'],
                     password=PROXMOX['PASSWORD'], verify_ssl=False)

LOG_LEVELS = ['debug', 'info', 'warning', 'error', 'critical']
SORT_KEYS = ['cluster', 'qty', 'percentage', 'node']

logger = logging.getLogger('proxmox_balance')


def log_init(loglevel):
    """ initialize the logging system """
    FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'
    logging.basicConfig(format=FORMAT, level=getattr(logging,
                                                     loglevel.upper()))
    coloredlogs.install(level=loglevel.upper())


def get_cluster(vm):
    """ get the cluster name from the vm name:
    the env (prod, staging, dev) is inherithed by
    the host index"""
    base_cluster = '%s%s' % (vm[:1], vm[1:].strip(digits))
    logger.debug(vm)
    try:
        idx = int(vm[1:].replace('-', '').strip(ascii_letters))
        logger.debug(idx)
    except ValueError:
        raise
    if idx < 80:
        return '%s' % (base_cluster)
    elif idx >= 80 and idx < 90:
        return '%s-stg' % (base_cluster)
    elif idx > 90:
        return '%s-dev' % (base_cluster)


def get_total(balance_map, cluster):
    """ get the the total number of hosts for cluster """
    total = 0
    for node in balance_map:
        if cluster in balance_map[node]:
            total += balance_map[node][cluster]
    return total


def get_unbalanced(balance_map, th_percentage, th):
    """ get a map of cluster distribution on proxmox node """
    unbalanced = {}
    for node in balance_map:
        for cluster in balance_map[node]:
            qty = balance_map[node][cluster]
            total = get_total(balance_map, cluster)
            percentage = round(qty/total*100)
            if qty > th and percentage > th_percentage:
                logger.debug('%s: %s/%s %s%% - %s' % (cluster, qty, total,
                                                      percentage, node))
                unbalanced[cluster] = {}
                unbalanced[cluster]['qty'] = qty
                unbalanced[cluster]['total'] = total
                unbalanced[cluster]['percentage'] = percentage
                unbalanced[cluster]['node'] = node

    logger.debug(unbalanced)
    return unbalanced


def unbalanced_sort_by(unbalanced, key, reverse=False):
    """ sort a dict of dict by a subdict key """
    ordered = sorted(unbalanced.items(), key=lambda x: x[1][key],
                     reverse=reverse)
    logger.debug(ordered)
    return ordered


def unbalanced_sort(unbalanced, key):
    """ sort the unbalanced map by a custom key """
    if key == 'cluster':
        logger.info('sort by cluster')
        for cluster in sorted(unbalanced.keys()):
            qty, total, percentage, node = unbalanced_get(unbalanced, cluster)
            logger.info('%s: %s/%s %s%% - %s' % (cluster, qty, total,
                                                 percentage, node))
    elif key == 'qty':
        logger.info('sort by quantity')
        ordered_log(unbalanced_sort_by(unbalanced, key, reverse=True))
    elif key == 'percentage':
        logger.info('sort by percentage')
        ordered_log(unbalanced_sort_by(unbalanced, key, reverse=True))
    elif key == 'node':
        logger.info('sort by node')
        ordered_log(unbalanced_sort_by(unbalanced, key))


def unbalanced_get(unbalanced, cluster):
    """ get dict values from unbalanced dict """
    entry = unbalanced[cluster]
    return entry['qty'], entry['total'], entry['percentage'], entry['node']


def ordered_log(ordered):
    """ format an ordered tuple """
    for entry in ordered:
        logger.info('%s: %s/%s %s%% - %s' % (entry[0], entry[1]['qty'],
                                             entry[1]['total'],
                                             entry[1]['percentage'],
                                             entry[1]['node']))


def percentage(string):
    """ validation for a percentage value """
    value = int(string)
    if value > 100 or value < 0:
        msg = '%r is not a valid percentage value (0-100)' % (string)
        raise argparse.ArgumentTypeError(msg)
    return value


if __name__ == '__main__':

    description = 'proxmox_balance, analyze cluster distribution on nodes'
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-k', '--key', default=SORT_KEYS[0],
                        help='sort key (default vm name)', choices=SORT_KEYS)
    parser.add_argument('-p', '--percentage', default=DYNAMIC_THRESHOLD,
                        help='percentage threshold', type=percentage)
    parser.add_argument('-t', '--threshold', default=STATIC_THRESHOLD,
                        help='static threshold', type=int)
    parser.add_argument('-n', '--node', default=None,
                        help='filter by node')
    parser.add_argument('-l', '--log-level', default=LOG_LEVELS[1],
                        help='log level (default info)', choices=LOG_LEVELS)

    # parse cli options
    options = {}
    cli_options = parser.parse_args()
    log_init(cli_options.log_level)
    logger.debug(cli_options)
    sort_key = cli_options.key
    percentage = cli_options.percentage
    threshold = cli_options.threshold
    node_filter = cli_options.node

    balance_map = {}

    for node in proxmox.nodes.get():
        n_name = node['node']
        if node_filter is None or n_name == node_filter:
            balance_map[n_name] = {}
            for vm in proxmox.nodes(node['node']).qemu.get():
                if vm['status'] == 'running':
                    try:
                        cluster = get_cluster(vm['name'])
                        if cluster in balance_map[n_name]:
                            balance_map[n_name][cluster] += 1
                        else:
                            balance_map[n_name][cluster] = 1
                    except ValueError:
                        pass

    unbalanced = get_unbalanced(balance_map, percentage, threshold)
    unbalanced_sort(unbalanced, sort_key)
