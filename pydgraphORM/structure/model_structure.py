#from .model_structure import dgraphModel, dgraphTypes, dgraphUID, dgraphID, dgraphString, dgraphInt, dgraphFloat, dgraphBool, dgraphGeo, dgraphDate
from .flags_structure import dgraphFlags
from textwrap import dedent
import random
import hashlib
import time
import copy


# Generate Random
SECRET_KEY = 'CC9S5AIiEtFvqn1Rg3YxryaVVmvxDWLecUVq94BezrwcwY25MT'

try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    import warnings
    warnings.warn('A secure pseudo-random number generator is not available '
                  'on your system. Falling back to Mersenne Twister.')
    using_sysrandom = False

def get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyz''ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    if not using_sysrandom:
        random.seed(
            hashlib.sha256(
                ("%s%s%s" % (
                    random.getstate(),
                    time.time(),
                    SECRET_KEY)).encode('utf-8')
            ).digest())
    return ''.join(random.choice(allowed_chars) for i in range(length))

def _name(cls):
    if hasattr(cls, "__name__"):
        return cls.__name__
    else:
        return cls.__class__.__name__

# Tasks: Storing data and properties, generating schema and nornmal output
# DgraphTypes
class dgraphTypes():
    validFlags = ["index", "reverse", "schema", "require"]
    validTypes = {t: "<class '{0}'>".format(
        t) for t in ["str", "int", "float", "bool"]}
    validSchemaTypes = [
        "string", "int", "float", "bool", "id", "date", "geo", "uid"]

    def __init__(self, *args, **kwargs):
        # Initiation Flags
        flags = {f: False for f in self.validFlags}
        flags["default"] = None

        for k in list(kwargs):
            if k in self.validFlags and kwargs[k] == True:
                flags[k] = True

        if "default" in kwargs:
              flags["default"] = kwargs["default"]

        self.requireSchema = any(
            [value for key, value in flags.items() if key != "require"])

        # print(flags["reverse"])

        self.flags = type('flags', (object,), flags)

        self.qflags = None
        self.varName = None
        self.setget = None
        self.prefix = ""

    @classmethod
    def invalidType(cls, typ, input, requestType=None):
        if not str(type(input)) == cls.validTypes[typ] and not str(type(input)) == "<class 'tuple'>" and not (requestType=="delete" and (input == "*" or input == None)):
            raise BaseException("Invalid type bypassed")
        else:
            cls.type = typ

    def setValue(self, uid, name, value, requestType=None):
        self.invalidType(self.vtype, value, requestType)
        new = copy.copy(self)
        new.uid = uid
        new.name = name
        new._value = value
        new.type = requestType
        new.setget = 0
        return new

    def queryValue(self, name, qflags=None, requestType=None):
        new = copy.copy(self)
        new.name = name
        new.qflags = qflags
        new.type = requestType
        new.setget = 1
        return new

    def setVar(self, name=None):
        if name == None:
            name = get_random_string()
        self.varName = name
        return self

    
    #Input#
    def _prechcheckVar(self, var):
        if self.type == "delete" and var == None:
            return "*"
        else:
            return '"{0}"'.format(var)
             

    def _genSingleInput(self, uid, name, value):
        if self.varName != None:
            return "{3} AS {0} <{1}> {2}".format(uid, name, value, self.varName)
        else:
            return "{0} <{1}> {2}".format(uid, name, value)

    ####Parser#####
    def _genSchema(self, name, vtype, flags):
        return "{0}: {1} {2}".format(name, vtype, flags)

    def _genInput(self):
        uid = self.uid
        name = "{0}{1}".format(self.prefix, self.name)
        value = self._value
        vtype = self.vtype
        stype = self.schemaType

        vset = []
        if isinstance(self._value, (tuple)):
            if isinstance(self._value[0], (tuple)):
                for t in self._value:
                    vset.append(
                        self._genSingleInput(uid, name, '''{0}@{1}'''.format(self._prechcheckVar(t[0]), t[1])))
            else:
                vset.append(
                    self._genSingleInput(uid, name, '''{0}@{1}'''.format(self._prechcheckVar(value[0]), value[1])))
        elif value.__class__.__bases__[0].__name__ == "dgraphModel":
            vset.append(
                self._genSingleInput(uid, name, '''{0}'''.format(value._uid)))
        else:
            vset.append(
                self._genSingleInput(uid, name, '''{0}'''.format(self._prechcheckVar(value))))

        if self.requireSchema == True:
            _index = getattr(self.flags, "index")
            _flags = []

            if _index != False:
                if self.schemaType in ("string", "id"):
                    if _index == True:
                        _tp = "term"
                    else:
                        _tp = _index
                else:
                    if _index == True:
                        _tp = self.schemaType
                    else:
                        _tp = _index

                _flags.append("index({0})".format(_tp))

            _flags += [v for v in ["reverse"]
                       if getattr(self.flags, v) == True]

            _flags = " ".join(
                ["@{0}".format(v) for v in _flags])

            schema = self._genSchema(name, stype, _flags)
            return (".\n".join(vset), schema)
        else:
            return (".\n".join(vset), None)

    #Output#
    def _genOutput(self):
        _querySub = '''{0} {1}{{
            {2}
        }}'''
        _querySubVar = '''{3} AS {0} {1}{{
            {2}
        }}'''
        _queryPart = '''{0} {1}'''
        _queryPartVar = '''{2} AS {0} {1}'''

        # ToDo: Input generation for other models
        # if val.__class__.__bases__[0].__name__ == "dgraphTypes":
        #   varName = value.__bases__._regVar(val.__name__)
        #   value = callableM.setValue(uid, name, 'var({0})'.format(varName), vtype)
        #   self._set.append(value)

        flags = self.qflags
        if flags != None:
            flags._prefix = self.prefix

        stype = self.schemaType 
        name = "{0}{1}".format(self.prefix, self.name)
        varName = self.varName

        _inner = []

        if flags == None:
            flags = ""

        if stype == 'uid':
            if flags._sub == []:
                raise "No child query properties defined"
            _sub = "\n".join([s.gen for s in flags.sub])
            if varName != None:
                _inner.append(_querySubVar.format(name, flags, _sub, varName))
            else:
                _inner.append(_querySub.format(name, flags, _sub))
        else:
            if varName != None:
                _inner.append(_queryPartVar.format(name, flags, varName))
            else:
                _inner.append(_queryPart.format(name, flags))

        return "\n".join(_inner)

    @property
    def gen(self):
        if self.setget == 0:
            return self._genInput()
        else:
            return self._genOutput()


