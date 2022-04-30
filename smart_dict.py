import re
import copy

from pyutils.atomic import to_int
from pyutils.collection import index_of


class SmartDict:
    """
    Provide an encapsulation of Python system-type dict.

    Along with native dict features, SmartDict has a powerful key syntax
    allowing the access of keys and values in horizontal and vertical depth.

    The SmartDict class powerful key syntax provided allows the use of three
    main mechanisms when using keys:

    Nested keys delimiters are used to work with vertical depth as a list of
    keys in which the n key contains the n+1 key, etc. In short, using nested
    keys delimiters is equivalent to fetching a dictionary value by key and looping on this operation to find the nth key-value.
    E.g.: SmartDict.get('key1:key2')
          is equivalent to
          smart_dict['key1']['key2']

    Many keys delimiters are used to work with horizontal depth as a list of
    keys in which each key is contained in the same-level dictionary. In short,
    using many keys delimiter is equivalent to fetching several values of
    a dictionary one by one, but with a single operation.
    E.g.: SmartDict.get('key1/key2')
          is equivalent to
          (smart_dict['key1'], smart_dict['key2'])

    Array keys are used to find values of arrays with a specific index inside the key syntax. In short, instead of fetching a dictionary array and then
    accessing the array item of index n, the whole operation can be done once.
    It is particularly useful when fetching a value from a deep key in which you have to cross dictionaries and arrays.
    E.g.: SmartDict.get('key1:0:key2')
          is equivalent to
          smart_dict['key1'][0]['key2']

    Dictionary selectors are used to find specific dictionaries in an
    array from the SmartDict. In short, instead of fetching an array
    contained in the SmartDict and then looping over this array to find
    a specific item, you can use the SmartDict dictionary selectors
    in a single operation.
    E.g.: SmartDict.get('database:tables:{name:users,size:4096}')
          is equivalent to
          tables = SmartDict.get('database:tables')
          for table in tables:
            if table['name'] == 'users' and table['size'] == 4096:
                return table

    The last strength of this powerful key syntax is the ability to combine
    all these features to manipulate a SmartDict efficiently and with elegance.
    E.g: SmartDict.get('database:tables:{name:users,size:4096}:0:name/city')
         is equivalent to
         tables = SmartDict.get('database:tables')
         user_table = None
         for table in tables:
            if table['name'] == 'users' and table['size'] == 4096:
                user_table = table
         name, city = (None, None)
         if user_table:
            user = user_table[0]
            name, city = (user['name'], user['city'])
         return name, city
    """

    class __NoDefault:
        """
        Empty class acting as a replacement for default values in method parameters.

        This is useful since the usual None default value can be used by the user as a specific None value.
        For example, if the user specifies SmartDict.get('key', default=None),
        the method will consider that the user WANTS a default value None if
        the key is not found, whereas if the default value equals __NoDefault,
        the user did not specify any default value and therefore will receive
        the KeyError behaviour with unknown keys.
        """

        pass

    _DEFAULT_NONE = __NoDefault()
    DEFAULT_NESTED_DELIMITER = ":"
    DEFAULT_MANY_KEYS_DELIMITER = "/"

    def __init__(self, dictionary=None, **kwargs):
        """
        Initialize a SmartDict either as an empty dict or with the given `dictionary` dict parameter.

        :param dictionary: An existing dictionary to populate the SmartDict
                           and make use of the SmartDict mechanisms.
        :type dictionary: dict
        :param kwargs: A list of SmartDict options changing the behaviour
                       of SmartDict manipulation. These options are
                       "set in stone" but can be overriden in
                       each SmartDict.get() call.
                       See SmartDict.set_options() for more information.
        :type kwargs: dict
        """
        self.__dict = {}

        if dictionary:
            self.update(dictionary)

        self.set_options(**kwargs)

    def __str__(self):
        return str(self.__dict)

    def __repr__(self):
        return "<SmartDict {}>".format(self.__dict)

    def __eq__(self, other):
        return self.__dict == other

    def __getitem__(self, key):
        """
        Find the item designated by the given key in the SmartDict.

        WARNING, using this method, SmartDict options cannot be overriden.
        For more information on the fetch method, see `SmartDict.get()`.

        :param key: The key to find in the SmartDict.
        :type key: str

        :return: The value of the given key in the SmartDict.
                 if the key does not exist, either return the optional default
                 value set in the SmartDict options or raise
                 a KeyError exception.
        :rtype: Any
        """
        return self.get(key)

    def __setitem__(self, key, value):
        """
        Set the value to the SmartDict key using the SmartDict.set() method.

        WARNING, using this method, SmartDict options cannot be overriden.
        For more information on the assignation method, see `SmartDict.set()`.

        :param key: The key to find in the SmartDict.
        :type key: str
        :param value: The value to set to the key.
        :type value: str
        """
        self.set(key, value)

    def __call__(self, *args, **kwargs):
        """
        Find the item designated by the given key in the SmartDict.

        For more information on the fetch method, see `SmartDict.get()`.

        :param args.key: The key to find in the SmartDict.
        :type args.key: str
        :param args.default: The default value to return if the key
                             is not found. If not given, a KeyError exception
                             is raised if the key is not found.
        :type args.default: Any
        :param kwargs: A list of SmartDict options changing the behaviour
                       of SmartDict manipulation. These options override the
                       SmartDict options set in the initializer for the
                       current method call, but not for the entire
                       SmartDict lifespan.
                       See SmartDict.set_options() for more information.
        :type kwargs: dict

        :return: The value of the given key in the SmartDict.
                 if the key does not exist, either return the optional default
                 value set in the SmartDict options or raise
                 a KeyError exception.
        :rtype: Any
        """
        return self.get(*args, **kwargs)

    def __contains__(self, item):
        """
        Check if the SmartDict contains the given item.

        :param item: The item to find in the SmartDict.
        :type item: Any

        :return: True if the item is contained in the SmartDict,
                 else False.
        :rtype: bool
        """
        return item in self.__dict

    def set_options(self, **kwargs):
        """
        Set the SmartDict options that will change the behaviour of the SmartDict during its manipulation.

        This method is automatically called at SmartDict initialization
        if options are passed but can also be called during the
        SmartDict lifespan based on the needs of the users.

        These options are "set in stone", which means they will be used
        by default in every SmartDict special behaviours encounters if
        the user did not override them manually.

        :param kwargs.copy: Option used to specify if the values returned
                            while fetching SmartDict items are copied
                            or returned as reference. By default the values
                            are returned as copies, but passing a False value
                            will return the fetched values as references
                            -i.e. modifiable externally and impacting the
                            SmartDict corresponding value.
        :type kwargs.copy: bool
        :param kwargs.raise_none: Option used to specify if the SmartDict
                                  should raise an exception when encountering
                                  unknown keys and thus IndexError, KeyError
                                  and ValueError exceptions. By default the SmartDict
                                  raises exceptions in those encounters to mimic
                                  the system-type dict behaviour.
                                  If `raise_none` is set to False,
                                  the encounters described above will either
                                  return the `default` value set manually in
                                  the SmartDict.get() method or `None`.
        :type kwargs.raise_none: bool
        :param kwargs.nested_delimiter: Set the delimiter for nested keys
                                        using the SmartDict powerful
                                        key syntax. This delimiter will be used
                                        to separate keys from the `key`
                                        parameter passed in the SmartDict
                                        access methods.
                                        Nested keys are a suite of keys in
                                        which the n key contains the n+1 key.
                                        E.g.: 'key1:key2:key3' represents a
                                        dict {'key1': {'key2': {'key3': ...}}}.
                                        By default, this delimiter is set to
                                        SmartDict.DEFAULT_NESTED_DELIMITER.
        :type kwargs.nested_delimiter: string
        :param kwargs.many_keys_delimiter: Set the delimiter for same level
                                           keys using the SmartDict powerful
                                           key syntax. This delimiter will be
                                           used to separate keys from the `key`
                                           parameter passed in the SmartDict
                                           access methods.
                                           Same level keys are a list of keys
                                           from the same dictionary depth and
                                           thus cannot contain duplicates.
                                           E.g.: 'key1/key2/key3' represents a
                                           dict {'key1': ..., 'key2': ...,
                                           'key3': ...}.
                                           By default, this delimiter is set to
                                           SmartDict.DEFAULT_MANY_KEYS_DELIMITER.
        :type kwargs.many_keys_delimiter: string
        """
        self.__as_copy = kwargs.pop("copy", True)
        self.__raise_none = kwargs.pop("raise_none", True)
        self.__nested_delimiter = kwargs.pop("nested_delimiter", SmartDict.DEFAULT_NESTED_DELIMITER)
        self.__many_keys_delimiter = kwargs.pop("many_keys_delimiter", SmartDict.DEFAULT_MANY_KEYS_DELIMITER)

    def reset(self, dictionary=None, **kwargs):
        """
        Reset the SmartDict by overriding the inner dictionary with the given dictionary.

        Override the inner dictionary with the given `dictionary` dict if not None
        and by reseting the options to either the given options or their default values.

        :param dictionary: The dictionary replacing the SmartDict inner
                           dictionary. Optional and if not given the SmartDict
                           will reset its options only.
        :type dictionary: dict
        :param kwargs: A list of SmartDict options changing the behaviour
                       of SmartDict manipulation. These options override the
                       SmartDict options set in the initializer for the
                       current method call, but not for the entire
                       SmartDict lifespan.
                       See SmartDict.set_options() for more information.
        :type kwargs: dict
        """
        if dictionary is not None:
            self.__dict = self.__copy(dictionary, as_copy=True)
        self.set_options(**kwargs)

    def update(self, dictionary):
        """
        Update the SmartDict inner dictionary with the given dictionary values.

        The new keys are added to the SmartDict.
        The existing keys replace the SmartDict ones.
        Similar to the system-type dict update() method.

        :param dictionary: The dictionary containing the keys to add to
                           the SmartDict.
        :type dictionary: dict
        """
        self.__dict.update(dictionary)

    def get(self, key=None, default=_DEFAULT_NONE, **kwargs):
        """
        Return the dictionary value for the given key using the
        SmartDict powerful key syntax.

        :param key: The key to find in the SmartDict.
        :type key: str
        :param default: The default value to return if the key
                        is not found. If not given, a KeyError exception
                        is raised if the key is not found.
        :type default: Any
        :param kwargs: A list of SmartDict options changing the behaviour
                       of SmartDict manipulation. These options override the
                       SmartDict options set in the initializer for the
                       current method call, but not for the entire
                       SmartDict lifespan.
                       See SmartDict.set_options() for more information.
        :type kwargs: dict

        :return: The value of the given key in the SmartDict.
                 if the key does not exist, either return the optional default
                 value set in the SmartDict options or raise
                 a KeyError exception.
        :rtype: Any
        """
        as_copy = kwargs.pop("copy", self.__as_copy)
        raise_none = kwargs.pop("raise_none", self.__raise_none)
        delimiter = kwargs.pop("nested_delimiter", self.__nested_delimiter)
        many_keys_delimiter = kwargs.pop("many_keys_delimiter", self.__many_keys_delimiter)

        value = copy.deepcopy(self.__dict) if as_copy else self.__dict
        if key is None:
            return value

        key, dictionary_selectors = self.__split_key_selectors(key)
        keys = key.split(delimiter)

        for index, key in enumerate(keys):
            match = re.match(r"\{(\d)\}", key)
            if match:
                pattern = dictionary_selectors[int(match.group(1))]
                key = index_of(value, pattern)
                if key == -1:
                    if raise_none:
                        return None
                    else:
                        raise KeyError("No match for pattern {}".format(pattern))
            elif many_keys_delimiter in key:
                if index < len(keys) - 1:
                    raise KeyError("Found a many-keys delimiter before end level.")

                subkeys = key.split(many_keys_delimiter)
                return tuple(self.__access(value, subkey, raise_none, default) for subkey in subkeys)

            if isinstance(value, list) or isinstance(value, tuple):
                key = to_int(key)

            value = self.__access(value, key, raise_none, default)

        return value

    def set(self, key, value, **kwargs):
        """
        Set the value to the SmartDict key using the SmartDict key syntax.

        :param key: The key to find in the SmartDict.
        :type key: str
        :param value: The value to set to the key.
        :type value: Any
        :param kwargs: A list of SmartDict options changing the behaviour
                       of SmartDict manipulation. These options override the
                       SmartDict options set in the initializer for the
                       current method call, but not for the entire
                       SmartDict lifespan.
                       See SmartDict.set_options() for more information.
        :type kwargs: dict
        """
        as_copy = kwargs.pop("copy", self.__as_copy)
        raise_none = kwargs.pop("raise_none", self.__raise_none)
        delimiter = kwargs.pop("nested_delimiter", self.__nested_delimiter)
        many_keys_delimiter = kwargs.pop("many_keys_delimiter", self.__many_keys_delimiter)

        key, dictionary_selectors = self.__split_key_selectors(key)
        keys = key.split(delimiter)
        pointer = self.__dict

        for _, key in enumerate(keys[:-1]):
            match = re.match(r"\{(\d)\}", key)
            if match:
                pattern = dictionary_selectors[int(match.group(1))]
                key = index_of(pointer, pattern)
                if key == -1:
                    if raise_none:
                        return None
                    else:
                        raise KeyError("No match for pattern {}".format(pattern))
            if isinstance(pointer, list) or isinstance(pointer, tuple):
                key = to_int(key)
            pointer = self.__access(pointer, key, raise_none)

        last_key = keys[-1]
        if many_keys_delimiter in last_key:
            if not isinstance(value, list) and not isinstance(value, tuple):
                raise TypeError("Found a many-keys delimiter with a not iterable value.")
            subkeys = last_key.split(many_keys_delimiter)
            if len(subkeys) != len(value):
                raise ValueError("Not same number of same-level keys and values.")

            for i, subkey in enumerate(subkeys):
                pointer[subkey] = self.__copy(value[i], as_copy)
        else:
            pointer[last_key] = self.__copy(value, as_copy)

    def __copy(self, value, as_copy=None):
        """
        Copy the value deeply if the `as_copy` inner option or user option
        is set, else just return it by reference.

        :param value: The value to either copy or return by reference.
        :type value: Any
        :param as_copy: Option to specify if the value should be copied or
                        returned by reference. If not specified, the as_copy
                        SmartDict option will be used if specified. Else, the
                        value is returned by reference.
        :type as_copy: bool

        :return: The value copied or referenced.
        :rtype: Any
        """
        as_copy = as_copy or self.__as_copy
        return copy.deepcopy(value) if as_copy else value

    def __split_key_selectors(self, key):
        """
        Extract the dictionary selectors from the given key, following
        the dictionary selector key syntax of the SmartDict class.

        If there are dictionary selectors in the key, they are extracted in a returned list and replaced in the key with `{n}`, n being the index
        of the dictionary selector.

        E.g.: For key 'database:tables:{name:users,size=4096}:name/city',
              the returned key will be 'database:tables:{0}:name/city'
              and the selectors will be [{'name': 'users', 'size': 4096}]

        :param key: The key using a SmartDict key syntax
                    possibly containing dictionary selectors to split.
        :type key: str

        :return: A tuple containing the key with its dictionary selectors
                 replaced with their index and a list of dictionaries
                 corresponding to the associated selectors.
        :rtype: tuple(str, list)
        """
        i = 0
        pattern = r"(?:\{(.*?)\})"
        dictionary_selectors = []

        for match in re.finditer(pattern, key):
            dictionary = {}
            whole_selector = match.group(1)
            selectors = whole_selector.split(",")
            for selector in selectors:
                k, v = selector.split(":")
                if to_int(v) is not None:
                    v = to_int(v)
                dictionary[k] = v
            key = key.replace("{{{}}}".format(whole_selector), "{{{}}}".format(i), 1)
            dictionary_selectors.append(dictionary)
            i += 1

        return key, dictionary_selectors

    def __access(self, collection, key, raise_none=False, default=_DEFAULT_NONE):
        """
        Access the value associated to the key in the collection.
        Perform a simple collection.__getitem__ but encapsulate the operation
        with SmartDict options `raise_none` and `default`.
        If the key does not exist, if raise_none is True and default is not
        _DEFAULT_NONE, return the default value, else raise the appropriate
        exception being either KeyError, IndexError or TypeError.

        :param collection: The collection in which to access the value
                           for the given key. Thanks to collection.__getitem__,
                           there is no specification about the collection
                           being a list, a tuple or even a dict.
        :type collection: list or tuple or dict
        :param key: The key to find in the collection in order to
                    access the value.
                    WARNING, the key DOES NOT follow the SmartDict key syntax,
                    it must be a single key accessible like accessing
                    any collection key/index.
        :type key: int or str
        :param raise_none: Option used to specify if the SmartDict
                           should raise an exception when encountering
                           unknown keys and thus IndexError, KeyError
                           and ValueError exceptions.
                           By default the SmartDict raises
                           exceptions in those encounters to mimic
                           the system-type dict behaviour.
                           If `raise_none` is set to False,
                           the encounters described above will either
                           return the `default` value set manually in
                           the SmartDict.get() method or `None`.
        :type raise_none: bool
        :param default: The default value to return if the key
                        is not found. If not given, a KeyError exception
                        is raised if the key is not found.
        :type default: Any

        :return:
        :rtype:
        """
        try:
            return collection[key]
        except (KeyError, IndexError, TypeError):
            if default == self._DEFAULT_NONE and raise_none:
                raise

        return None if default == self._DEFAULT_NONE else default
