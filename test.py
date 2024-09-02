import json
import stix2
import attack_flow_model as attack_model

action1 = attack_model.AttackAction(name="Test Action", tactic_id='asds')
a = attack_model.AttackFlow(name="Test Attack Flow", start_refs=[action1], created_by_ref='identity--0')
with open(r'configs/attack_flow_ext.json') as f:
    att_ex = json.load(f)
att_ex = stix2.ExtensionDefinition(**att_ex)
b = stix2.Bundle(a, action1, att_ex)
print(b.serialize(pretty=True))
