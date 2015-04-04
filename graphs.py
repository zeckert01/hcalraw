import math
import collections
import printer
import utils
r = utils.ROOT()


def combineBinContentAndError(histo, binToContainCombo, binToBeKilled):
    xflows     = histo.GetBinContent(binToBeKilled)
    xflowError = histo.GetBinError(binToBeKilled)

    if xflows == 0.0:  # ugly
        return

    currentContent = histo.GetBinContent(binToContainCombo)
    currentError   = histo.GetBinError(binToContainCombo)

    histo.SetBinContent(binToBeKilled, 0.0)
    histo.SetBinContent(binToContainCombo, currentContent+xflows)

    histo.SetBinError(binToBeKilled, 0.0)
    histo.SetBinError(binToContainCombo, math.sqrt(xflowError**2+currentError**2))


def shiftFlows(histo=None):
    bins = histo.GetNbinsX()
    entries = histo.GetEntries()
    combineBinContentAndError(histo, binToContainCombo=1   , binToBeKilled=0     )
    combineBinContentAndError(histo, binToContainCombo=bins, binToBeKilled=bins+1)
    histo.SetEntries(entries)


def labelYAxis(h=None, labels={}):
    h.SetStats(False)
    yaxis = h.GetYaxis()
    for iBin, label in sorted(labels.iteritems()):
        yaxis.SetBinLabel(iBin, label)
    yaxis.SetLabelSize(2.0 * 0.035)


def xMin_xMax(graph=None):
    """assumes that graph is sorted"""
    N = graph.GetN()
    X = graph.GetX()
    if 1 <= N:
        return X[0], X[N-1]
    else:
        printer.error("graph contains zero points.")
        return 0.0, 0.0


def multiY(graph=None):
    s = set()
    y = graph.GetY()
    for i in range(graph.GetN()):
        s.add(y[i])
    return 2 <= len(s)


def fillRateHisto(h, g):
    n = g.GetN()
    x = g.GetX()
    y = g.GetY()

    # make histo coarser if needed
    if 10 <= n:
        while n < 2 * h.GetNbinsX():
            h.Rebin(2)

    evn = collections.defaultdict(list)
    for i in range(n):
        iBin = h.FindBin(x[i])
        evn[iBin].append(y[i])

    for iBin, lst in evn.iteritems():
        nL1A = 1 + max(lst) - min(lst)
        deltaT = h.GetBinWidth(iBin)  # minutes
        deltaT *= 60.0  # seconds
        c = nL1A / deltaT
        h.SetBinContent(iBin, c)

        relErr = 1.0 / len(lst)  # +- 1 events
        h.SetBinError(iBin, c * relErr)


def magnify(h, factor=1.0):
    h.GetYaxis().SetTitleOffset(1.2)
    h.GetZaxis().SetTitleOffset(1.2)

    default = 0.035
    for axis in [h.GetXaxis(), h.GetYaxis(), h.GetZaxis()][:2]:
        axis.SetLabelSize(factor * default)
        axis.SetTitleSize(factor * default)



def adjustPad(pad=r.gPad, logX=False, logY=False, logZ=False,
              m={"Left": 0.15, "Bottom": 0.15, "Right": 0.15, "Top": None}):

    for key, value in m.iteritems():
        if value is None:
            continue
        getattr(r.gPad, "Set%sMargin" % key)(value)

    r.gPad.SetTickx()
    r.gPad.SetTicky()
    if logX:
        r.gPad.SetLogx()
    if logY:
        r.gPad.SetLogy()
    if logZ:
        r.gPad.SetLogz()


def stylize(h, color=r.kBlack, style=1, width=1):
    #r.gStyle.SetOptStat(110010)
    h.SetStats(False)
    h.SetMinimum(0.5)
    h.SetLineColor(color)
    h.SetLineStyle(style)
    h.SetLineWidth(width)