class dgraphUID(dgraphTypes):
    schemaType = "uid"
    vtype = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setValue(self, uid, name, value, requestType=None):
        if not _name(value.__class__.__base__) == "dgraphModel":
            raise BaseException("Invalid type bypassed")
        new = copy.copy(self)
        new.uid = uid
        new.name = name
        new._value = value
        new.type = requestType
        new.setget = 0
        return new


class dgraphID(dgraphTypes):
    schemaType = "id"
    vtype = "int"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class dgraphString(dgraphTypes):
    schemaType = "string"
    vtype = "str"

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


class dgraphPassword(dgraphTypes):
    schemaType = "string"
    vtype = "str"

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def value(self):
        return '''"{0}"^^<pwd:password>'''.format(self._value)


class dgraphInt(dgraphTypes):
    schemaType = "int"
    vtype = "int"

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


class dgraphFloat(dgraphTypes):
    schemaType = "float"
    vtype = "float"

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


class dgraphBool(dgraphTypes):
    schemaType = "bool"
    vtype = "bool"

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


class dgraphGeo(dgraphTypes):
    schemaType = "geo"
    vtype = "str"

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


class dgraphDate(dgraphTypes):
    schemaType = "date"
    vtype = "str"

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)


# Model generator
class dgraphModel():
    disableSchema = False
    validModelTypes = [_name(m)for m in [dgraphUID, dgraphID, dgraphString,
                                         dgraphInt, dgraphFloat, dgraphBool, dgraphGeo, dgraphDate, dgraphPassword]]
    pushTypes = ("set", "delete")
    pullTypes = ("query", "recurse", "var")

    def __init__(self, *args, **kwargs):
        self.modelName = str(self.__class__.__name__)
        self.meta = type('metaType', (object,), {})
        if hasattr(self, '__meta__'):
            self.__meta__()


    def _name(self, name):
        return name

    ##################
    #dgraphModel.push#
    ##################
    def _push(self, vtype, *args, **kwargs):
        if hasattr(self.meta, "staticID"):
            uid =  "<{0}>".format(self.meta.staticID)
            skipRequire = True
        else:
            if "uid" in kwargs:
                uid = "<{0}>".format(kwargs["uid"])
                skipRequire = True
            else:
                uid = "_:{0}".format(get_random_string())

        self._uid = uid
        if not hasattr(self, "_set"):
            self._set = []

        _set = []
        for name in dir(self):
            callableM = getattr(self, name)
            if callableM.__class__.__bases__[0].__name__ == "dgraphTypes":
                if name in kwargs:
                    callName = _name(callableM)
                    if callName in self.validModelTypes:
                        val = kwargs[name]
                        value = callableM.setValue(
                            uid, self._name(name), val, vtype)
                        _set.append(value)
                elif callableM.flags.require == True and skipRequire != True:
                    if callableM.flags.default == None:
                        raise Exception("Value {0} required.".format(name))
                    else:
                        val = callableM.flags.default
                        value = callableM.setValue(uid, self._name(name), val, vtype)
                        _set.append(value)

        self._set.append(
            type('dgraphPushData', (object,), {"type": vtype, "data": _set, "additional": {"root": self.meta.root, "model":self.modelName, "uid":uid}}))
        return self

    @classmethod
    def set(cls, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        self.__init__()
        resp = self._push("set", *args, **kwargs)
        return resp

    @classmethod
    def delete(cls, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        self.__init__()
        resp = self._push("delete", *args, **kwargs)
        return resp
    
    @classmethod
    def uid(cls, uid):
        self = cls.__new__(cls, *args, **kwargs)
        self.__init__()
        self._uid = uid
        return self
        
    ##################
    #dgraphModel.pull#
    ##################
    def _pull(self, vtype, start, *args, **kwargs):
        self.__init__()
        if not hasattr(self, "_set"):
            self._set = []

        if hasattr(self.meta, "staticID"):
            start = dgraphFlags.init(start.name, id=self.meta.staticID)
        
        _getall = ('*' in args)
        _set = []
        for name in dir(self):
            if name in kwargs:
                callableM = getattr(self, name)
                flags = kwargs[name]
                _set.append(
                    callableM.queryValue(flags._name(name), flags, vtype))
            elif name in args:
                callableM = getattr(self, name)
                _set.append(
                    callableM.queryValue(self._name(name), None, vtype))
            elif _getall == True and getattr(self, name).__class__.__bases__[0].__name__ == "dgraphTypes":
                callableM = getattr(self, name)
                _set.append(
                    callableM.queryValue(self._name(name), None, vtype))
                    
        self._set.append(
            type('dgraphPullData', (object,), {"type": vtype, "data": _set, "start": start, "additional": {"model":self.modelName, "root": self.meta.root}}))
        return self

    @classmethod
    def query(cls, responceStart, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        return self._pull("query", responceStart, *args, **kwargs)

    @classmethod
    def recurse(cls, iterStart, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        return self._pull("recurse", iterStart, *args, **kwargs)

    @classmethod
    def var(self, varStart, *args, **kwargs):
        self = cls.__new__(cls, *args, **kwargs)
        return self._pull("var", varStart, *args, **kwargs)

    def generate(self, alternativeSet=None):
        _set = alternativeSet or self._set
        _itSet = []
        _flagParms = ["index", "reverse", "schema"]

        _getSection = '''{0}({1}){{
            {2}
        }}'''

        _getBasic = '''
                {
                    %s
                }
        '''

        _setBasicnSchema = '''
            mutation {
                schema {
                    %s .
                }

                %s{
                    %s .
                }
            }
        '''

        _setBasic = '''
            mutation {
                %s{
                    %s .
                }
            }
        '''

        # List generation
        for s in _set:
            stype = s.type
            data = s.data

            if stype in self.pushTypes:
                for d in data:
                    d.prefix = self.modelName + "_"
                    _itSet.append((stype, *d.gen))
            elif stype in self.pullTypes:
                _inner = []
                s.start._prefix = self.modelName + "_"
                sflags = s.start.flags
                if stype == "recurse":
                    sname = "recurse"
                else:
                    sname = s.start.name

                for d in data:
                    d.prefix = self.modelName + "_"
                    _inner.append(d.gen)
                _itSet.append(
                    (stype, _getSection.format(sname, sflags, "\n".join(_inner)), None))

            if s.additional["root"] != None:
                if s.__name__ == "dgraphPullData":
                    pass
                elif s.__name__ == "dgraphPushData":
                    _rootParts = reversed(s.additional["root"].split("."))
                    _link = self
                    for idx, _p in enumerate(_rootParts):
                        _sp = _p.split(":")
                        if _sp[0] == "<*>":
                            _uid = "_:{0}".format(get_random_string())
                            _link = dgraphUID().setValue(
                                _uid, _sp[1], _link, stype)
                        else:
                            _link = dgraphUID().setValue(
                                "<{0}>".format(_sp[0]), _sp[1], _link, stype)

                        _itSet.append((stype, *_link.gen))

        _itSet.append((None, None, None))

        _set = []
        _schema = []
        _last = _itSet[0][0]
        _generator = ""

        # List to Output
        for idx, (t, s, sc) in enumerate(_itSet):
            if t != _last:

                # Set
                if _last in ("set", "delete"):
                    if len(_schema) > 0 and not self.disableSchema == True:
                        _generator += dedent(_setBasicnSchema %
                                             (" .\n".join(_schema), _last, " .\n".join(_set)))
                    else:
                        _generator += dedent(_setBasic %
                                             (_last, " .\n".join(_set)))

                # Query
                elif _last in ("query", "recurse"):
                    _generator += dedent(_getBasic % ("\n".join(_set)))
                if sc != None:
                    _schema = [sc]
                else:
                    _schema = []

                _set = [s]
                _last = t

            else:
                if sc != None:
                    _schema.append(sc)
                _set.append(s)

        return _generator

    def join(self, *args):
        _self = copy.copy(self)
        _set = copy.copy(_self._set)

        for a in args:
            _set += a._set
        _self._set = _set

        return _self

    def __str__(self):
        return self.generate()

    def __unicode__(self):
        return self.__str__()
        
#UniqueIDGenerator
class idGen():
    def __init__(self, prefix, idlength = 8):
        self.secret = SECRET_KEY
        self.idlength = idlength
        self.prefix = str(prefix)
        self.allowed_chars='abcdefghijklmnopqrstuvwxyz''ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    def __call__(self, uniquifier):
        if not isinstance(uniquifier, list):
            uniquifier = [uniquifier]
        return self.transform(self.prefix, uniquifier)

    def transform(self, prefix, ident):
            sha256key = [i for i in hashlib.sha256('{0}_{1}{2}'.format(prefix, ".".join([str(i) for i in ident]), self.secret).encode('utf-8')).hexdigest() if i in self.allowed_chars]
            sha256prefix = [i for i in hashlib.sha256('{0}_{1}'.format(prefix, self.secret).encode('utf-8')).hexdigest() if i in self.allowed_chars]
            return '{0}.{1}'.format("".join(sha256prefix[:4]), "".join(sha256key[:self.idlength]))
        
