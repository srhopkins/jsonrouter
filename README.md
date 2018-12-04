
# JSON Events Router

Uses simple `yaml` based rules to take action on `JSON` events. Uses [jsonpath](https://readthedocs.org/projects/jsonpath-rw/) to scan the event message and `regex` for `includes` and `excludes` conditionals.

## Basic Usage

Simplest capture. 

```yaml
rules:
- name: notification
  routers: 
  - name: slack
    channel: my-channel
  vars:
  - name: type
    jsonpath: $..Type
    # include anything
    includes: ['.*']
    # exclude empty
    excludes: ['^$']
  message: |
    This {type} just came in
```

### Constants

You can define a constant var by providing `value` field only

```yaml
  vars:
  - name: my-constant
    value: my constant value
```

## Advanced Regex

### Match Part of String `()`

```yaml
rules:
- name: console_login
  routers: 
  - name: slack
    channel: my-channel
  vars:
  - name: detail-type
    jsonpath: $..detail-type
    includes: ['AWS Console Sign In via CloudTrail']
    excludes: ['^$']
  - name: user
    jsonpath: $..principalId
    # Match part of string
    includes: ['.*:(.*)']
    excludes: ['^$']
  - name: account
    jsonpath: $..account
    includes: ['.*']
    excludes: ['^$']    
  message: |
    Yo! {user} just signed in to {account}.
```

### Match in String with Group Name

Use `(?P<variable_name>)` to capture patterns within the matched field.

> This overrides the `vars:name` you set in the yaml and instead merges the matched name(s) declared in the regex pattern into the message format.

```yaml
rules:
- name: console_login
  routers: 
  - name: slack
    channel: my-channel
  vars:
  - name: detail-type
    jsonpath: $..detail-type
    includes: ['AWS Console Sign In via CloudTrail']
    excludes: ['^$']
  - name: user
    jsonpath: $..principalId
    # Match part of string with variable names
    includes: ['(?P<stuff>.*):(?P<user>.*)']
    excludes: ['^$']
  - name: account
    jsonpath: $..account
    includes: ['.*']
    excludes: ['^$']    
  message: |
    Yo! {user} just signed in to {account}. This {stuff} was before the user.
```

```yaml
rules:
- name: notification
  routers: 
  - name: slack
    channel: my-channel
  vars:
  - name: type
    jsonpath: $..Type
    # include anything
    includes: ['.*']
    # exclude empty
    excludes: ['^$']
  message: |
    This {type} just came in
```

## Lambda Example


```python
import json
import yaml


from jsonrouter import JsonMatchEngine, Rule, jsonify_message
from routers.slack import Slack


with open('rules/rules.yaml', 'r') as f:
    configs = yaml.safe_load(f)

registered_routers = {
    'slack': Slack(webhook='1234567890').handler
}

eng = SnsMatchEngine(configs, registered_routers)


def handler(event, context):
    # Main lambda handler function
    eng.route_matches(jsonify_message(event))
```


```python
# Load configs and some sample json

with open('examples/rules/rules.yaml', 'r') as f:
    configs = yaml.safe_load(f)
    
with open('examples/data/sample.json', 'r') as f:
    sample = json.load(f)
```


```python
handler(sample, _)
```

