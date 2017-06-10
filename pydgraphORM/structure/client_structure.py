from pydgraph.client import DgraphClient

#Stable client initialization
class staticClient():
        def __init__(self, ip, port):
                print("InitClient")
                self.dg_client = DgraphClient(ip, port)

        def client(self):
                return self.dg_client

        def query(self, cmd):
                return self.dg_client.query(cmd)

        async def aQuery(self, cmd):
                return await self.dg_client.aQuery(cmd)

stdStaticClient = None

#Structure request class
class structRequest():
        def __init__(self, client=stdStaticClient):
                if client == None:
                        stdStaticClient  = staticClient('127.0.0.1', 8080)
                self.client = client

                schema = self.schema()
                if schema != None:
                        client.client().query(schema)

        async def  __aenter__(self, client=stdStaticClient):
                self.client = client
                return await self.aQuery(self.schema)

        async def __aexit__(self):
                pass

        def schema(self):
                return None

        #Query
        async def _queryAsync(self, resp):
                return await self.client.aQuery(str(resp))

        def _query(self, resp):
                return self.client.query(str(resp))

class assembly():
        def __init__(self):
                self.structReq = structRequest()
                self.inDecode = self._inDecode()
                self.asyn = type("asyn", (object,), {"assemble": self._asyncAssemble})

        def setStdClient(self, client):
                self.structReq.client = client

        class objectview(object):
                def __init__(self, d):
                        for k,v in d.items():
                                if isinstance(v, dict):
                                        d[k] = self.__class__(v)
                                if isinstance(v, list):
                                        d[k] = [self.__class__(l) if hasattr(l, 'iteritems') else l for l in v ]
                        self.__dict__ = d
                def __iter__(self):
                        for attr, value in self.__dict__.items():
                                yield attr
                def __getitem__(self, idx):
                        return getattr(self,idx)

        class _inDecode():

                def value(self, obj):
                        val = list(obj.value._fields.values())
                        if len(val) == 1:
                                val = val[0]
                        elif len(val) == 0:
                                val = None
                        return (self.regulateName(obj.prop), val)

                def properties(self, obj):
                        return (self.regulateName(obj.attribute), obj.properties._values)

                def children(self, obj):
                        return (obj.attribute, obj.children._values)

                def values(self, obj):
                        return obj.n._values

                def regulateName(self, name):
                        split = name.split("_", 1)
                        if len(split) > 1:
                                return name.split("_", 1)[1]
                        else:
                                return name

                def leafIter(self, obj):
                        if hasattr(obj, "value"):
                                return self.value(obj)

                        resp = {}
                        name, childs = self.children(obj)
                        if len(childs) > 0:
                                for c in childs:
                                        n, val = self.leafIter(c)
                                        resp[n] = val
                                return name, resp

                        name, props = self.properties(obj)
                        if len(props) > 0:
                                for p in props:
                                        n, val = self.leafIter(p)
                                        resp[n] = val
                                return name, resp
                        return None, None
                def __call__(self, data):
                        resp = {}

                        for i, v in enumerate(self.values(data)):
                                name, d = self.leafIter(v)
                                if d != None:
                                        resp[i] = d
                        return resp

        def decode(self, responce, obj):
                stats = {
                        "performance":{
                                "parsing": responce.l.parsing,
                                "pb": responce.l.pb,
                                "processing": responce.l.processing
                        }
                }

                inp = {}
                if responce.AssignedUids.values()._mapping._values != {}:
                        d = responce.AssignedUids.values()._mapping._values
                else:
                        d = {}

                for s in obj._set:
                        if s.__name__ == "dgraphPushData" and [s.additional["uid"][0], s.additional["uid"][-1]] == ["<", ">"]:
                                if s.additional["model"] not in d:   
                                        d[s.additional["model"]] = s.additional["uid"]
                                else:
                                        if not isinstance(d[s.additional["model"]], list):
                                                d[s.additional["model"]] = [d[s.additional["model"]], s.additional["uid"]]
                                        else:
                                                d[s.additional["model"]].append(s.additional["uid"])
                        
                        elif s.__name__ == "dgraphPushData" and s.additional["uid"][0:2] == '_:':
                                for attr, value in list(d.items()):
                                        if s.additional["uid"] == '_:' + attr:
                                                if s.additional["model"] not in d:   
                                                        d[s.additional["model"]] = value
                                                else:
                                                        if not isinstance(d[s.additional["model"]], list):
                                                                d[s.additional["model"]] = [d[s.additional["model"]], value]
                                                        else:
                                                                d[s.additional["model"]].append(value)
                                                del d[attr]

                if d != {}:
                        inp = dict(inp, **{"mappings":d})

                if len(responce.n) > 0:
                        d = self.inDecode(responce)
                        setnames = [s.additional["model"] for s in obj._set if s.__name__ == "dgraphPullData"]
                        l = len(setnames)

                        for idx, (attr, value) in enumerate(list(d.items())):
                                if l > idx:
                                        if setnames[idx] not in d:
                                                d[setnames[idx]] = value
                                                del d[attr]
                                        else:
                                                if not isinstance(d[setnames[idx]], list):
                                                        d[setnames[idx]] = [d[setnames[idx]], value]
                                                else:
                                                        d[setnames[idx]].append(value)
                                                del d[attr]

                        inp = dict(inp, **{"data": d})

                return self.objectview(dict({"statistics": stats}, **inp))

        async def _asyncAssemble(self, *args, **kwargs):
                re = {}

                for i, a in enumerate(args):
                        if type(a) is list or type(a) is tuple:
                                ac = a[0].join(*a[1:])
                                re[i] = (ac, await self.structReq._queryAsync(ac.generate()))
                        else:
                                re[i] = (a, await self.structReq._queryAsync(a))

                for i, a in kwargs.items():
                        re[i] = (a, await self.structReq._queryAsync(a))

                for i, (a, r) in re.items():
                        re[i] = self.decode(r, a)

                return re

        def assemble(self, *args, **kwargs):
                re = {}

                for i, a in enumerate(args):
                        if type(a) is list or type(a) is tuple:
                                ac = a[0].join(*a[1:])
                                re[i] = (ac, self.structReq._query(ac.generate()))
                        else:
                                re[i] = (a, self.structReq._query(a))

                for i, a in kwargs.items():
                        re[i] = (a, self.structReq._queryAsync(a))

                for i, (a, r) in re.items():
                        re[i] = self.decode(r, a)

                return re