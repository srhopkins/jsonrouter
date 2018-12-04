import json
import yaml
import re

from copy import deepcopy

from jsonpath_rw import jsonpath, parse


class RuleProperties(object):
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        if isinstance(name, str):
            self.__name = name
        else:
            raise TypeError("rule name must be a string")

    @property
    def template(self):
        return self.__template

    @template.setter
    def template(self, template):
        if isinstance(template, str):
            self.__template = template
        else:
            raise TypeError("template must be a string")

    @property
    def vars(self):
        return self.__vars

    @vars.setter
    def vars(self, vars):
        if isinstance(vars, list):
            self.__vars = vars
        else:
            raise TypeError("vars must be a list/array")

    @property
    def routers(self):
        return self.__routers

    @routers.setter
    def routers(self, routers):
        if isinstance(routers, list):
            self.__routers = routers
        else:
            raise TypeError("routers must be a list/array")


class Rule(RuleProperties):
    ''' One rule from `rules` root of yaml

    - name: scaling
      routers:
      - name: slack
        channel: sysops-prod
      vars:
      - name: type
        jsonpath: $..Type
        includes: ['.*']
        excludes:
      template: |
        This {type} just came in

    '''

    def __init__(self, data):
        # Make sure we have required fields and nothing extra
        validate_keys({
            'name',
            'routers',
            'vars',
            'template'
        }, data.keys())

        self.__data = data

        self.name = data['name']
        self.template = data['template']

        self.vars = [Variable(var) for var in data['vars']]

        self.routers = data['routers']

    def __repr__(self):
        return "{cls}(name='{name}')".format(cls=self.__class__.__name__, name=self.name)


    def get_matches(self, json_data):
        m = {}
        for var in self.vars:
            match = var.get_matches(json_data)
            if match == False:
                # Field not found or did not match criteria
                return

            if match:
                # Merge dict together for all matches
                m = {**m, **match}

        return m


class VariableProperties(object):
    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        if isinstance(name, str):
            self.__name = name
        else:
            raise TypeError("name must be a string")

    @property
    def jsonpath(self):
        return self.__jsonpath

    @jsonpath.setter
    def jsonpath(self, jsonpath):
        if isinstance(jsonpath, str):
            self.__jsonpath = jsonpath
        else:
            raise TypeError("jsonpath must be a string")

    @property
    def includes(self):
        return self.__includes

    @includes.setter
    def includes(self, includes):
        if isinstance(includes, list):
            self.__includes = includes
        else:
            raise TypeError("includes must be a list/array")

    @property
    def excludes(self):
        return self.__excludes

    @excludes.setter
    def excludes(self, excludes):
        if isinstance(excludes, list):
            self.__excludes = excludes
        else:
            raise TypeError("excludes must be a list/array")


class Variable(VariableProperties):
    ''' One var from `vars` array in rule

    - name: type
      jsonpath: $..Type
      includes: ['.*']
      excludes:

    '''

    def __init__(self, variable):
        self.__data = variable
        self.name = variable['name']

        # Check if variable has a constant `value` defined
        if not variable.get('value'):
            # Make sure we have required fields and nothing extra
            validate_keys({
                'name',
                'jsonpath',
                'includes',
                'excludes'
            }, variable.keys())

            self.jsonpath = variable['jsonpath']

            # Check for includes field then compile as regex to
            # confirm proper regex format. Defaults to all `[.*]`
            includes = variable.get('includes')
            if includes:
                try:
                    self.includes = [re.compile(regex) for regex in includes]
                except (TypeError, re.error):
                    # TypeError should be trying to iterate on non list
                    # re.error should be compile error; indicates bad regex
                    raise
            else:
                self.includes = ['.*']

            # Check for excludes field then compile as regex to
            # confirm proper regex format. Defaults to no excludes `[]`
            excludes = variable.get('excludes')
            if excludes:
                try:
                    self.excludes = [re.compile(regex) for regex in excludes]
                except (TypeError, re.error):
                    # TypeError should be trying to iterate on non list
                    # re.error should be compile error; indicates bad regex
                    raise
            else:
                self.excludes = []


    def __repr__(self):
        return "{cls}(name='{name}')".format(cls=self.__class__.__name__, name=self.name)


    def get_matches(self, json_data):
        # If its a constant (e.g. value: <value> in yaml) return value
        if self.__data.get('value'):
            return {self.name: self.__data.get('value')}

        m = get_jsonpath(self.jsonpath, json_data)
        if isinstance(m, list) and m:
            # Is it a non-empty list?? Join it
            match = ''.join(m)
        else:
            # This condition means the field wasn't found
            return False

        for exclude in self.excludes:
            if exclude.match(match):
                return False

        for include in self.includes:
            m = include.match(match)
            if m:
                return get_groups(self.name, m)


class JsonMatchEngine(object):
    def __init__(self, configs, registered_routers):
        self.rules = [Rule(rule) for rule in configs['rules']]
        self.registered_routers = registered_routers

    def match_rules(self, records):
        r = []
        for rule in self.rules:
            for rec in records['Records']:
                vrs = rule.get_matches(rec)
                if vrs:
                    r.append({
                        'name': rule.name,
                        'routers': rule.routers,
                        'vars': vrs,
                        'template': rule.template
                    })
        return r

    def route_matches(self, records):
        matched_rules = self.match_rules(records)
        if matched_rules:
            for matched_rule in matched_rules:
                for r in matched_rule.get('routers'):
                    rname = r.get('name')
                    if rname:
                        router = self.registered_routers.get(rname)
                        if router:
                            router(matched_rule)
                    else:
                        # Will error with name not registered or None if name field not supplied
                        raise KeyError(
                            "'{name}' is not a registered router".format(name=rname))


def validate_keys(accept_keys, keys):
    # Checks to make sure all keys are present and nothing extra
    accept_keys = set(accept_keys)
    keys = set(keys)

    missing = accept_keys.difference(keys)
    extra = keys.difference(accept_keys)

    if missing or extra:
        raise KeyError('Missing fields: {missing}. Extra fields: {extra}'.format(
            missing=missing, extra=extra))
    else:
        return True


def get_jsonpath(path, json_data):
    r = []
    path = parse(path)
    for match in [match.value for match in path.find(json_data)]:
        if match:
            r.append(match)
        else:
            r.append('')

    return r


def get_groups(var_name, matches):
    if not isinstance(matches, gtype):
        raise TypeError(
            "expected match object of type re.match(r'[pattern]', '')")

    r = {}

    #  print(matches.groupdict()) # contains dict of named regex matches e.g. `(?P<var_name>) == {'var_name': 'match'}`
    #  print(matches.groups()) # contains list of matches e.g. `(.*):(.*) == ('match1', 'match2')
    #  print(matches.group()) # single match only

    if matches.groups():
        r[var_name] = ' '.join(matches.groups())
    if matches.group():
        if not r.get(var_name):
            r[var_name] = matches.group()
    if not r:
        r[var_name] = ''
    if matches.groupdict():
        # This overrides any previous r[var_name]
        r = {**r, **matches.groupdict()}

    return r


def jsonify_string(records):
    # This converts SNS `['Records'][*]['Sns']['Message']` field from string to json
    rcrds = deepcopy(records)

    for record in rcrds['Records']:
        message = record['Sns']['Message']
        if isinstance(message, str):
            try:
                record['Sns']['Message'] = json.loads(message)
            except json.JSONDecodeError:
                raise

    return rcrds


# Get a match's type for later error checking
gtype = type(re.match(r'.*', ''))
