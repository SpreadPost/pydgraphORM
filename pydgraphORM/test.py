from pydgraphORM.flags_structure import dgraphFlags
from pydgraphORM.model_structure import dgraphModel, dgraphTypes, dgraphUID, dgraphID, dgraphString, dgraphInt, dgraphFloat, dgraphBool, dgraphGeo, dgraphDate, idGen
from pydgraphORM.client_structure import structRequest, staticClient, assembly


#Init Models

class dgraphStatic(dgraphModel):
    id = dgraphInt(require=True, default=0)
    name = dgraphString(require=True, default="")
    option = dgraphString(require=True, default="")

    def __meta__(self):
        self.meta.root = 'test:dgraphStatic'
        self.meta.staticID = "staticTest"


class dgraphDynamic(dgraphModel):
    id = dgraphInt(require=True, default=0)
    name = dgraphString(require=True, default="")
    option = dgraphString(require=True, default="")

    def __meta__(self):
        self.meta.root = 'test:dgraphDynamic'


#Init Connector & Assembly
asm = assembly()
asm.setStdClient(staticClient('192.168.2.100', 8080))


def _remStatic(values):
    return dgraphStatic.delete(**values)

async def remStatic(values):
    return await asm.asyn.assemble(_remStatic(values)) 

def _modStatic(values):
    return dgraphStatic.set(**values)

async def modStatic(values):
    return await asm.asyn.assemble(_modStatic(values)) 

def _getStatic(id=None):
    if id != None:
        return dgraphStatic.query(dgraphFlags.init("static", id=id), "*")
    else:
        return dgraphStatic.query(dgraphFlags.init("static"), "*")

async def getStatic(id=None):
    return await asm.asyn.assemble(_getStatic(id))


def _remDynamic(values):
    return dgraphDynamic.delete(**values)

async def remDynamic(values):
    return await asm.asyn.assemble(_remDynamic(values)) 

def _modDynamic(values):
    return dgraphDynamic.set(**values)

async def modDynamic(values):
    return await asm.asyn.assemble(_modDynamic(values)) 

def _getDynamic(id=None):
    if id != None:
        return dgraphDynamic.query(dgraphFlags.init("dynamic", id=id), "*")
    else:
        return dgraphDynamic.query(dgraphFlags.init("dynamic"), "*")

async def getDynamic(id=None):
    return await asm.asyn.assemble(_getDynamic(id))





if __name__ == "__main__":
    #Sync
    print("Synchronious")

    #In static
    print("\nStatic")
    #Set entry and get pull from db afterwards
    resp = asm.assemble(_modStatic({"id": 2, "name": "foo", "option": "bar"}), _getStatic())
    staticIn = resp[0]
    staticOut = resp[1]
    #Print uid and db entry
    print(str(staticIn.mappings.dgraphStatic))
    print("id:{0}, name:{1}, option:{2}".format(staticOut.data.dgraphStatic.static.id, staticOut.data.dgraphStatic.static.name, staticOut.data.dgraphStatic.static.option))
    #Remove entry
    resp = asm.assemble(_remStatic({"id":None, "name":None, "option":None}), _getStatic())
    staticIn = resp[0]
    staticOut = resp[1]
    #Print removed entry uid
    print(str(staticIn.mappings.dgraphStatic))

    resp = asm.assemble(_modStatic({"id": 2, "name": "foo", "option": "bar"}), _getStatic())

    #Now into dynamic
    print("\nDynamic")
    #Set entry
    resp = asm.assemble(_modDynamic({"id": 2, "name": "foo", "option": "bar"}))
    #Get UID
    dynamicIn = resp[0]
    uid = dynamicIn.mappings.dgraphDynamic
    print(uid)
    #Get entry
    resp = asm.assemble(_getDynamic(uid))
    dynamicOut = resp[0]
    print("id:{0}, name:{1}, option:{2}".format(dynamicOut.data.dgraphDynamic.dynamic.id, dynamicOut.data.dgraphDynamic.dynamic.name, dynamicOut.data.dgraphDynamic.dynamic.option))
    #Remove entry
    resp = asm.assemble(_remDynamic({"uid": uid, "id":None, "name":None, "option":None}))
    #Get old UID
    dynamicIn = resp[0]
    print(str(dynamicIn.mappings.dgraphDynamic))


    #Async
    print("\nAsynchronious")
    try:
        import asyncio
    except:
        raise BaseException("Sorry, asnycio library not existing")
    
    #Init loop
    loop = asyncio.get_event_loop()
    loops = []

    #Set static and dynamic async parallel
    loops.append(modStatic({"id": 3, "name": "foo", "option": "bar"}))
    loops.append(modDynamic({"id": 3, "name": "foo", "option": "bar"}))
    
    #Get results
    resp = loop.run_until_complete(asyncio.gather(*loops))
    staticIn = resp[0][0]
    dynamicIn = resp[1][0]

    #Print results
    print(str(staticIn.mappings.dgraphStatic))
    print(str(dynamicIn.mappings.dgraphDynamic))
    
    #Query static and dynamic async parallel
    loops = []
    loops.append(getStatic())
    uid = dynamicIn.mappings.dgraphDynamic
    loops.append(getDynamic(uid))
    
    #Get results
    resp = loop.run_until_complete(asyncio.gather(*loops))
    staticOut= resp[0][0]
    dynamicOut= resp[1][0]

    print("id:{0}, name:{1}, option:{2}".format(staticOut.data.dgraphStatic.static.id, staticOut.data.dgraphStatic.static.name, staticOut.data.dgraphStatic.static.option))
    print("id:{0}, name:{1}, option:{2}".format(dynamicOut.data.dgraphDynamic.dynamic.id, dynamicOut.data.dgraphDynamic.dynamic.name, dynamicOut.data.dgraphDynamic.dynamic.option))
    
    #Query static and dynamic async parallel
    loops = []
    loops.append(remStatic({"id":None, "name":None, "option":None}))
    loops.append(remDynamic({"uid": uid, "id":None, "name":None, "option":None}))
    
    #Get results
    resp = loop.run_until_complete(asyncio.gather(*loops))
    staticIn = resp[0][0]
    dynamicIn = resp[1][0]
    
    #Print results
    print(str(staticIn.mappings.dgraphStatic))
    print(str(dynamicIn.mappings.dgraphDynamic))
    
    loop.close()