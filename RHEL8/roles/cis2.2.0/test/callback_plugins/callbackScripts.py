from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import json
import socket
import psycopg2
import logging
import math
import jinja2

from ansible import context
from json import JSONEncoder
from ansible.utils.path import makedirs_safe
from ansible.module_utils._text import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.module_utils.basic import get_distribution, get_exception
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase
from datetime import datetime


class Host:
    def __init__(self):
        self.distribution = ""
        self.distribution_version = ""
        self.distribution_major_version = ""
        self.os_family = ""
        self.hostname = ""
        self.ipv4 = ""
        self.tasks = {}


class Task:
    def __init__(self):
        self.rule = ""
        self.section = ""
        self.scored = ""
        self.level = ""
        self.profiles = []
        self.category = ""
        self.headings = {}
        self.message = ""
        self.isManual = False
        
class Heading:
    def __init__(self):
        self.level = 0
        self.rule = ""
        self.section = ""

class CISEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

# ==========================================================

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    my_objects = []

    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.last_task_name = None
        self.playbook_name = None
        self._play = ""
        self.node_task_result = {}
        self.check_mode = False
        self.transaction_per_node = {}
        self.tags = []
        self.tasks_per_host = {}

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # create a file handler
        handler = logging.FileHandler('/home/automation/automationtool/Linux/RHEL7/log/rhel_logger.log')
        handler.setLevel(logging.DEBUG)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # add the file handler to the logger
        self.logger.addHandler(handler)

        self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')        

    def _all_vars(self, host=None, task=None):
        return self._play.get_variable_manager().get_vars(
            play=self._play,
            host=host,
            task=task
        )


    def log(self, result, category): 
        values = self.last_task_name.split("|")
        print("Status: {0}".format(category))
        
        self.logger.debug('Task: %s\n', self.last_task_name)
        self.logger.debug('Status: %s\n', category)
        if 'msg' in result._result:
            message = result._result['msg']
            self.logger.debug('msg: %s\n', message)   
            print("Msg: {0}".format(message))                

        host_name = result._host.get_name()

        if len(self.tags) > 0 and ("RULE" in self.tags):                
            tmp_task = {}
            main_section = values[0]
            print(main_section)
            main_section = main_section[main_section.index(":")+2:]
            main_rule = values [1]
                        
            task = Task()
            if "MANUAL" in self.tags:
                task.isManual = True
                
            if 'msg' in result._result:
                task.message = result._result['msg']

            task.category = category
            task.section = main_section
            task.rule = main_rule
            
            main_scored = "NA"
            if "not_scored" in self.tags:
                main_scored = "Not Scored"
            elif "scored" in self.tags:
                main_scored = "Scored"
            else:
                main_scored = "NA"
            task.scored = main_scored
            task.level = len(main_section.split(".")) - 1
            tmp_task[main_section] = task

            profiles = []
            if "Level1_Workstation" in self.tags:
                profiles.append("Level1_Workstation")
            if "Level2_Workstation" in self.tags:
                profiles.append("Level2_Workstation")
            if "Level1_Server" in self.tags:
                profiles.append("Level1_Server")
            if "Level2_Server" in self.tags:
                profiles.append("Level2_Server")  
            task.profiles = profiles

            headings = {}
            for tag in self.tags: 
                if "|" in tag:
                    values = tag.split("|")
                    
                    heading = Heading()
                    heading_section = values[0]
                    
                    heading.section = heading_section
                    heading.rule = values[1]
                    heading.level = len(heading_section.split(".")) - 1
                    headings[heading_section] = heading

            task.headings = headings

            host_result = self.tasks_per_host[host_name]


            host_result_tasks = host_result.tasks

            if main_section not in host_result_tasks:
                host_result_tasks[main_section] = task
            else:
                original_task = host_result_tasks[main_section]
                                
                if original_task.category == "OK":
                    if category != "SKIPPED":
                        host_result_tasks[main_section] = task
                elif original_task.category == "SKIPPED":
                    host_result_tasks[main_section] = task
                elif original_task.category == "CHANGED":
                    if category == "FAILED" or category == "CHANGED":
                        host_result_tasks[main_section] = task                    
                elif original_task.category == "FAILED":
                    pass


        print('----------------- END OF TASK -----------------')

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(
            task_keys=task_keys, var_options=var_options, direct=direct)

    # done
    def create_host(self, result):
        host_name = result._host.get_name()

        if host_name not in self.tasks_per_host:
            hostname = self._all_vars(
            )['hostvars'][host_name]["ansible_hostname"]
            ipv4 = self._all_vars()[
                'hostvars'][host_name]["ansible_default_ipv4"]["address"]
            distribution = self._all_vars(
            )['hostvars'][host_name]["ansible_distribution"]
            distribution_major_version = self._all_vars(
            )['hostvars'][host_name]["ansible_distribution_major_version"]
            distribution_version = self._all_vars(
            )['hostvars'][host_name]["ansible_distribution_version"]
            os_family = ""
            # os_family = distribution_version + " " + distribution_version
            linux_family = self._all_vars()['vars']['linux']
            windows_family = self._all_vars()['vars']['windows']

            is_linux = distribution in linux_family
            is_windows = distribution in windows_family

            if is_linux:
                os_family = "LINUX"
            elif is_windows:
                os_family = "WINDOWS"
            else:
                os_family = "UNKNOWN"

            host = Host()
            host.distribution = distribution
            host.distribution_major_version = distribution_major_version
            host.distribution_version = distribution_version
            host.os_family = os_family
            host.hostname = hostname
            host.ipv4 = ipv4

            self.tasks_per_host[host_name] = host  

    def v2_runner_on_ok(self, result, **kwargs):
        print("===================== v2_runner_on_ok ======================")   
        if('output' in result._result):
            print(result._result['output'])
        # changed = ('changed' in result._result and result._result['changed'])
        # ok_or_changed = 'OK'

        # if changed:
        #     #if self.check_mode:
        #     #    ok_or_changed = 'CHANGED'
        #     #else:
        #     #    ok_or_changed = 'OK'
        #     ok_or_changed = 'CHANGED' # TODO testing purpose, neeed to remove later

        # self.create_host(result)

        # tags = result._task.tags 
        
        
        # if ('redhat_version' in tags):             
        #     host_name = result._host.get_name()
        #     host = self.tasks_per_host[host_name] 
        #     host.distribution = result._result['stdout']
        
        # #if ('tasks' in tags):
        # self.log(result, ok_or_changed)


    def v2_runner_on_failed(self, result, ignore_errors=False):
        #print("===================== v2_runner_on_failed ======================")
        
        self.create_host(result)
        self.log(result, 'FAILED')

    def v2_runner_on_skipped(self, result, ignore_errors=False):
        #print("===================== v2_runner_on_skipped ======================")
        self.create_host(result)
        self.log(result, 'SKIPPED')

    def v2_runner_item_on_skipped(self, result, ignore_errors=False):
        #print("===================== v2_runner_item_on_skipped ======================")
        self.create_host(result)
        self.log(result, 'SKIPPED')

    def v2_runner_on_unreachable(self, result):
        #print("===================== v2_runner_on_unreachable ======================")
        self.create_host(result)
        self.log(result, 'UNREACHABLE')

    def v2_runner_on_async_failed(self, result):
        #print("===================== v2_runner_on_async_failed ======================")
        self.create_host(result)
        self.log(result, 'ASYNC_FAILED')


    def v2_playbook_on_task_start(self, task, **kwargs):
        self.last_task_name = task.get_name()
        self.tags = task._attributes['tags']

    def playbook_on_setup(self):
        #print("\n{0}".format('GATHERING FACTS'))
        pass

    def set_play_context(self, play_context):
        self.play_context = play_context

    def v2_playbook_on_play_start(self, play):
        self._play = play
        playbook = self._all_vars()['vars']['playbook_dir']

        index = playbook.rfind('/')+1

        self.playbook_name = playbook[index:]
        if self.play_context.check_mode:
            self.check_mode = True


    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def v2_playbook_on_start(self, playbook):
        pass

    def v2_playbook_on_stats(self, stats):        
        """Complete: Flush log to database"""
        hosts = stats.processed.keys()

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>")        

        cisJSONData = json.dumps(self.tasks_per_host, indent=4, cls=CISEncoder)
        self.html_generator(cisJSONData)
        self.logger.info('Return result: \n%s', cisJSONData)

        print("------------------------------------------------")

        for h in hosts:
            t = stats.summarize(h)
            msg = "Host: %s, ok: %d, failures: %d, unreachable: %d, changed: %d, skipped: %d" % (
                h, t['ok'], t['failures'], t['unreachable'], t['changed'], t['skipped'])
            print("\n{0}".format(msg))

        #self.flush_to_database(hosts, is_compliant)
        print("============= Completed Successfully =============")

    def html_generator(self, cisJSONData):
        print("Generating report....")
        data = json.loads(cisJSONData)
        for host in data:
            list_body = []
            for i in data[host]["tasks"]:
                list_body.append(data[host]["tasks"][i]["section"])
                list_body.append(data[host]["tasks"][i]["rule"] + " (" + data[host]["tasks"][i]["scored"]+ ")" )

                if data[host]["tasks"][i]["category"] == "OK":
                    list_body.append("Compliant")
                if data[host]["tasks"][i]["category"] == "CHANGED":
                    if data[host]["tasks"][i]["isManual"]:
                        list_body.append("Manual")
                    else:
                        list_body.append("Non-compliant")
                if data[host]["tasks"][i]["category"] == "SKIPPED":
                    list_body.append("Compliant")
                if data[host]["tasks"][i]["category"] == "FAILED":
                    if data[host]["tasks"][i]["isManual"]:
                        list_body.append("Manual")
                    else:
                        list_body.append("Error")

                #list_body.append(data[host]["tasks"][i]["message"])
                if data[host]["tasks"][i]["isManual"] and data[host]["tasks"][i]["category"] == "FAILED":
                    list_body.append(data[host]["tasks"][i]["message"])
                else:
                    list_body.append(data[host]["tasks"][i]["category"])

            pass_count = list_body.count("Compliant")
            fail_count = list_body.count("Non-compliant")
            skip_count = list_body.count("Skipped")
            error_count = list_body.count("Error")
            manual_count = list_body.count("Manual")
            total = pass_count + fail_count + skip_count + error_count + manual_count

            compliant_count = pass_count + skip_count + manual_count
            non_compliant_count = fail_count + error_count

            percentageVal = math.floor((compliant_count/total)*100)

            percentage = str(percentageVal)+'%'

            status = ""
            if percentageVal == 100:
                status += "Passed"
            else:
                status += "Failed"

            i = 0
            list_of_lists = []
            while i < len(list_body):
                list_of_lists.append(list_body[i:i+4])
                i += 4

            templateLoader = jinja2.FileSystemLoader(
                searchpath="/home/automation/automationtool/Linux/RHEL7/callback_plugins")
            templateEnv = jinja2.Environment(loader=templateLoader)
            templateFile = "template.html"
            template = templateEnv.get_template(templateFile)
            html = template.render(machine_hostname=data[host]["hostname"], 
                machine_ip_address=data[host]["ipv4"], 
                machine_distro=data[host]["distribution"], 
                machine_time=self.start_time, 
                machine_number_of_policies=total, 
                machine_compliant=compliant_count, 
                machine_non_compliant=non_compliant_count, 
                machine_compliance_rate=percentage, 
                machine_status=status, 
                machine_manual=manual_count,
                table_items=list_of_lists)

            with open(data[host]["hostname"] + "_report.html", "w") as report:
                report.write(html)

    def flush_to_database(self, hosts, is_compliant):
        connection = psycopg2.connect(
            host='10.10.14.10', database='automation', user='postgres', password='P@ssw0rd')
        cursor = connection.cursor()
        print("Playbook: {}".format(self.playbook_name))
        playbook_name = self.playbook_name
        # PLAYBOOK
        sql_select_query_for_play = 'SELECT id FROM playbook WHERE name=%s'
        cursor.execute(sql_select_query_for_play, (playbook_name,))
        playbook_id = cursor.fetchone()[0]
        print("Playbook ID: {0}".format(playbook_id))

        #HISTORY
        sql_insert_query_for_run_history = 'INSERT INTO run_history (playbook_id, run_date) VALUES (%s, now()) RETURNING id'
        cursor.execute(sql_insert_query_for_run_history, (playbook_id,))
        history_id = cursor.fetchone()[0]
        print("History ID:::: {0}".format(history_id))

        for h in hosts:
            remote_node = self.node_task_result[h]
            ruleNodes = remote_node.rule_node #  set of section_rules
            distribution = remote_node.distribution
            distribution_version = remote_node.distribution_version
            distribution_major_version = remote_node.distribution_major_version
            print("\ndistribution: {0}".format(distribution))
            print("\ndistribution_version: {0}".format(distribution_version))
            print("\ndistribution_major_version: {0}".format(distribution_major_version))

            # OS
            sql_select_query_for_os_id = 'INSERT INTO os(playbook_id, distribution, distribution_version, distribution_major_version, os_family) values (%s, %s, %s, %s, %s) ON CONFLICT (distribution, os_family) DO UPDATE SET distribution = EXCLUDED.distribution RETURNING id'        
            cursor.execute(sql_select_query_for_os_id, (playbook_id, remote_node.distribution, remote_node.distribution_version, remote_node.distribution_major_version, remote_node.os_family,))
            os_id = cursor.fetchone()[0]
            print("OS ID:::: {0}".format(os_id))
            print("HostName: {0}".format(remote_node.hostname))
            print("IPV4: {0}".format(remote_node.ipv4))

            # MACHINE
            sql_select_query_for_machine_id = 'INSERT INTO machine(os_id, hostname, ipv4) VALUES (%s, %s, %s) ON CONFLICT (os_id, hostname, ipv4) DO UPDATE SET hostname = EXCLUDED.hostname RETURNING id'
            cursor.execute(sql_select_query_for_machine_id, (os_id, remote_node.hostname, remote_node.ipv4,))
            machine_id = cursor.fetchone()[0]
            print("Machine ID:::: {0}".format(machine_id))

            #RUN_HISTORY
            sql_insert_query_for_machine_run_history = 'INSERT INTO machine_run_history (history_id, machine_id) VALUES (%s, %s)'
            cursor.execute(sql_insert_query_for_machine_run_history, (history_id, machine_id,))

            for ruleNode in ruleNodes:            
                taskNodes = ruleNode.task_node
                status = ruleNode.status
                parent_id = 0

                for section in sorted(taskNodes.keys()):
                    rule = taskNodes[section]                

                    # RULES
                    sql_select_query_for_rule_id = 'INSERT INTO compliance_rule(playbook_id, parent_id, rule, is_scored, level, expcted_value, profile1, profile2, section) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)  ON CONFLICT (playbook_id, rule, section) DO UPDATE SET rule = EXCLUDED.rule RETURNING id' 
                    cursor.execute(sql_select_query_for_rule_id, (playbook_id, parent_id, rule.rule, rule.scored, rule.level, "NA", rule.profile1, rule.profile2, section,))
                    rule_id = cursor.fetchone()[0]

                    if parent_id == 0:
                        sql_update_query_for_compliance_rule = 'UPDATE compliance_rule SET parent_id=%s WHERE id=%s'
                        cursor.execute(sql_update_query_for_compliance_rule, (rule_id, rule_id,))

                    if rule.level != 0:
                        parent_id = rule_id

                    is_compliant = 'Compliant' if status in ["OK", "CHANGED", "SKIPPED"] else 'Non-Compliant'
                    # MACHINE COMPLIANCE RULE
                    print("historyID: {0}, ruleID: {1}, status: {2}".format(history_id, rule_id, status))
                    sql_insert_query_for_run_machine_compliance_rule = 'INSERT INTO machine_compliance_rule (history_id, compliance_rule_id, status, is_compliant) VALUES (%s, %s, %s, %s) RETURNING id'
                    cursor.execute(sql_insert_query_for_run_machine_compliance_rule, (history_id, rule_id, status, is_compliant,))
            
        connection.commit()
        connection.close()