def legends(legEntries=[], twoLines=False):
    out = []
    dx = 0.8 / max(1, len(legEntries))
    dx *= 2 if twoLines else 1
    if twoLines:
        max1 = len(legEntries)/2
        y = 0.95
    else:
        max1 = len(legEntries)
        y = 0.91

    x0 = 0.1
    for iLeg in range(max1):
        h, desc = legEntries[iLeg]
        leg = r.TLegend(x0, y, x0+dx, 1.0)
        x0 += dx
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(h, desc, "l")
        leg.Draw()
        out.append(leg)

    x0 = 0.1
    for iLeg in range(max1, len(legEntries)):
        h, desc = legEntries[iLeg]
        leg2 = r.TLegend(x0, 0.90, x0+dx, y)
        x0 += dx
        leg2.SetBorderSize(0)
        leg2.SetFillStyle(0)
        leg2.AddEntry(h, desc, "l")
        leg2.Draw()
        out.append(leg2)

    return out


def justOne(s):
    fields = s.split("_")
    return 2 <= len(fields) and fields[0] == "BcN" and fields[1] != "HTRs"


def histoLoop(f, lst, func):
    out = []
    maxes = []
    legEntries = []
    h0 = None

    didOne = False
    twoLines = False
    for x, color, style in lst:
        h = f.Get(func(x))
        if not h:
            continue

        if not h.GetEntries():
            continue

        if justOne(func(x)):
            if didOne:
                continue
            didOne = True

        gopts = "hist"
        if h0:
            gopts += "same"
        else:
            h0 = h
        maxes.append(h.GetMaximum())
        shiftFlows(h)
        h.Draw(gopts)
        stylize(h, color, style)
        magnify(h, factor=1.8)
        if not h.GetXaxis().GetTitle():
            h.GetXaxis().SetLabelSize(0.13)
        out.append(h)

        s = "Matched"
        if func(x).startswith(s):
            twoLines = True
            ch = func(x).replace(s, "").replace("Fibers", "").replace("TriggerTowers", "")
            if not ch:
                ch = "TP  "
            t = "%s  %d#pm%d" % (ch, h.GetMean(), h.GetRMS())
            h.GetXaxis().SetTitle("no. matched")
        else:
            t = h.GetTitle().replace("FED ", "")

        if justOne(func(x)):
            t += "   (%d entries)" % h.GetEntries()

        legEntries.append((h, t))
        h.SetTitle("")

    if maxes and h0:
        h0.SetMaximum(2.0*max(maxes))
    out += legends(legEntries, twoLines=twoLines)
    return out


def fedString(lst=[]):
    return ",".join(["%d" % i for i in lst])


def plotGlobal(f, pad, offset=None, names=[], logY=False, logX=False, logZ=True, gopts="colz", feds1=[], feds2=[]):
    keep = []

    for iHisto, name in enumerate(names):
        if not name:
            continue
        pad.cd(offset + iHisto)
        adjustPad(logX=logX, logY=logY, logZ=logZ)
        h = f.Get(name)
        if not h:
            continue

        shiftFlows(h)
        h.Draw(gopts)
        stylize(h)
        magnify(h, factor=1.8)

        P = name[:name.find("_vs_")].upper()
        h.GetXaxis().SetTitle("%s (%s)" % (P, fedString(feds1)))
        h.GetYaxis().SetTitle("%s (%s)" % (P, fedString(feds2)))
        h.GetZaxis().SetTitle("samples / bin")

        if h.GetTitle():
            h.GetXaxis().SetTitle(h.GetXaxis().GetTitle().replace(")", ": %s)" % h.GetTitle()))
            if h.GetTitle().startswith("SOI"):
                h.GetYaxis().SetTitle(h.GetYaxis().GetTitle().replace(")", ": SOI)"))

        h.SetTitle("")

        xMin = h.GetXaxis().GetXmin()
        xMax = h.GetXaxis().GetXmax()

        line = r.TLine()
        line.SetLineWidth(1)
        line.SetLineStyle(2)
        x0 = line.DrawLine(0.0, xMin, 0.0, xMax)
        y0 = line.DrawLine(xMin, 0.0, xMax, 0.0)

        h.Draw(gopts + "same")  # draw again to be on top of dashed lines

        yx = r.TF1("yx", "x", xMin, xMax)
        yx.SetLineColor(r.kBlack)
        yx.SetLineWidth(1)
        yx.SetLineStyle(3)
        yx.Draw("same")

        leg = r.TLegend(0.25, 0.75, 0.55, 0.88)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.AddEntry(yx, "y = x", "l")
        leg.AddEntry(x0, "zero", "l")
        leg.Draw()
        keep += [h, yx, x0, y0, leg]
    return keep


