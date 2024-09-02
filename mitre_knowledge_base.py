import requests
import json
from stix2 import MemoryStore
from stix2 import Filter
from simulator_config import (mitre_github_attack_stix_data_url, knowledgebase_db_location, knowledgebase_location,
                              execution_logger_name)
import logging
from itertools import chain

exec_logger = logging.getLogger(execution_logger_name)


def update_knowledge_base(db_url=mitre_github_attack_stix_data_url, knowledgebase_db_path=knowledgebase_db_location):
    exec_logger.info('MITRE knowledgebase update request')
    with open(knowledgebase_db_path, 'w', encoding='UTF-8') as f:
        r = requests.get(db_url)
        if r.status_code != 200:
            exec_logger.error('Error while getting MITRE knowledgebase')
            exec_logger.debug(f'Error while getting MITRE knowledgebase. Debug request info: {r.request} {r.text}')
            raise RuntimeError
        json.dump(r.json(), f, indent=4)


def _get_db(knowledgebase_db_path=knowledgebase_db_location):
    with open(knowledgebase_db_path, encoding='UTF-8') as f:
        return json.load(f)


def load_stix_db_into_memory():
    exec_logger.info('Loading MITRE knowledgebase into the memory, it will take some time ...')
    db = _get_db()
    return MemoryStore(stix_data=db)


def get_all_tactics(stix_data):
    return stix_data.query(Filter("type", "=", "x-mitre-tactic"))


def get_techniques_or_subtechniques(thesrc, include="both"):
    """Filter Techniques or Sub-Techniques from ATT&CK Enterprise Domain.
    include argument has three options: "techniques", "subtechniques", or "both"
    depending on the intended behavior."""
    if include == "techniques":
        query_results = thesrc.query([
            Filter('type', '=', 'attack-pattern'),
            Filter('x_mitre_is_subtechnique', '=', False)
        ])
    elif include == "subtechniques":
        query_results = thesrc.query([
            Filter('type', '=', 'attack-pattern'),
            Filter('x_mitre_is_subtechnique', '=', True)
        ])
    elif include == "both":
        query_results = thesrc.query([
            Filter('type', '=', 'attack-pattern')
        ])
    else:
        raise RuntimeError("Unknown option %s!" % include)

    return query_results


def get_software(thesrc):
    return list(chain.from_iterable(
        thesrc.query(f) for f in [
            Filter("type", "=", "tool"),
            Filter("type", "=", "malware")
        ]
    ))

# if __name__ == '__main__':
#     update_knowledge_base()
# else:
#     stix_data = load_stix_db_into_memory()

#stix_data = load_stix_db_into_memory()