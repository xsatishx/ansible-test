#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule

def main():

    fields = {
        "section": {"required": True, "type": "str"},
        "description": {"required": False, "type": "str"},
        "info": {"required": True, "type": "str"},
        "cmd_output": {"default": "", "type": "str"},
        "isManual": {"default": False, "type": "bool"},
        "isRemediate": {"default": False, "type": "bool"},
        "state": {
            "default": "error",
            "choices": ['passed', 'failed', 'error', 'changed', 'manual'],
            "type": 'str'
        },
    }
    
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)

    section = module.params['section']
    desc = module.params['description']
    info = module.params['info']
    #info = info.replace(" ", "&nbsp;")
    #info = info.replace("\n", "<br>")
    cmd_output = module.params['cmd_output']
    state = module.params['state']    
    isManual = module.params['isManual']  
    isRemediate = module.params['isRemediate']  

    #if isRemediate and state != "changed":
    #    cmd_output = ''

    if isRemediate and state == "passed":
       cmd_output = ''

    #isRemediate = module.params['isRemediate']   

    # if isRemediate:
    #     if state == "changed" or state == "passed":
    #         state = "changed"
    # else:
    #     if state == "changed" or state == "passed":
    #         state = "passed"

    response = {"section": section, "description": desc, "info": info, "cmd_output": cmd_output, "state": state, "isManual": isManual}

    module.exit_json(changed=False, moveit=response)

    
if __name__ == '__main__':
    main()