def plotList(f, pad, offset=None, names=[], logY=True, logX=False, logZ=False, gopts="hist", feds1=[], feds2=[]):
    fedList = (feds1 + feds2)[:5]
    color = [r.kBlack, r.kRed, r.kBlue, r.kGreen, r.kMagenta]
    color += [r.kBlack] * (len(fedList) - len(color))
    style = [1, 2, 3, 4, 5]
    style += [1] * (len(fedList) - len(style))

    keep = []
    for iHisto, name in enumerate(names):
        if not name:
            continue
        pad.cd(offset + iHisto)
        adjustPad(logX=logX, logY=logY, logZ=logZ)

        feds = []
        for iFed, fed in enumerate(sorted(fedList)):
            feds.append((fed, color[iFed], style[iFed]))

        keep += histoLoop(f, feds, lambda x: "%s_%d" % (name, x))
    return keep


def draw_graph(graph, title="", rate=False):
    if not graph:
        return

    padg = r.TPad("padg", "padg", 0.00, 0.75, 0.80, 1.00)
    padg.Draw()
    keep = [padg]

    if rate:
        split = 0.3
        padg.Divide(1, 2)
        padg.cd(1).SetPad(0.01, split, 0.99, 0.99 )
        padg.cd(2).SetPad(0.01, 0.01 , 0.99, split)

    graph.SetMarkerStyle(20)
    graph.SetMarkerColor(r.gStyle.GetHistLineColor())
    graph.SetMarkerSize(0.5*graph.GetMarkerSize())
    t = graph.GetTitle().split("_")

    xMin, xMax = xMin_xMax(graph)
    delta = xMax - xMin
    if delta:
        tenPercent = 0.1 * delta
    else:
        tenPercent = 0.1/60.0  # 1/10 second

    null = r.TH2D("null", ";time (minutes);",
                  60, xMin - tenPercent, xMax + tenPercent,
                  3, 0.5, 3.5)

    if rate:
        h = null.ProjectionX()
        fillRateHisto(h, graph)
        h.SetStats(False)
        h.SetMarkerStyle(20)
        h.SetMarkerSize(0.5)
        y = 10.0

        padg.cd(1)
        adjustPad(m={"Bottom": 0.0, "Left": 0.1, "Top": 0.03, "Right": 0.03})
        r.gPad.SetLogy(True)
        r.gPad.SetGridy()
        hu = h.DrawClone("pe")
        hu.GetYaxis().SetTitle("L1A rate (Hz)")
        hu.GetXaxis().SetLabelSize(0.0)
        hu.GetXaxis().SetTickLength(0.0)
        hu.SetMinimum(y)
        hu.SetMaximum(2.0e5)
        keep.append(hu)
        magnify(hu, factor=3.0)
        hu.GetYaxis().SetTitleSize(0.15)
        hu.GetYaxis().SetTitleOffset(0.18)
        hu.GetYaxis().SetLabelOffset(0.001)

        padg.cd(2)
        adjustPad(m={"Bottom": 0.5, "Left": 0.1, "Top": 0.0, "Right": 0.03})
        r.gPad.SetLogy(False)
        r.gPad.SetTickx(0)
        hl = h.DrawClone("pe")
        hl.SetMinimum(0.0)
        hl.SetMaximum(y)
        keep.append(hl)
        magnify(hl, factor=9.0)
        hl.GetXaxis().SetTickLength(0.1)
        hl.GetXaxis().SetTitleOffset(0.7)

        hl.GetYaxis().SetTickLength(hu.GetYaxis().GetTickLength())
        hl.GetYaxis().SetLabelSize(0.25)
        hl.GetYaxis().SetNdivisions(402, True)
    else:
        padg.Draw()
        padg.cd()

        adjustPad(m={"Bottom": 0.2, "Left": 0.15, "Top": 0.03, "Right": 0.03})
        null.Draw()
        magnify(null, factor=3.0)
        labelYAxis(null, labels={1: t[0], 2: t[1], 3: t[2]})
        graph.Draw("psame")
        keep += [null, graph]
        null.GetXaxis().SetTitleOffset(0.75)
        null.GetYaxis().SetLabelSize(0.1)

    padg.cd(0)
    latex = r.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(90)
    latex.SetTextSize(0.17)
    latex.SetTextAlign(33)
    title = title.replace("output/", "").replace(".root:/", "")
    if "_" not in title:
        title = "Run %s" % title
    keep.append(latex.DrawLatex(0.01, 0.98, "#color[46]{%s}" % title))
    return keep


