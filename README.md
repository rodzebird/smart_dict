# π§  SmartDict π§ 

## π­ Overview

The SmartDict library provides an override for Python dict system type.  
Along with dict features, SmartDict has a powerful [key syntax](#-key-syntax).

## π©Ί Dependencies

- **_My_ [pyutils](https://github.com/rodzebird/pyutils)** β Feel free to extract the dependencies from pyutils.

## π Quick links

- π  [How to use](#-how-to-use)
  - β­ [Initialize](#-initialize)
  - β­ [Base class](#-as-a-base-class)
  - β­ [Optional parameters](#-optional-parameters)
  - β­ [Get keys](#-how-to-get-keys)
  - β­ [Set keys](#-how-to-set-keys)
  - β­ [Reset dictionary](#-how-to-reset-the-dictionary)
- π£ [Key syntax](#-key-syntax)

## π  How to use

### β­ Initialize

```python
some_dict = {'name': 'SmartDict', 'company': 'VultureIndustries'}
sm = SmartDict(some_dict)
value = sm.get('key')
```

### β­ As a base class

Alternatively, you can use SmartDict as a base class:

```python
class MyClass(SmartDict):
    def __init__(self, some_dict):
        super().__init__(some_dict)

    def do_something(self):
        value = self.get('key')
```

### β­ Optional parameters

There are several optional parameters at initialization.  
Setting an option at initialization dictates the behavior **for all operations**.

π‘ Each option can be overriden in SmartDict methods for _oneshot usage_.

#### β Nested key delimiter (`nested_delimiter`, default β `:`)

Set the delimiter for nested keys, used in the [key syntax](#-key-syntax).

#### β Same-level key delimiter (`same_level_delimiter`, default β `/`)

Set the delimiter for same-level keys, used in the [key syntax](#-key-syntax).

#### β Toggle raise on key error (`raise_none`, default β `True`)

Toggle the raise behavior when a `KeyError` or `IndexError` _βkey not foundβ_ is raised.  
If `raise_none = False`, above errors are not raised and `None` is returned.

#### β Toggle copy/reference usage (`copy`, default β `True`)

Toggle the dictionary interaction by copy or reference.  
If `copy = False`, `SmartDict.get()` returns a reference to the dictionary.

#### π― Example

```python
some_dict = {'name': 'SmartDict', 'company': 'VultureIndustries'}
sm = SmartDict(some_dict, nested_delimiter='foo', same_level_delimiter='bar', raise_none=False, copy=False)
```

### β­ How to get keys

There are 3 methods to get a key.  
To override options from initialization, you can pass optional parameters to the following methods.

#### β Using `get()`

```python
sm = SmartDict(some_dict)

value = sm.get('key')
value = sm.get('key', copy=False)
value = sm.get('unknown_key', raise_none=False)
```

#### β Using `__call__`

```python
sm = SmartDict(some_dict)

value = sm('key')
value = sm('key', copy=False)
value = sm('unknown_key', raise_none=False)
```

#### β Using `__getitem__`

β  WARNING β When using `__getitem__`, you **cannot** pass optional parameters ; but you can use the [key syntax](#-key-syntax) β

```python
sm = SmartDict(some_dict)
value = sm['key']
```

### β­ How to set keys

There are 2 methods to set a key.  
To override options from initialization, you can pass optional parameters to the following methods.

#### β Using `set()`

```python
sm = SmartDict(some_dict)

sm.set('key', 'value')
sm.set('object_reference', object_reference, copy=False)
```

#### β Using `__setitem__`

β  WARNING β When using `__setitem__`, you **cannot** pass optional parameters ; but you can use the [key syntax](#-key-syntax) β

```python
sm = SmartDict(some_dict)

sm['key'] = 'value'
sm['object_reference'] = object_reference
```

### β­ How to reset the dictionary

The `reset()` method is used to pass a new dictionary to the instance, which is not doable with the [set() method](#-using-set) since doing a `SmartDict.set('', new_object)` will set the empty key `''` to `new_object`.

```python
sm = SmartDict(some_dict)

sm.reset({})
sm.reset({'key': 'value'})
```

---

## π£ Key syntax

The SmartDict library uses a specific key syntax to designate which keys to target in get and set operations.

### π Simple key

A simple key is designated by a string.

```python
sm = SmartDict(some_dict)
value = sm.get('key')
```

### π Nested key

Nested keys represent iterables inside other iterables.  
The equivalent in Python is using iterable brackets.

The SmartDict key syntax uses a delimiter [`nested_delimiter`](#-nested-key-delimiter-nested_delimiter-default--) defaulting to `:` and overridable.

```python
sm = SmartDict(some_dict)

value = sm.get('nested:key')

# is equivalent to
value = sm.get('nested')['key']

# is equivalent to
dictionary = sm.get()
value = dictionary['nested']['key']
```

### π Same-level keys

Same-level keys are a list of keys for the same iterable.  
The equivalent in Python is multiple statements to get the iterable keys.

The SmartDict key syntax uses a delimiter [`same_level_delimiter`](#-same-level-key-delimiter-same_level_delimiter-default--) defaulting to `/` and overridable.

```python
sm = SmartDict(some_dict)

first, second = sm.get('first/second')

# is equivalent to
first = sm.get('first')
second = sm.get('second')
```

π‘ It is particularly useful when combined with [nested keys](#-nested-same-level-keys).

### π Array key

While the key syntax is used as a string, it is possible to access dictionary array items by passing indexes in the syntax.

```python
sm = SmartDict(some_dict)

first_item = sm.get('array:0')

# is equivalent to
first_item = sm.get('array')[0]

# is equivalent to
dictionary = sm.get()
first_item = dictionary['array'][0]
```

πββοΈ **What if my dictionary contains a key named `0` ?!**  
Well... wait for an update of the library ? π¬  
We might enforce the type of the value with a special flag such as `sm.get('key:(array)0')` or `sm.get('key:(dict)0')`.

### π Dictionary selector

If the dictionary contains a list of dictionaries, you can use a special dictionary selector to access a specific dictionary.  
It prevents you from using the array keys if not known.

```python
sm = SmartDict(some_dict)

table = sm.get('database:tables:{name:users}')

# is equivalent to
table = sm.get('database:tables:0')  # with 0 being the index in the list of dictionaries β but you might not know it in advance !

# is equivalent to something like this
tables = sm.get('database:tables')
table = find_dict_in_list(tables, {'name': 'users'})
```

```python
category = sm.get('database:tables:{name:articles,size:4096}:categories:{id:1}:name')

# is equivalent to
category = sm.get('database:tables:0:categories:0:name')

# is equivalent to something like this
tables = sm.get('database:tables')
table = find_dict_in_list(tables, { 'name': 'articles' })
category = find_dict_in_list(table['categories'], { 'id': 1 })
name = category['name']
```

### π Empty key

As empty keys are valid in Python dictionaries, you can get and set empty keys with the key syntax.

βΉ _While not very useful, it is important to note that passing an empty string to `SmartDict.get()` will not return the entire dictionary but the value of the first level empty key βsame idea for `SmartDict.set()`_.

```python
sm = SmartDict(some_dict)

value = sm.get('')
value = sm.get('dict:')
value = sm.get('dict::key')

# are equivalent to
dictionary = sm.get()
value = dictionary['']
value = dictionary['dict']['']
value = dictionary['dict']['']['key']
```

```python
sm.set('', 'value')

# is equivalent to
dictionary = sm.get()
dictionary[''] = 'value'
```

### π Nested same-level keys

[Nested](#-nested-key), [same-level](#-same-level-keys), [array](#-array-key) and [empty](#-empty-key) key syntaxes can be combined to use the full power of the key syntax.

```python
sm = SmartDict(some_dict)

first_user_name, first_user_password = sm.get('website:users:0:name/password')
first, second = sm.get('nested:keys:first/second')
even_array = sm.get('nested:list:0/2/4/6/8/10')
odd_array = sm.get('nested:list:1/3/5/7/9')
```

### π With different delimiters

As [stated above](#-optional-parameters), delimiters can be set at initialization and overriden at get/set for oneshot usage.

π‘ Oneshot usage means that the optional parameters passed at get/set won't be remembered by SmartDict after **one use**.

```python
sm = SmartDict(some_dict, nested_delimiter=',', same_level_delimiter='|')

first, second = sm.get('nested,keys,first|second')
first, second = sm.get('nested>keys>first.second', nested_delimiter='>', same_level_delimiter='.')
first, second = sm.get('nested,keys,first|second')
```
