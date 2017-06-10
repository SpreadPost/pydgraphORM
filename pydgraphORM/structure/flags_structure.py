#from .flags_structure import dgraphFlags
class dgraphFlags():
	@classmethod
	def query(cls, *args, **kwargs):
		self = dgraphQueryFlags(*args, **kwargs)
		return self

	@classmethod
	def init(cls, *args, **kwargs):
		self = dgraphInitFlags(*args, **kwargs)
		return self

#ClassQueries
class dgraphQueryFlags():
	def __init__(self, *args, **kwargs):
		self._validLng = ["da","nl","en","fi","fr","de","hu","it","no","pt","ro","ru","es","sv","tr"]
		self._flags = type('flags', (object,), {"method":None, "flags":[]})
		self._prefix = ""
		self._sub = []
		self._alias = None
		self._reverse = False
		self._language = None

		validFlags = ("first", "offset", "after", "id", "orderasc", "orderdesc")
		for k, v in kwargs.items():
			if k in validFlags:
				self._flags.flags.append("{0}: {1}".format(str(k),str(v)))

	#Search
	###GeneralQuery###
	##################
	def _var(self, value):
		if value.__class__.__bases__[0].__name__ == "dgraphTypes":
			varName = value.setVar().varName 
			return 'var({0})'.format(varName)
		else:
			return value

	def anyofterms(self, name, values):
		self._flags.method = ('anyofterms', name, ",".join(['"{0}"'.format(str(self._var(v))) for v in values]))
		return self

	def allofterms(self, name, values):
		self._flags.method = ('allofterms', name, ",".join(['"{0}"'.format(str(self._var(v))) for v in values]))
		return self
	
	def regexp(self, name, value):
		self._flags.method = 'regexp({0}, {1})'.format(str(name), str(self._var(value)))
		return self

	#Numeric
	def greaterThan(self, name, value):
		self._flags.method = 'ge({0}, {1})'.format(str(name), str(self._var(value)))
		return self

	def lowerThan(self, name, value):
		self._flags.method = 'le({0}, {1})'.format(str(name), str(self._var(value)))
		return self

	#Alias
	def alias(self, alias):
		self._alias = alias
		return self

	def reverse(self):
		self._reverse = True
		return self

	def language(self, lang):
		if lang in self._validLng:
			self._language = str(lang)
		return self

	#UID Child
	def child(self, childModel, *args, **kwargs):
		_set = []
		for name in dir(childModel):
			if name in kwargs:
				callableM = getattr(childModel, name)
				_set.append(callableM.queryValue(name, kwargs[name]))
			elif name in args:
				callableM = getattr(childModel, name)
				_set.append(callableM.queryValue(name, None))
				
		self._sub = _set
		return self

	#FlagModify
	def _name(self, name):
		if self._reverse == True:
			name = '~{0}'.format(name)
		if self._language != None:
			name = '{0}@{1}'.format(name, self._language)
		if self._alias == None:
			return name
		else:
			return "{0}:{1}".format(self._alias, name)

	@property
	def flags(self):
		if self._flags.method == None:
			return "({0}) ".format(", ".join(self._flags.flags))
		else:
			method = '{0}({1}, [{2}])'.format(self._flags.method[0], "{0}{1}".format(self._prefix , self._flags.method[1]), self._flags.method[2])
			return "({0}) @filter({1})".format(", ".join(self._flags.flags), method)
	
	@property
	def sub(self):
		return self._sub
    
#ClassInit
class dgraphInitFlags(dgraphQueryFlags):
	###Start###
	###########
	def __init__(self, name, *args, **kwargs):
		self.name = name
		id = None
		if "id" in kwargs:
			id = kwargs["id"]
			del kwargs["id"]
			
		super().__init__(*args, **kwargs)
		self.id(id)
		

    #StartID
	def id(self, id):
		self._flags.id = id 
		return self
	
	#Geolocation
	def near(self, name, position, distance):
		self._flags.method = 'near({0}, {1}, {2})'.format(str(name), str(position), str(distance)) 
		return self

	def within(self, name, entities):
		self._flags.method = 'within({0}, {1})'.format(str(name), str(entities)) 

	def contains(self, name, position):
		self._flags.method = 'contains({0}, {1})'.format(str(name), str(position))

	def intersects(self, name, entities):
		self._flags.method = 'intersects({0}, {1})'.format(str(name), str(entities)) 

	@property
	def flags(self):
		if self._flags.method == None and self._flags.id != None:
			if len(self._flags.flags) > 0:
				return "id:{1}, {0}".format(", ".join(self._flags.flags), self._var(self._flags.id))
			else:
				return "id:{0}".format(self._var(self._flags.id))
		elif self._flags.method != None:
			method = '{0}({1}, [{2}])'.format(self._flags.method[0], "{0}{1}".format(self._prefix , self._flags.method[1]), self._flags.method[2])
			if len(self._flags.flags) > 0:
				return "func:{1}, {0}".format(", ".join(self._flags.flags), method)
			else:
				return "func:{0}".format(method)
		else:
			raise "No start id or methode specified"