def pageOne(f=None, feds1=[], feds2=[], canvas=None, pdf=""):
    pad20 = r.TPad("pad20", "pad20", 0.00, 0.00, 1.00, 1.00)
    pad20.Divide(5, 4, 0.001, 0.001)
    pad20.Draw()

    keep = []

    title = f.GetPath()
    cats = f.Get("category_vs_time")
    if multiY(cats):
        keep += draw_graph(cats, title)
    else:
        keep += draw_graph(f.Get("evn_vs_time"), title, rate=True)


    # single FED
    keep += plotList(f, pad20, offset=5,
                     names=["BcN",
                            "nBytesSW", "nWord16Skipped", "ChannelFlavor", "nQieSamples", "nTpSamples",
                            "EvN_HTRs", "OrN5_HTRs", "BcN_HTRs", "LMSEPVC", "ErrF0",
                            "", "", "", "", "nTS_for_matching",
                            # "TTS", "PopCapFrac",
                            ], feds1=feds1, feds2=feds2)

    # EvN, OrN, BcN agreement
    fed1 = sorted(feds1)[0]
    for i, fed2 in enumerate(feds2[:3]):
        pad20.cd(16 + i)
        adjustPad(logY=True)
        keep += histoLoop(f,
                          [("OrN", r.kBlue, 1),
                           ("EvN", r.kCyan, 2),
                           ("BcN", r.kBlack, 3),
                           ],
                          lambda x: "delta%s_%s_%s" % (x, fed1, fed2),
                          )

    # fibers
    pad20.cd(19)
    adjustPad(logY=True)
    keep += histoLoop(f,
                      [("MatchedFibersCh0", r.kBlue, 1),
                       ("MatchedFibersCh1", r.kCyan, 2),
                       ("MatchedFibersCh2", r.kBlack, 3),
                       ("MatchedTriggerTowers", r.kGreen, 4),
                       ],
                      lambda x: x,
                      )

    canvas.Print(pdf)


def pageTwo(f=None, feds1=[], feds2=[], canvas=None, pdf="", names=[]):
    # don't print blank page
    if not any([f.Get(name) for name in names]):
        return

    pad0 = r.TPad("pad0", "pad0", 0.00, 0.00, 1.00, 1.00)
    pad0.Divide(2, 1)
    pad0.Draw()
    keep = plotGlobal(f, pad0, offset=1, names=names, feds1=feds1, feds2=feds2)
    canvas.Print(pdf)


def makeSummaryPdf(inputFiles=[], feds1=[], feds2=[], pdf="summary.pdf"):
    r.gROOT.SetBatch(True)
    r.gROOT.SetStyle("Plain")
    r.gErrorIgnoreLevel = r.kWarning

    canvas = r.TCanvas()
    canvas.Print(pdf + "[")

    for fileName in inputFiles:
        f = r.TFile(fileName)
        if (not f) or f.IsZombie():
            continue

        pageOne(f, feds1, feds2, canvas, pdf)
        if feds2:
            pageTwo(f, feds1, feds2, canvas, pdf, names=["adc_vs_adc", "tp_vs_tp"])
            pageTwo(f, feds1, feds2, canvas, pdf, names=["adc_vs_adc_both_soi"])

        f.Close()
    canvas.Print(pdf + "]")
