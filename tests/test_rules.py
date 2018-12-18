import pytest
import yaml
import json

from jsonrouter import JsonMatchEngine, Rule, Variable


with open('examples/rules/validate.rules.yaml') as f:
  rules = yaml.load(f)

with open('examples/data/test_rules.json') as f:
  records = json.load(f)

def print_router(record):
  print(record) 

registered_routers = { 'print-router': print_router }


rules = rules['rules']


def get_var(rule, name):
  for var in rule['vars']:
    if name == var['name']:
      return var 


def test_constant(capsys):
  var_name = get_var(rules[0], 'constant')
  var = Variable(var_name)

  assert var.get_matches({}) == {'constant': 'constant-value'} 


def test_minimal_var():
  var_name = get_var(rules[0], 'minimal-var')
  var = Variable(var_name)


def test_empty_excludes_includes():
  var_name = get_var(rules[0], 'empty-excludes-includes')
  var = Variable(var_name)


def test_empty_excludes_includes_with_spaces():
  var_name = get_var(rules[0], 'empty-excludes-includes-with-spaces')
  var = Variable(var_name)

def test_empty_excludes():
  var_name = get_var(rules[0], 'empty-excludes')
  var = Variable(var_name)


def test_omit_excludes():
  var_name = get_var(rules[0], 'omit-excludes')
  var = Variable(var_name)
 

def test_include_all_exclude_empty():
  var_name = get_var(rules[0], 'include-all-exclude-empty')
  var = Variable(var_name)


def test_missing_required():
  with pytest.raises(KeyError):
    var_name = get_var(rules[0], 'missing-required')
    var = Variable(var_name)


def test_omit_template():
  rule = Rule(rules[1])


def test_missing_routers():
  with pytest.raises(KeyError):
    rule = Rule(rules[2])


def test_match_includes():
  configs = {'rules': [rules[3]]}
  eng = JsonMatchEngine(configs, registered_routers)
  matches = eng.route_matches(records)

  print(json.dumps(matches, indent=4))
  assert len(matches) == 1
  