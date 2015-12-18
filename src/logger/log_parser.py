import dateutil
import numpy
import logging
import math
import matplotlib.pyplot as plot
from config import config

LOG_DIRECTORY = config.log_directory
LOG_TAGS = config.log_tags
LOG_SEPARATOR = config.log_tag_separator


class LogParser(object):


    VM_STATES = {
                    'deleted' : 0,
                    'building' : 1,
                    'active'   : 2,
                    'migrating' : 3,
                    'error'     : 4
                }

    def __init__(self, logger = None):
        self.__clear_data()
        self.__parsing_functions = {
                                    LOG_TAGS['sys_info'] : None,
                                    LOG_TAGS['total_info'] : self.__parse_total_info,
                                    LOG_TAGS['node_info'] : self.__parse_node_info,
                                    LOG_TAGS['vm_info'] : self.__parse_vm_info,
                                    LOG_TAGS['migration_started'] : None,
                                    LOG_TAGS['migration_ended'] : None
                                  }
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

    def __clear_data(self):
        """ Pomocna funckija za restartovanje podataka """
        self.nodes = {}
        self.vms = {}
        self.total_vms = {
                            'time'  : [0],
                            'value' : [0]
                         }

    def parse_log(self, filename):
        """" Funkcija za parsiranje log fajla. Format svake linije log fajla je sledeci:
             datum vrijeme SEPARATOR milisekunde SEPARATOR tag SEPARATOR poruka
             Funkcija prolazi kroz svaku liniju fajla i na osnovu taga poziva odgovarajucu pomocnu funkciju.
             Funkcije se vrlo lako pozivaju jer se reference na njih cuvaju u dictionary strukturi u parovima TAG : FUNKCIJA
        """
        self.log_filename = LOG_DIRECTORY + filename
        try:
            file_obj = open(self.log_filename, 'r')
            self.__clear_data()
            for line in file_obj.readlines():
                self.logger.info(line)
                splitted_line = line.split(LOG_SEPARATOR)
                if len(splitted_line) == 4:
                    splitted_line[3] = splitted_line[3].replace('\n', '')
                    tag = splitted_line[2]
                    parsing_function = self.__parsing_functions[tag]
                    if parsing_function is not None:
                        parsing_function(time = splitted_line[1], message = splitted_line[3])

            file_obj.close()

        except Exception as e:
            print e

    def __parse_total_info(self, time, message):
        """ Pomocna funkcija za parsiranje poruka o ukupnom broju VM
            Format u kojem dolazi poruka je sledeci:
            Total: %d vms - broj instanci
        """
        data = message.split()
        num_vms = data[1]
        self.total_vms['time'].append(float(time)/1000.0)
        self.total_vms['value'].append(float(num_vms))

    def __parse_node_info(self, time, message):
        """ Pomocna funkcija za parsiranje informacija o cvoru
            Format u kojem dolazi poruka je sledeci:
            %s: %d State: %s %s - naziv hosta, broj instanci, status (up, down) i stanje (enabled, disabled)
        """
        data = message.split()
        node_name = data[0].replace(':', '')
        num_vms = data[1]
        if node_name not in self.nodes.keys():
            self.nodes[node_name] = {}
            self.nodes[node_name]['time'] = [0]
            self.nodes[node_name]['value'] = [0]
        self.nodes[node_name]['time'].append(float(time)/1000.0)
        self.nodes[node_name]['value'].append(float(num_vms))


    def __parse_vm_info(self, time, message):
        """ Pomocna funkcija za parsiranje informacija o virtuelnoj instanci
            Format u kojem dolazi poruka je sledeci:
            Host: %s Name: %s State: %s New_task: %s	- naziv hosta, naziv instance, trenutno stanje instace i sta instance trenutno radi
        """
        data = message.split()
        host_name = data[1]
        i = 3
        vm_name = data[i]
        while data[i] != 'State:':
            vm_name += ' ' + data[i]
            i += 1
        state = data[i + 1]
        new_task_state = data[i + 3]
        if vm_name not in self.vms:
            self.vms[vm_name] = {}
            self.vms[vm_name]['time'] = [0]
            self.vms[vm_name]['state'] = [LogParser.VM_STATES['deleted']]

        try:
            self.vms[vm_name]['time'].append(float(time)/1000.0)
            self.vms[vm_name]['state'] = [LogParser.VM_STATES[state]]
        except KeyError as e:
            print('ERROR: State %s unknown in dict VM_STATES' %state)



    def show_graphs(self):
        """ Funkcija za iscrtavanje statistickih podataka dobijenih iz log fajla.
            Iscrtava se grafik sa svim cvorovima i i ukupnim brojem virtuelnih instanci,
            iscrtavaju se grafici za svaki cvor posebno i
            grafik sa svim cvorovima bez ukupnog broja virtuelnih instanci.
        """
        plot.title('Statika cloud sistema')

        self.total_vms['value'][0] = self.total_vms['value'][1]
        maximum_num = max(self.total_vms['value'])

        graph = plot.plot(self.total_vms['time'], self.total_vms['value'], 'r', label = 'Ukupan broj VM')
        plot.setp(graph, color='r', linewidth=2.0)

        for node in self.nodes.keys():
            self.nodes[node]['value'][0] = self.nodes[node]['value'][1]
            plot.plot(self.nodes[node]['time'], self.nodes[node]['value'], label = node)

        plot.yticks(numpy.arange(0, maximum_num + 2, 1))
        plot.ylabel('Broj virtuelnih instanci')
        plot.xlabel('Vrijeme u sekundama')
        plot.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        plot.grid()

        for node in self.nodes.keys():
            plot.figure(node)
            graph = plot.plot(self.total_vms['time'], self.total_vms['value'], 'r', label = 'Ukupan broj VM')
            plot.setp(graph, color='r', linewidth=2.0)
            average = []
            for value in self.total_vms['value']:
                #average.append(value / len(self.nodes.keys()))
                optimum = value / len(self.nodes.keys())
                diff = optimum - math.floor(optimum)
                if diff >= 0.5:
				    average.append(math.ceil(optimum))
                else:
				    average.append(math.floor(optimum))
            graph = plot.plot(self.total_vms['time'], average, 'g', label = 'Optimalan broj instanci')
            plot.plot(self.nodes[node]['time'], self.nodes[node]['value'], 'b', label = node)
            plot.yticks(numpy.arange(0, maximum_num + 2, 1))
            plot.ylabel('Broj virtuelnih instanci')
            plot.xlabel('Vrijeme u sekundama')
            plot.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
            plot.grid()

        plot.figure('Svi hostovi')
        max_list = []
        for node in self.nodes.keys():
            self.nodes[node]['value'][0] = self.nodes[node]['value'][1]
            plot.plot(self.nodes[node]['time'], self.nodes[node]['value'], label = node)
            max_list.append(max(self.nodes[node]['value']))

        maximum_num = max(max_list)
        plot.yticks(numpy.arange(0, maximum_num + 2, 1))
        plot.ylabel('Broj virtuelnih instanci')
        plot.xlabel('Vrijeme u sekundama')
        plot.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        plot.grid()
        plot.show()
