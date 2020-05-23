#!/usr/bin/python

from ansible.module_utils.basic import *

def main():

    fields = {
        "policy_number": {"required": True, "type": "str"},
        "description": {"required": False, "type": "str"},
        "audit_info": {"required": True, "type": "str"},
        "audit_output": {"default": True, "type": "str"},
        "state": {
            "default": "pass",
            "choices": ['pass', 'fail'],
            "type": 'str'
        },
    }
    
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)

    pn = module.params['policy_number']
    desc = module.params['description']
    ai = module.params['audit_info']
    ao = module.params['audit_output']
    state = module.params['state']

    response = {"policy_number": pn, "description": desc, "audit_info": ai, "audit_output": ao, "state": state}

    module.exit_json(changed=False, result=response)

    
if __name__ == '__main__':
    main()