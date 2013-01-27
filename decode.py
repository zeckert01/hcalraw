#For AMC13, see http://ohm.bu.edu/~hazen/CMS/SLHC/HcalUpgradeDataFormat_v1_2_2.pdf
#For DCC2, see http://cmsdoc.cern.ch/cms/HCAL/document/CountingHouse/DCC/FormatGuide.pdf

def bcn(raw, delta = 0) :
    if not delta : return raw
    out = raw + delta
    if out<0    : out += 3564
    if out>3563 : out -= 3564
    return out

def trailer(d = {}, iWord64 = None, word64 = None, bcnDelta = 0) :
    d["TTS"] = (word64>>4)&0xf
    d["CRC16"] = (word64>>16)&0xffff
    d["nWord64"] = (word64>>32)&0xffffff

def htrDict(w) :
    return {"nWord16":w&0x3ff,
            "E":(w>>15)&1,
            "P":(w>>14)&1,
            "C":(w>>10)&1,
            "V":not ((w>>12)&1 or (w>>13)&1),
            }

def uHtrDict(w) :
    return {"nWord16":w&0xfff,
            "E":(w>>15)&1,
            "P":(w>>14)&1,
            "V":(w>>13)&1,
            "C":(w>>12)&1,
            }

def header(d = {}, iWord64 = None, word64 = None, utca = None, bcnDelta = 0) :
    w = word64
    if iWord64==0 :
        d["FEDid"] = (w>>8)&0xfff
        d["BcN"] = (w>>20)&0xfff
        d["EvN"] = (w>>32)&0xffffff
        d["BcN"] = bcn(d["BcN"], bcnDelta)
    if iWord64==1 :
        d["OrN"] = (w>>4)&0xffffffff

    if utca :
        if 3<=iWord64<=5 :
            uhtr0 = 4*(iWord64-3)
            for i in range(4) :
                d["uHTR%d"%(uhtr0+i)] = uHtrDict((w>>(16*i))&0xffff)
    else :
        if 3<=iWord64<=10 :
            j = (iWord64-3)*2
            d["HTR%d"%j] = htrDict(w)
            if iWord64!=10 :
                d["HTR%d"%(j+1)] = htrDict(w>>32)

def payload(d = {}, iWord16 = None, word16 = None, bcnDelta = 0) :
#https://cms-docdb.cern.ch/cgi-bin/PublicDocDB/RetrieveFile?docid=3327&version=14&filename=HTR_MainFPGA.pdf
    w = word16
    if "iWordZero" not in d :
        d["iWordZero"] = iWord16
        d[d["iWordZero"]] = {}

    l = d[d["iWordZero"]]
    i = iWord16 - d["iWordZero"]
    l["iWordQie0"] = 8

    #header
    if i==0 :
        l["InputID"] = (w&0xf0)/(1<<8)
        l["EvN"] = w&0xf
    if i==1 :
        l["EvN"] += w*(1<<8)
    if i==3 :
        l["ModuleId"] = w&0x7ff
        l["OrN5"] = (w&0xf800)>>11
    if i==4 :
        l["BcN"] = bcn(w&0xfff, bcnDelta)
        l["FormatVer"] = (w&0xf000)>>12
    if i==5 :
        l["nWord16"] = 228 #fixme
        l["nWord16Tp"] = (w&0xfc)>>3
        l["nPreSamples"] = (w&0xfc)>>3
        l["channelData"] = {}
    if i<l["iWordQie0"] :
        return

    #trailer
    if i==l["nWord16"]-4 :
        l["nWord16Qie"] = w&0x7ff
        l["nSamples"] = (w&0xfc00)>>11
        return
    if i==l["nWord16"]-3 :
        l["CRC"] = w
        return
    elif i==l["nWord16"]-1 :
        del d["iWordZero"]
        del d["currentChannelId"]
        l["EvN8"] = w>>8
        l["DTCErrors"] = w&0xff
        return

    #data
    if w&(1<<15) :
        d["currentChannelId"] = w&0xff
        l["channelData"][d["currentChannelId"]] = {"CapId0":(w&0x300)>>8,
                                                   "ErrF":(w&0xc00)>>10,
                                                   "Flavor":(w&0x7000)>>12,
                                                   "iWord16":iWord16,
                                                   "QIE":{},
                                                   }
    else :
        if "currentChannelId" not in d : return
        dct = l["channelData"][d["currentChannelId"]]
        j = iWord16 - dct["iWord16"] - 1
        dct["QIE"][2*j  ] = word16&0xff
        dct["QIE"][2*j+1] = (word16&(0xff<<8))>>8