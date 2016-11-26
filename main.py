# common imports
from __init__ import *

# internal functions
from util import *
from visu import *

def work(gdat, indxprocwork):

    timereal = time.time()
    timeproc = time.clock()
    
    # re-seed the random number generator for this chain
    seed()
    
    # empty object to hold chain-specific variables that will be modified by the chain
    gdatmodi = tdpy.util.gdatstrt()
    
    # data structure to hold the indices of model PS to be compared to the reference catalog 
    gdatmodi.indxmodlpntscomp = [[] for l in gdat.indxpopl]
    
    # construct the initial state
    if gdat.verbtype > 0:
        print 'Initializing the unit sample vector'
    
    ## unit sample vector
    gdatmodi.drmcsamp = zeros((gdat.numbpara, 2))
   
    ## Fixed-dimensional parameters
    for k in gdat.indxfixp:
        if gdat.randinit or gdat.truefixp[k] == None:
            if k in gdat.indxfixpnumbpnts:
                gdatmodi.drmcsamp[gdat.indxfixp[k], 0] = choice(arange(gdat.minmnumbpnts, gdat.maxmnumbpnts[k] + 1))
            else:
                gdatmodi.drmcsamp[gdat.indxfixp[k], 0] = rand()
        
        else:
            gdatmodi.drmcsamp[gdat.indxfixp[k], 0] = cdfn_fixp(gdat, gdat.truefixp[k], k)
          
    ## lists of occupied and empty transdimensional parameters
    thisnumbpnts = gdatmodi.drmcsamp[gdat.indxfixpnumbpnts, 0].astype(int)
    gdatmodi.thisindxpntsfull = []
    gdatmodi.thisindxpntsempt = []
    if gdat.numbtrap > 0:
        for l in gdat.indxpopl:
            gdatmodi.thisindxpntsfull.append(range(thisnumbpnts[l]))
            gdatmodi.thisindxpntsempt.append(range(thisnumbpnts[l], gdat.maxmnumbpnts[l]))
    else:
        gdatmodi.thisindxpntsfull = []
    gdatmodi.thisindxsamplgal, gdatmodi.thisindxsampbgal, gdatmodi.thisindxsampspec, gdatmodi.thisindxsampspep, \
                                                                                                    gdatmodi.thisindxsampcompcolr = retr_indx(gdat, gdatmodi.thisindxpntsfull)
        
    if gdat.numbtrap > 0:
        ## PS components
        if gdat.randinit:
            randinittemp = True
        else:
            try:
                for l in gdat.indxpopl:
                    gdatmodi.drmcsamp[gdatmodi.thisindxsamplgal[l], 0] = copy(cdfn_self(gdat.truelgal[l], -gdat.maxmgangmodl, 2. * gdat.maxmgangmodl))
                    gdatmodi.drmcsamp[gdatmodi.thisindxsampbgal[l], 0] = copy(cdfn_self(gdat.truebgal[l], -gdat.maxmgangmodl, 2. * gdat.maxmgangmodl))
                    if gdat.fluxdisttype[l] == 'powr':
                        fluxdistslop = icdf_atan(gdatmodi.drmcsamp[gdat.indxfixpfluxdistslop[l], 0], gdat.minmfluxdistslop[l], gdat.factfluxdistslop[l])
                        fluxunit = cdfn_flux_powr(gdat.truespec[l][0, gdat.indxenerfluxdist[0], :], gdat.minmflux, gdat.maxmflux, fluxdistslop)
                    if gdat.fluxdisttype[l] == 'brok':
                        flux = gdat.truespec[l][0, gdat.indxenerfluxdist[0], :]
                        fluxdistbrek = icdf_logt(gdatmodi.drmcsamp[gdat.indxfixpfluxdistbrek[l], 0], gdat.minmfluxdistbrek[l], gdat.factfluxdistbrek[l])
                        fluxdistsloplowr = icdf_atan(gdatmodi.drmcsamp[gdat.indxfixpfluxdistsloplowr[l], 0], gdat.minmfluxdistsloplowr[l], gdat.factfluxdistsloplowr[l])
                        fluxdistslopuppr = icdf_atan(gdatmodi.drmcsamp[gdat.indxfixpfluxdistslopuppr[l], 0], gdat.minmfluxdistslopuppr[l], gdat.factfluxdistslopuppr[l])
                        fluxunit = cdfn_flux_brok(flux, gdat.minmflux, gdat.maxmflux, fluxdistbrek, fluxdistsloplowr, fluxdistslopuppr)
                    gdatmodi.drmcsamp[gdatmodi.thisindxsampspec[l][gdat.indxenerfluxdist[0], :], 0] = copy(fluxunit)
                    if gdat.numbener > 1:
                        # color parameters
                        gdatmodi.drmcsamp[gdatmodi.thisindxsampspep[l][:, 0], 0] = cdfn_gaus(gdat.truespep[l][:, 0], gdat.truesinddistmean[l], gdat.truesinddiststdv[l])
                        if gdat.spectype[l] == 'curv':
                            gdatmodi.drmcsamp[gdatmodi.thisindxsampspep[l][:, 1], 0] = cdfn_gaus(gdat.truespep[l][:, 1], gdat.curvdistmean[l], gdat.curvdiststdv[l])
                        if gdat.spectype[l] == 'expo':
                            gdatmodi.drmcsamp[gdatmodi.thisindxsampspep[l][:, 1], 0] = cdfn_logt(gdat.truespep[l][:, 1], gdat.minmener, gdat.factener)
                
                randinittemp = False
            except:
                randinittemp = True
                print 'Reference catalog is inappropriate for deterministic initial state. Seeding the initial state randomly...'
        
        if randinittemp:
            for l in gdat.indxpopl:
                gdatmodi.drmcsamp[gdatmodi.thisindxsampcompcolr[l], 0] = rand(gdatmodi.thisindxsampcompcolr[l].size)

    if gdat.verbtype > 1:
        print 'drmcsamp'
        for k in gdat.indxpara:
            print gdatmodi.drmcsamp[k, :]
    
    # check the initial unit sample vector for bad entries
    indxsampbaddlowr = where(gdatmodi.drmcsamp[gdat.numbpopl:, 0] < 0.)[0] + gdat.numbpopl
    indxsampbadduppr = where(gdatmodi.drmcsamp[gdat.numbpopl:, 0] > 1.)[0] + gdat.numbpopl
    indxsampbadd = concatenate((indxsampbaddlowr, indxsampbadduppr))
    if indxsampbadd.size > 0:
        print 'Initial unit sample vector went outside the unit interval...'
        gdatmodi.drmcsamp[indxsampbaddlowr, 0] = 0.
        gdatmodi.drmcsamp[indxsampbadduppr, 0] = 1.

    ## sample vector
    gdatmodi.thissampvarb = retr_sampvarb(gdat, gdatmodi.thisindxpntsfull, gdatmodi.drmcsamp[:, 0])

    ## initial predicted count maps
    if gdat.pntstype == 'lght':
        temp = retr_maps(gdat, gdatmodi.thisindxpntsfull, gdatmodi.thissampvarb, evalcirc=gdat.evalcirc)
        if gdat.correxpo:
            gdatmodi.thispntsflux, gdatmodi.thispntscnts, gdatmodi.thismodlflux, gdatmodi.thismodlcnts = temp
        else:
            gdatmodi.thispntsflux, gdatmodi.thismodlflux, gdatmodi.thismodlfluxtotl = temp 
   
    if gdat.pntstype == 'lens':
        
        gdatmodi.thispntsflux = zeros((gdat.numbener, gdat.numbpixl, gdat.numbevtt))
        gdatmodi.thisdefl = zeros((gdat.numbpixl, 2))
        # create source model object
        gdatmodi.thissourobjt = franlens.Source(gdat.truesourtype, gdatmodi.thissampvarb[gdat.indxfixplgalsour], \
                                                               gdatmodi.thissampvarb[gdat.indxfixpbgalsour], \
                                                               gdatmodi.thissampvarb[gdat.indxfixpfluxsour], \
                                                               gdatmodi.thissampvarb[gdat.indxfixpsizesour], \
                                                               gdatmodi.thissampvarb[gdat.indxfixpratisour], \
                                                               gdatmodi.thissampvarb[gdat.indxfixpanglsour])
        
        # construct lens object
        gdatmodi.thislistlensobjt = []
        ## PS
        if gdat.numbtrap > 0:
            for l in gdat.indxpopl:
                for k in range(gdatmodi.thissampvarb[gdat.indxfixpnumbpnts[l]].astype(int)):
                    # create lens model object for the PS 
                    gdatmodi.thislistlensobjt.append(franlens.LensModel(gdat.truelenstype, gdatmodi.thissampvarb[gdatmodi.thisindxsamplgal[l][k]], \
                                                                                   gdatmodi.thissampvarb[gdatmodi.thisindxsampbgal[l][k]], \
                                                                                   0., 0., 0., 0., \
                                                                                   # beta
                                                                                   gdatmodi.thissampvarb[gdatmodi.thisindxsampspec[l][0, k]]))
        # host
        gdatmodi.thislistlensobjt.append(franlens.LensModel(gdat.truelenstype, gdatmodi.thissampvarb[gdat.indxfixplgalhost], \
                                                                               gdatmodi.thissampvarb[gdat.indxfixpbgalhost], \
                                                                               gdatmodi.thissampvarb[gdat.indxfixpellphost], \
                                                                               gdatmodi.thissampvarb[gdat.indxfixpanglhost], \
                                                                               gdatmodi.thissampvarb[gdat.indxfixpsherhost], \
                                                                               gdatmodi.thissampvarb[gdat.indxfixpsanghost], \
                                                                               gdatmodi.thissampvarb[gdat.indxfixpbeinhost]))

        # calculate the initial predicted flux map
        gdatmodi.thispntsflux[0, :, 0], gdatmodi.thisdefl = franlens.macro_only_image(gdat.lgalgrid, gdat.bgalgrid, gdatmodi.thissourobjt, \
                                                                                    gdatmodi.thislistlensobjt, gdatmodi.thissampvarb[gdat.indxfixpsigc])
        gdatmodi.thismodlflux = gdatmodi.thispntsflux
        gdatmodi.thispntscnts = gdatmodi.thispntsflux * gdat.expo * gdat.apix
        if gdat.enerbins:
            gdatmodi.thispntscnts *= gdat.diffener[:, None, None]
        gdatmodi.thismodlcnts = gdatmodi.thispntscnts
   
    # temp
    if gdat.pntstype == 'lens':
        if gdatmodi.thismodlcnts.shape[1] != gdat.numbpixl:
            raise Exception('Number of pixels in the lensing map mismatches with that of PCAT')

    ## indices of the PS parameters
    indxsamplgaltemp, indxsampbgaltemp, indxsampspectemp, indxsampspeptemp, indxsampcompcolrtemp = retr_indx(gdat, gdatmodi.thisindxpntsfull)
    

    if gdat.evalpsfnpnts:
        ## PSF
        gdatmodi.thispsfn = retr_psfn(gdat, gdatmodi.thissampvarb[gdat.indxfixppsfp], gdat.indxener, gdat.binsangl, gdat.psfntype, \
                                                                                                                    binsoaxi=gdat.binsoaxi, varioaxi=gdat.varioaxi)
        
        if gdat.boolintpanglcosi:
            binsangltemp = gdat.binsanglcosi
        else:
            binsangltemp = gdat.binsangl
        
        if gdat.varioaxi:
            gdatmodi.thispsfnintp = [[] for k in gdat.indxoaxi]
            for k in gdat.indxoaxi:
                gdatmodi.thispsfnintp[k] = interp1d(binsangltemp, gdatmodi.thispsfn[:, :, :, k], axis=1)
            gdatmodi.nextpsfnintp = [[] for k in gdat.indxoaxi]
        else:
            gdatmodi.thispsfnintp = interp1d(binsangltemp, gdatmodi.thispsfn, axis=1)
        
    # log-prior
    if gdat.bindprio:
        gdatmodi.thislpri = empty((gdat.numbpopl, gdat.numbfluxplot))
    else:
        gdatmodi.thislpri = empty((gdat.numbpopl, 2))

    # allocate memory for variables to hold the proposed state
    ## sample vector
    gdatmodi.nextsampvarb = copy(gdatmodi.thissampvarb)
        
    ## likelihood
    gdatmodi.nextllik = zeros_like(gdatmodi.thispntsflux)
    gdatmodi.deltllik = 0.
        
    ## modification catalog
    gdatmodi.modilgal = zeros(gdat.maxmnumbpntstotl + 2)
    gdatmodi.modibgal = zeros(gdat.maxmnumbpntstotl + 2)
    gdatmodi.modispec = zeros((gdat.numbener, gdat.maxmnumbpntstotl + 2))
    gdatmodi.modispep = zeros((gdat.maxmnumbpntstotl + 2, 2))
    
    ## flux and count maps
    gdatmodi.nextpntsflux = zeros_like(gdatmodi.thispntsflux)
    gdatmodi.nextmodlflux = zeros_like(gdatmodi.thispntsflux)
    gdatmodi.nextmodlcnts = zeros_like(gdatmodi.thispntsflux)
        
    # plotting variables
    gdatmodi.thiscntsbackfwhm = empty((gdat.numbener, gdat.numbpixl, gdat.numbevtt))
   
    # log-prior
    gdatmodi.nextlpri = empty((gdat.numbpopl, gdat.numbfluxplot))

    # log the initial state
    if gdat.verbtype > 1 and gdat.numbtrap > 0:
        print 'thisindxpntsfull'
        for l in gdat.indxpopl:
            print gdatmodi.thisindxpntsfull[l]
        
        print 'thisindxpntsempt'
        for l in gdat.indxpopl:
            print gdatmodi.thisindxpntsempt  
        
        print 'thisindxsamplgal'
        for l in gdat.indxpopl:
            print gdatmodi.thisindxsamplgal[l]
        
        print 'thisindxsampbgal'
        for l in gdat.indxpopl:
            print gdatmodi.thisindxsampbgal[l]
        
        print 'thisindxsampspec'
        for l in gdat.indxpopl:
            print gdatmodi.thisindxsampspec[l]
       
        if gdat.numbener > 1:
            print 'thisindxsampspep'
            for l in gdat.indxpopl:
                print gdatmodi.thisindxsampspep[l]
        
        print 'thisindxsampcompcolr'
        for l in gdat.indxpopl:
            print gdatmodi.thisindxsampcompcolr[l]

    if gdat.verbtype > 1:
        print 'thissampvarb'
        for k in gdat.indxpara:
            print gdatmodi.thissampvarb[k]
        
    if gdat.verbtype > 1:
        tdpy.util.show_memo(gdatmodi, 'gdatmodi')

    # sweeps to be saved
    gdat.boolsave = zeros(gdat.numbswep, dtype=bool)
    indxswepsave = arange(gdat.numbburn, gdat.numbburn + gdat.numbsamp * gdat.factthin, gdat.factthin)
    gdat.boolsave[indxswepsave] = True
    gdat.indxsampsave = zeros(gdat.numbswep, dtype=int) - 1
    gdat.indxsampsave[indxswepsave] = arange(gdat.numbsamp)
    
    if gdat.diagmode:
        if indxswepsave.size != gdat.numbsamp:
            raise Exception('Inappropriate number of samples.')

    # run the sampler
    listchan = rjmc(gdat, gdatmodi, indxprocwork)
    
    timereal = time.time() - timereal
    timeproc = time.clock() - timeproc
    
    listchan.append(timereal)
    listchan.append(timeproc)
    
    return listchan

    
def init( \
         # user interaction
         verbtype=1, \
         pathbase=os.environ["PCAT_DATA_PATH"], \

         # diagnostics
         # temp
         diagmode=True, \
         pntscntr=False, \

         # sampler
         numbswep=None, \
         numbburn=None, \
         factthin=None, \
         
         datatype='mock', \
         indxevttincl=None, \
         indxenerincl=None, \
         
         # comparison with the reference catalog
         anglassc=None, \
         margfactcomp=0.9, \
         nameexpr=None, \

         numbspatdims=2, \
         pntstype='lght', \

         randinit=None, \
         loadvaripara=False, \
         optiprop=False, \
         regulevi=False, \
         strgexpr=None, \
         strgcatl=None, \
         strgback=[1.], \
         lablback=None, \
         nameback=None, \
         strgexpo=1., \
         numbproc=None, \
         liketype='pois', \
         exprtype='ferm', \
         lgalcntr=0., \
         bgalcntr=0., \
         maxmangl=None, \
         exprinfo=None, \
         pixltype=None, \
         
         # plotting
         numbswepplot=50000, \
         makeplot=True, \
         scalmaps='asnh', \
         satumaps=None, \
         makeanim=True, \
         anotcatl=False, \
         strgbinsener=None, \
         strgexprname=None, \
         strganglunit=None, \
         strganglunittext=None, \
         anglfact=None, \
         fluxfactplot=None, \
         enerfact=None, \
         
         # misc
         strgfunctime='clck', \
         strgxaxi=None, \
         strgyaxi=None, \

         # model
         ## PSF
         specfraceval=0.1, \
         numbangl=1000, \
         binsangltype='logt', \
         numbsidepntsprob=400, \
         strgfluxunit=None, \
         strgflux=None, \
         strgenerunit=None, \
         indxenerfull=None, \
         indxevttfull=None, \
         binsenerfull=None, \
         maxmnumbpnts=array([1000]), \
         asymfluxprop=False, \
         psfninfoprio=True, \
         ## spectral

         # prior
         priotype='logt', \
         priofactdoff=0., \
         margfactmodl=0.9, \
         bindprio=False, \
         maxmbacp=None, \
         minmbacp=None, \
         maxmgang=None, \
         minmmeanpnts=None, \
         maxmmeanpnts=None, \
    
         spatdisttype=None, \
         spatdistslop=None, \
         
         fluxdisttype=None, \
         minmfluxdistslop=None, \
         maxmfluxdistslop=None, \
         minmfluxbrek=None, \
         maxmfluxbrek=None, \
         minmfluxdistbrek=None, \
         maxmfluxdistbrek=None, \
         minmfluxdistsloplowr=None, \
         maxmfluxdistsloplowr=None, \
         minmfluxdistslopuppr=None, \
         maxmfluxdistslopuppr=None, \
         minmsinddistmean=None, \
         maxmsinddistmean=None, \
         minmsinddiststdv=None, \
         maxmsinddiststdv=None, \

         psfntype=None, \
         varioaxi=None, \
         minmsigm=None, \
         maxmsigm=None, \
         meansigm=None, \
         stdvsigm=None, \
         minmgamm=None, \
         maxmgamm=None, \
         meangamm=None, \
         stdvgamm=None, \
         minmpsff=None, \
         maxmpsff=None, \
         meanpsff=None, \
         stdvpsff=None, \

         minmfluxsour=None, \
         maxmfluxsour=None, \
         minmsizesour=None, \
         maxmsizesour=None, \
         minmratisour=None, \
         maxmratisour=None, \
         minmellphost=None, \
         maxmellphost=None, \
         minmsherhost=None, \
         maxmsherhost=None, \
         minmbeinhost=None, \
         maxmbeinhost=None, \
    
         spectype=None, \
         
         curvdistmean=None, \
         curvdiststdv=None, \
         
         minmflux=None, \
         maxmflux=None, \
        
         # proposals
         numbpntsmodi=1, \
         stdvmeanpnts=0.05, \
         stdvfluxdistslop=0.1, \
         stdvproppsfp=0.1, \
         stdvback=0.04, \
         stdvlbhl=0.1, \
         stdvlbhlvari=True, \
         stdvflux=0.15, \
         stdvspep=0.15, \
         stdvspmrsind=0.2, \
         fracrand=0.05, \
         boolpropfluxdist=True, \
         boolpropfluxdistbrek=True, \
         proppsfp=True, \
         propbacp=True, \
         proplens=True, \
         radispmr=None, \

         truevarioaxi=None, \
         truepsfntype=None, \

         # mock data
         mockspatdisttype=None, \
         mockspatdistslop=None, \
         mockfluxdisttype=None, \
         mockminmflux=None, \
         mockmaxmflux=None, \
         mockfluxdistslop=None, \
         mockfluxdistbrek=None, \
         mockfluxdistsloplowr=None, \
         mockfluxdistslopuppr=None, \
         mockspectype=None, \
         mocksinddistmean=None, \
         mocksinddiststdv=None, \
         mockpsfntype=None, \
         mockvarioaxi=None, \
         mockstrgback=None, \
         mockbacp=None, \
         
         mocklgalsour=None, \
         mockbgalsour=None, \
         mockfluxsour=None, \
         mocksizesour=None, \
         mockratisour=None, \
         mockanglsour=None, \
         mocklgalhost=None, \
         mockbgalhost=None, \
         mockellphost=None, \
         mockanglhost=None, \
         mocksherhost=None, \
         mocksanghost=None, \
         mockbeinhost=None, \
         
         mocknumbpnts=None, \
         numbsidecart=200, \
         numbsideheal=256, \
         numbdatasamp=100, \
        ):

    # construct the global object 
    gdat = tdpy.util.gdatstrt()
    for attr, valu in locals().iteritems():
        if '__' not in attr:
            setattr(gdat, attr, valu)

    # defaults
    ### number of backgrounds
   
    ### number of populations
    gdat.numbpopl = gdat.maxmnumbpnts.size
    if gdat.datatype == 'mock':
        if gdat.mocknumbpnts == None:
            gdat.mocknumbpopl = 1
        else:
            gdat.mocknumbpopl = gdat.mocknumbpnts.size
        if gdat.mockstrgback == None:
            gdat.mockstrgback = gdat.strgback
        
        gdat.mocknumbback = len(gdat.mockstrgback)
    gdat.numbback = len(gdat.strgback)
    gdat.indxpopl = arange(gdat.numbpopl, dtype=int)
    gdat.mockindxpopl = arange(gdat.mocknumbpopl, dtype=int)
    
    if gdat.indxevttincl == None:
        if gdat.exprtype == 'ferm':
            gdat.indxevttincl = arange(2, 4)
        if gdat.exprtype == 'chan':
            gdat.indxevttincl = arange(1)
    
    if gdat.indxenerincl == None:
        if gdat.exprtype == 'ferm':
            gdat.indxenerincl = arange(1, 3)
        if gdat.exprtype == 'chan':
            gdat.indxenerincl = arange(2)
    
    ### number of energy bins
    if gdat.indxenerincl != None:
        gdat.numbener = gdat.indxenerincl.size
    else:
        gdat.numbener = 1

    if gdat.randinit == None:
        if gdat.datatype == 'mock':
            gdat.randinit = False
        else:
            gdat.randinit = True

    # if the images are arcsinh scaled, do not saturate them
    if gdat.satumaps == None:
        if gdat.scalmaps == 'asnh':
            gdat.satumaps = False
        else:
            gdat.satumaps = True

    if gdat.strgflux == None:
        if gdat.pntstype == 'lens':
            gdat.strgflux = 'R'
        else:
            if gdat.exprtype == 'ferm' or gdat.exprtype == 'chan':
                gdat.strgflux = 'f'
            if gdat.exprtype == 'chem':
                gdat.strgflux = 'p'
    
    if gdat.strgfluxunit == None:
        if gdat.pntstype == 'lens':
            gdat.strgfluxunit = 'arcsec'
        else:
            if gdat.exprtype == 'sdss' or gdat.exprtype == 'hubb':
                gdat.strgfluxunit = 'mag'
            if gdat.exprtype == 'ferm':
                gdat.strgfluxunit = '1/cm$^2$/s/GeV'
            if gdat.exprtype == 'chan':
                gdat.strgfluxunit = '1/cm$^2$/s/KeV'

    if gdat.indxevttfull == None:
        if gdat.exprtype == 'ferm':
            gdat.indxevttfull = arange(4)
        else:
            gdat.indxevttfull = arange(1)

    if gdat.strgenerunit == None:
        if gdat.exprtype == 'ferm':
            gdat.strgenerunit = 'GeV'
        if gdat.exprtype == 'chan':
            gdat.strgenerunit = 'KeV'
        if gdat.exprtype == 'chem':
            gdat.strgenerunit = ''

    if gdat.exprtype == 'ferm':
        if gdat.anglassc == None:
            gdat.anglassc = deg2rad(0.5)
        if gdat.pixltype == None:
            gdat.pixltype = 'heal'
    

    if gdat.strgexprname == None:
        if gdat.exprtype == 'chan':
            gdat.strgcatl = 'Chandra'
        if gdat.exprtype == 'ferm':
            gdat.strgexprname = 'Fermi-LAT'
        if gdat.exprtype == 'chem':
            gdat.strgexprname = 'TGAS-RAVE'
    
    if gdat.strganglunit == None:
        if gdat.exprtype == 'ferm':
            gdat.strganglunit = '$^o$'
        if gdat.exprtype == 'sdss' or gdat.exprtype == 'chan' or gdat.exprtype == 'hubb':
            gdat.strganglunit = '$^{\prime\prime}$'

    if gdat.strganglunittext == None:
        if gdat.exprtype == 'ferm':
            gdat.strganglunittext = 'degree'
        if gdat.exprtype == 'sdss' or gdat.exprtype == 'chan' or gdat.exprtype == 'hubb':
            gdat.strganglunittext = 'arcsec'
    
    if gdat.anglfact == None:
        if gdat.exprtype == 'ferm':
            gdat.anglfact = 180. / pi
        if gdat.exprtype == 'sdss' or gdat.exprtype == 'chan' or gdat.exprtype == 'hubb':
            gdat.anglfact = 3600 * 180. / pi
        if gdat.exprtype == 'chem':
            gdat.anglfact = 1.

    if gdat.fluxfactplot == None:
        if gdat.pntstype == 'lens':
            gdat.fluxfactplot = gdat.anglfact
        else:
            gdat.fluxfactplot = 1.

    if gdat.enerfact == None:
        if gdat.exprtype == 'ferm':
            gdat.enerfact = 1.
        if gdat.exprtype == 'chem':
            gdat.enerfact = 1.
        if gdat.exprtype == 'chan':
            gdat.enerfact = 1e3

    if gdat.strgxaxi == None:
        if gdat.exprtype == 'chem':
            gdat.strgxaxi = r'$E_k^{\prime}$'
        else:
            if gdat.lgalcntr != 0. or gdat.bgalcntr != 0.:
                gdat.strgxaxi = '$x$'
            else:
                gdat.strgxaxi = '$l$'

    if gdat.strgyaxi == None:
        if gdat.exprtype == 'chem':
            gdat.strgyaxi = r'$L_z^{\prime}$'
        else:
            if gdat.lgalcntr != 0. or gdat.bgalcntr != 0.:
                gdat.strgyaxi = '$y$'
            else:
                gdat.strgyaxi = '$b$'

    ## experiment defaults
    if gdat.binsenerfull == None:
        if gdat.exprtype == 'ferm':
            gdat.binsenerfull = array([0.1, 0.3, 1., 3., 10., 100.])
        elif gdat.exprtype == 'chan':
            gdat.binsenerfull = array([5e-4, 2e-3, 8e-3])
        else:
            gdat.binsenerfull = array([0.])
   
    # energy bin indices
    if gdat.indxenerfull == None:
        if gdat.exprtype == 'ferm':
            gdat.indxenerfull = arange(5)
        elif gdat.exprtype == 'chan':
            gdat.indxenerfull = arange(2)
        else:   
            gdat.indxenerfull = arange(gdat.binsenerfull.size - 1)
   
    # energy band string
    if gdat.strgbinsener == None and gdat.binsenerfull != None:
        if gdat.exprtype == 'sdss' or gdat.exprtype == 'hubb':
            if gdat.exprtype == 'sdss':
                gdat.strgbinsener = ['z-band', 'i-band', 'r-band', 'g-band', 'u-band']
            if gdat.exprtype == 'hubb':
                gdat.strgbinsener = ['F606W']
        else: 
            gdat.strgbinsener = []
            for i in gdat.indxenerfull:
                gdat.strgbinsener.append('%.3g %s - %.3g %s' % (gdat.enerfact * gdat.binsenerfull[i], gdat.strgenerunit, \
                                                                                                                   gdat.enerfact * gdat.binsenerfull[i+1], gdat.strgenerunit))
   
    # flux bin for likelihood evaluation inside circles
    if gdat.exprtype == 'ferm':
        gdat.numbfluxprox = 3
    else:
        gdat.numbfluxprox = 1
    
    ## Lensing
    if gdat.exprtype == 'hubb':
        if gdat.anglassc == None:
            gdat.anglassc = 0.15 / gdat.anglfact
        if gdat.pixltype == None:
            gdat.pixltype = 'heal'

    ## Chandra and SDSS
    if gdat.exprtype == 'chan' or gdat.exprtype == 'sdss':
        if gdat.anglassc == None:
            gdat.anglassc = 0.5 / gdat.anglfact
        if gdat.pixltype == None:
            gdat.pixltype = 'cart'
    
    if exprinfo == None:
        if exprtype == 'ferm' or exprtype == 'chan':
            exprinfo = True
        else:
            exprinfo = False

    if gdat.nameexpr == None:
        if gdat.exprtype == 'ferm':
            gdat.nameexpr = 'Fermi-LAT'
        if gdat.exprtype == 'sdss':
            gdat.nameexpr = 'SDSS'
        if gdat.exprtype == 'chan':
            gdat.nameexpr = 'Chandra'
        if gdat.exprtype == 'hubb':
            gdat.nameexpr = 'HST'
        # temp
        if gdat.exprtype == 'chem':
            gdat.nameexpr = 'Gaia'
    
    if gdat.lablback == None:
        if gdat.numbback == 1:
            gdat.lablback = [r'$\mathcal{I}$']
        else:
            gdat.lablback = [r'$\mathcal{I}$', r'$\mathcal{D}$']
    
    if gdat.nameback == None:
        if gdat.numbback == 1:
            gdat.nameback = ['normisot']
        else:
            gdat.nameback = ['normisot', 'normdiff']
    
    if gdat.radispmr == None:
        gdat.radispmr = 2. / gdat.anglfact
   
    if gdat.pathbase[-1] != '/':
        gdat.pathbase += '/'
    
    # paths
    gdat.pathdata = gdat.pathbase + 'data/'
    gdat.pathimag = gdat.pathbase + 'imag/'
    
    ## PSF class
    if gdat.indxevttincl != None:
        gdat.evttbins = True
    else:
        gdat.evttbins = False
    if gdat.evttbins:
        gdat.numbevtt = gdat.indxevttincl.size
        gdat.numbevttfull = gdat.indxevttfull.size
    else:
        gdat.numbevtt = 1
        gdat.numbevttfull = 1
        gdat.indxevttincl = array([0])
    gdat.indxevtt = arange(gdat.numbevtt)

    ## energy
    if gdat.binsenerfull.size > 1:
        gdat.enerbins = True
    else:
        gdat.enerbins = False
    if gdat.enerbins:
        gdat.numbener = gdat.indxenerincl.size
        gdat.numbenerfull = gdat.binsenerfull.size - 1
        gdat.indxenerinclbins = empty(gdat.numbener+1, dtype=int)
        gdat.indxenerinclbins[0:-1] = gdat.indxenerincl
        gdat.indxenerinclbins[-1] = gdat.indxenerincl[-1] + 1
        gdat.binsener = gdat.binsenerfull[gdat.indxenerinclbins]
        gdat.diffener = (roll(gdat.binsener, -1) - gdat.binsener)[0:-1]
        gdat.meanener = sqrt(roll(gdat.binsener, -1) * gdat.binsener)[0:-1]
        gdat.minmener = gdat.binsener[0]
        gdat.maxmener = gdat.binsener[-1]
        gdat.indxenerfull = gdat.binsenerfull.size - 1
    else:
        gdat.indxenerfull = []
        gdat.numbener = 1
        gdat.numbenerfull = 1
        gdat.indxenerincl = array([0])
        gdat.indxenerfluxdist = array([0])
        gdat.factspecener = array([1.])
    gdat.indxener = arange(gdat.numbener, dtype=int)
    gdat.indxenerfluxdist = ceil(array([gdat.numbener]) / 2.).astype(int) - 1
       
    # construct the true PSF
    if gdat.exprtype == 'ferm':
        retr_fermpsfn(gdat)
        gdat.truepsfntype = 'doubking'
    if gdat.exprtype == 'chan':
        retr_chanpsfn(gdat)
        gdat.truepsfntype = 'singgaus'
    if gdat.exprtype == 'sdss':
        retr_sdsspsfn(gdat)
        gdat.truepsfntype = 'singgaus'
    if gdat.exprtype == 'hubb':
        retr_hubbpsfn(gdat)
        gdat.truepsfntype = 'singgaus'
    if gdat.exprtype == 'chem':
        gdat.truevarioaxi = False
        gdat.truepsfntype = 'singgaus'
        gdat.truepsfp = array([0.1 / gdat.anglfact])
 
    # model
    ## hyperparameters
    setp_varbfull(gdat, 'meanpnts', [gdat.minmmeanpnts, gdat.maxmmeanpnts], [1., 1e3], gdat.numbpopl)
    
    ### spatial
    if gdat.exprtype == 'chan':
        gdat.maxmgang = 0.492 / gdat.anglfact * gdat.numbsidecart / 2.
    if gdat.exprtype == 'ferm':
        gdat.maxmgang = 20. / gdat.anglfact
    if gdat.exprtype == 'chem':
        gdat.maxmgang = 1.
    if gdat.exprtype == 'hubb':
        gdat.maxmgang = 2. / gdat.anglfact
    gdat.minmlgal = -gdat.maxmgang
    gdat.maxmlgal = gdat.maxmgang
    gdat.minmbgal = -gdat.maxmgang
    gdat.maxmbgal = gdat.maxmgang
    
    if gdat.spatdisttype == None:
        gdat.spatdisttype = array(['unif' for l in gdat.indxpopl])
    
    ### flux
    if gdat.fluxdisttype == None:
        gdat.fluxdisttype = array(['powr' for l in gdat.indxpopl])

    if gdat.exprtype == 'ferm':
        gdat.minmflux = 3e-11
    if gdat.exprtype == 'chan':
        gdat.minmflux = 1e-5
    if gdat.exprtype == 'chem':
        gdat.minmflux = 1e0
    if gdat.exprtype == 'ferm':
        gdat.maxmflux = 1e-7
    if gdat.exprtype == 'chan':
        gdat.maxmflux = 1e-3
    if gdat.exprtype == 'chem':
        gdat.maxmflux = 1e4
    
    setp_varbfull(gdat, 'fluxdistslop', [gdat.minmfluxdistslop, gdat.maxmfluxdistslop], [1.5, 3.5], gdat.numbpopl)
    setp_varbfull(gdat, 'fluxdistbrek', [gdat.minmfluxbrek, gdat.maxmfluxbrek], [gdat.minmflux, gdat.maxmflux], gdat.numbpopl)
    setp_varbfull(gdat, 'fluxdistsloplowr', [gdat.minmfluxdistsloplowr, gdat.maxmfluxdistsloplowr], [-1.5, 3.5], gdat.numbpopl)
    setp_varbfull(gdat, 'fluxdistslopuppr', [gdat.minmfluxdistslopuppr, gdat.maxmfluxdistslopuppr], [1.5, 3.5], gdat.numbpopl)
    
    ### color
    if gdat.numbener > 1:
        setp_varbfull(gdat, 'sinddistmean', [gdat.minmsinddistmean, gdat.maxmsinddistmean], [0.5, 3.], gdat.numbpopl)
        setp_varbfull(gdat, 'sinddiststdv', [gdat.minmsinddiststdv, gdat.maxmsinddiststdv], [0.1, 1.], gdat.numbpopl)
    
    # PS spectral model
    if gdat.spectype == None:
        gdat.spectype = array(['powr' for l in gdat.indxpopl])

    ## PSF
    if gdat.psfntype == None:
        gdat.psfntype = gdat.truepsfntype

    if gdat.varioaxi == None:
        if gdat.exprtype == 'chan':
            gdat.varioaxi = True
        else:
            gdat.varioaxi = False

    if gdat.psfninfoprio:
        gdat.meanpsfp = gdat.truepsfp
        gdat.stdvpsfp = 0.1 * gdat.truepsfp
    else:
        if gdat.exprtype == 'ferm':
            minmsigm = 0.1
            maxmsigm = 5.
        if gdat.exprtype == 'chan':
            minmsigm = 0.1 / gdat.anglfact
            maxmsigm = 1. / gdat.anglfact
        if gdat.exprtype == 'hubb':
            minmsigm = 0.01 / gdat.anglfact
            maxmsigm = 0.1 / gdat.anglfact
        setp_varbfull(gdat, 'sigm', [gdat.minmsigm, gdat.maxmsigm], [0.5, 2.])
        
        minmgamm = 2.
        maxmgamm = 20.
        setp_varbfull(gdat, 'sigm', [gdat.minmgamm, gdat.maxmgamm], [0.5, 2.])
        
        gdat.minmpsff = 0.
        gdat.maxmpsff = 1.
 
    # background parameters
    setp_varbfull(gdat, 'bacp', [gdat.minmbacp, gdat.maxmbacp], [0.5, 2.])
    
    # lensing
    gdat.minmlgalsour = gdat.minmlgal
    gdat.maxmlgalsour = gdat.maxmlgal
    gdat.minmbgalsour = gdat.minmbgal
    gdat.maxmbgalsour = gdat.maxmbgal
    setp_varbfull(gdat, 'fluxsour', [gdat.minmfluxsour, gdat.maxmfluxsour], [0.5, 2.])
    setp_varbfull(gdat, 'sizesour', [gdat.minmsizesour, gdat.maxmsizesour], [0.5, 2.])
    setp_varbfull(gdat, 'ratisour', [gdat.minmratisour, gdat.maxmratisour], [0.5, 2.])
    gdat.minmanglsour = 0.
    gdat.maxmanglsour = 180.
    
    gdat.minmlgalhost = gdat.minmlgal
    gdat.maxmlgalhost = gdat.maxmlgal
    gdat.minmbgalhost = gdat.minmbgal
    gdat.maxmbgalhost = gdat.maxmbgal
    setp_varbfull(gdat, 'ellphost', [gdat.minmellphost, gdat.maxmellphost], [0., 0.5])
    gdat.minmanglhost = 0.
    gdat.maxmanglhost = 180.
    setp_varbfull(gdat, 'sherhost', [gdat.minmsherhost, gdat.maxmsherhost], [0., 0.3])
    gdat.minmsanghost = 0.
    gdat.maxmsanghost = 180.
    setp_varbfull(gdat, 'beinhost', [gdat.minmbeinhost, gdat.maxmbeinhost], [1e-3, 1e-1])

   


    if gdat.maxmangl == None:
        if gdat.exprtype == 'ferm' or gdat.exprtype == 'chan':
            if gdat.exprtype == 'ferm':
                gdat.maxmangl = 20. / gdat.anglfact
            else:
                gdat.maxmangl = 10. / gdat.anglfact
        else:
            gdat.maxmangl = 3. * gdat.maxmgang

    if gdat.datatype == 'mock':
        
        if gdat.mockspectype == None:
            gdat.mockspectype = ['powr' for l in gdat.mockindxpopl]

        if gdat.mockvarioaxi == None:
            gdat.mockvarioaxi = gdat.truevarioaxi
       
        if gdat.mockpsfntype == None:
            gdat.mockpsfntype = gdat.truepsfntype

        if gdat.mockminmflux == None:
            gdat.mockminmflux = gdat.minmflux

    # number of total sweeps
    if gdat.numbswep == None:
        gdat.numbswep = 100000

    # number of burned sweeps
    if gdat.numbburn == None:
        if gdat.datatype == 'mock' and not gdat.randinit:
            gdat.numbburn = 0
        else:
            gdat.numbburn = gdat.numbswep / 10

    # factor by which to thin the sweeps to get samples
    if gdat.factthin == None:
        gdat.factthin = int(ceil(1e-3 * (gdat.numbswep - gdat.numbburn)))

    if gdat.strgcatl == None:
        if gdat.datatype == 'mock':
            gdat.strgcatl = 'Mock'
        else:
            if gdat.exprtype == 'ferm':
                gdat.strgcatl = '3FGL'
            else:
                gdat.strgcatl = gdat.strgexprname

    # number of processes
    if gdat.numbproc == None:
        gdat.strgproc = os.uname()[1]
        if gdat.strgproc == 'fink1.rc.fas.harvard.edu' or gdat.strgproc == 'fink2.rc.fas.harvard.edu':
            gdat.numbproc = 20
        else:
            gdat.numbproc = 1

    # conditional imports
    ## import the lensing solver by Francis-Yan if the PSs are lenses
    if gdat.pntstype == 'lens':
        gdat.pixltype = 'cart'
        gdat.proppsfp = False
        gdat.propbacp = False

    # get the time stamp
    gdat.strgtimestmp = tdpy.util.retr_strgtimestmp()
    
    # check the call stack for the name of the configuration function
    gdat.strgcnfg = inspect.stack()[1][3]
   
    if gdat.pntstype == 'lens' or gdat.numbback == 0:
        gdat.evalpsfnpnts = False
        gdat.backemis = False
    else:
        gdat.evalpsfnpnts = True
        gdat.backemis = True

    # temp
    # check inputs
    if gdat.numbburn != None and gdat.numbswep != None:
        if gdat.numbburn > gdat.numbswep:
            raise Exception('Bad number of burn-in sweeps.')
        if gdat.factthin != None:
            if gdat.factthin > gdat.numbswep - gdat.numbburn:
                raise Exception('Bad thinning factor.')
    
    if not gdat.randinit and not gdat.exprinfo and gdat.datatype == 'inpt':
        raise Exception('If the data is provided by the user and no experimental information is given, initial state must be random.')
        
    if gdat.pixltype == 'heal' and gdat.numbspatdims > 2:
        raise Exception('More than 2 spatial dimensions require Cartesian binning.')

    if not gdat.propbacp and gdat.backemis:
        raise Exception('Background changes cannot be proposed if no background emission is in the model.')

    if gdat.verbtype > 0:
        print 'PCAT v0.1 started at %s' % gdat.strgtimestmp
        print 'Configuration %s' % gdat.strgcnfg
        print 'Initializing...'
        print '%d samples will be taken, discarding the first %d. The chain will be thinned by a factor of %d.' % (gdat.numbswep, gdat.numbburn, gdat.factthin)
    
    # create the PCAT folders
    gdat.pathoutp = gdat.pathdata + 'outp/' + gdat.strgtimestmp + '_' + gdat.strgcnfg + '/'
    os.system('mkdir -p %s' % gdat.pathoutp)
    pathpcatlite = gdat.pathoutp + 'catllite.fits'  
    pathpcat = gdat.pathoutp + 'catl.fits'  
    
    # initial setup
    setpinit(gdat, True) 
   
    # redirect standard output to a file if in a Screen session
    # temp
    # if os.environ["TERM"] == 'screen':
    #    path = gdat.pathoutp + 'rlog.txt'
    #    sys.stdout = open(path, 'w')

    # generate mock data
    if gdat.datatype == 'mock':
        
        if gdat.mocknumbpnts == None:
            gdat.mocknumbpnts = empty(gdat.numbpopl, dtype=int)
            for l in gdat.indxpopl:
                gdat.mocknumbpnts[l] = random_integers(0, gdat.maxmnumbpnts[l])
        gdat.mocknumbpopl = gdat.mocknumbpnts.size 
    
        if gdat.mockspatdisttype == None:
            gdat.mockspatdisttype = ['unif' for l in gdat.mockindxpopl]
        
        if gdat.mockfluxdisttype == None:
            gdat.mockfluxdisttype = ['powr' for l in gdat.mockindxpopl]
       
        # fix the hyperparameters
        if gdat.mockfluxdistslop == None:
            gdat.mockfluxdistslop = zeros(gdat.mocknumbpopl) + 2.
        
        if gdat.mockfluxdistslop == None:
            gdat.mockfluxdistslop = zeros(gdat.mocknumbpopl) + 2.
        
        if gdat.mockfluxdistbrek == None:
            gdat.mockfluxdistbrek = zeros(gdat.mocknumbpopl) + 2.
        
        if gdat.mockfluxdistsloplowr == None:
            gdat.mockfluxdistsloplowr = zeros(gdat.mocknumbpopl) + 1.
        
        if gdat.mockfluxdistslopuppr == None:
            gdat.mockfluxdistslopuppr = zeros(gdat.mocknumbpopl) + 2.
        
        if gdat.mocksinddistmean == None:
            gdat.mocksinddistmean = zeros(gdat.mocknumbpopl) + 2.
        
        if gdat.mocksinddiststdv == None:
            gdat.mocksinddiststdv = zeros(gdat.mocknumbpopl) + 0.5
        
        gdat.mockfixp = empty(gdat.mocknumbfixp)
        for k in gdat.mockindxfixp:
            if k in gdat.mockindxfixpnumbpnts:
                varb = gdat.mocknumbpnts[k]
            else:
                varb = rand()
            gdat.mockfixp[k] = icdf_fixp(gdat, varb, k, mock=True)
        
        gdat.mockindxpnts = []
        for l in gdat.mockindxpopl: 
            gdat.mockindxpnts.append(arange(gdat.mocknumbpnts[l]))
        gdat.mocknumbpntstotl = sum(gdat.mocknumbpnts)
        gdat.mockindxpntstotl = arange(gdat.mocknumbpntstotl)

        gdat.mockcnts = [[] for l in gdat.mockindxpopl]
        gdat.mocklgal = [[] for l in gdat.mockindxpopl]
        gdat.mockbgal = [[] for l in gdat.mockindxpopl]
        gdat.mockgang = [[] for l in gdat.mockindxpopl]
        gdat.mockaang = [[] for l in gdat.mockindxpopl]
        gdat.mockspec = [[] for l in gdat.mockindxpopl]
        gdat.mocknumbspep = retr_numbspep(gdat.mockspectype)
        gdat.mockspep = [empty((gdat.mocknumbpnts[l], gdat.mocknumbspep[l])) for l in gdat.mockindxpopl]
        for l in gdat.mockindxpopl:
            if gdat.mockspatdisttype[l] == 'unif':
                gdat.mocklgal[l] = icdf_self(rand(gdat.mocknumbpnts[l]), -gdat.maxmgangmodl, 2. * gdat.maxmgangmodl)
                gdat.mockbgal[l] = icdf_self(rand(gdat.mocknumbpnts[l]), -gdat.maxmgangmodl, 2. * gdat.maxmgangmodl) 
            if gdat.mockspatdisttype[l] == 'disc':
                gdat.mockbgal[l] = icdf_logt(rand(gdat.mocknumbpnts[l]), gdat.minmgang, gdat.factgang) * choice(array([1., -1.]), size=gdat.mocknumbpnts[l])
                gdat.mocklgal[l] = icdf_self(rand(gdat.mocknumbpnts[l]), -gdat.maxmgangmodl, 2. * gdat.maxmgangmodl) 
            if gdat.mockspatdisttype[l] == 'gang':
                gdat.mockgang[l] = icdf_logt(rand(gdat.mocknumbpnts[l]), gdat.minmgang, gdat.factgang)
                gdat.mockaang[l] = icdf_self(rand(gdat.mocknumbpnts[l]), 0., 2. * pi)
                gdat.mocklgal[l], gdat.mockbgal[l] = retr_lgalbgal(gdat.mockgang[l], gdat.mockaang[l])
            
            gdat.mockspec[l] = empty((gdat.numbener, gdat.mocknumbpnts[l]))
            if gdat.mockfluxdisttype[l] == 'powr':
                gdat.mockspec[l][gdat.indxenerfluxdist[0], :] = icdf_flux_powr(rand(gdat.mocknumbpnts[l]), gdat.mockminmflux, gdat.maxmflux, \
                                                                                                                            gdat.mockfixp[gdat.mockindxfixpfluxdistslop[l]])
            if gdat.mockfluxdisttype[l] == 'brok':
                gdat.mockspec[l][gdat.indxenerfluxdist[0], :] = icdf_flux_brok(rand(gdat.mocknumbpnts[l]), gdat.mockminmflux, gdat.maxmflux, gdat.mockfluxdistbrek[l], \
                                                                                                                     gdat.mockfluxdistsloplowr[l], gdat.mockfluxdistslopuppr[l])
            if gdat.numbener > 1:
                # spectral parameters
                gdat.mockspep[l][:, 0] = icdf_gaus(rand(gdat.mocknumbpnts[l]), gdat.mocksinddistmean[l], gdat.mocksinddiststdv[l])
                if gdat.mockspectype[l] == 'curv':
                    gdat.mockspep[l][:, 1] = icdf_gaus(rand(gdat.mocknumbpnts[l]), gdat.mockcurvdistmean[l], gdat.mockcurvdiststdv[l])
                
                if gdat.mockspectype[l] == 'expo':
                    gdat.mockspep[l][:, 1] = icdf_logt(rand(gdat.mocknumbpnts[l]), gdat.minmener, gdat.factener)
            
            # spectra
            gdat.mockspec[l] = retr_spec(gdat, gdat.mockspec[l][gdat.indxenerfluxdist[0], :], spep=gdat.mockspep[l], spectype=gdat.mockspectype[l])
               
            if gdat.verbtype > 1:
                if gdat.numbener > 1:
                    print 'mockspectype[l]'
                    print gdat.mockspectype[l]
                    print 'mockspep[l]'
                    print gdat.mockspep[l]
                print 'mockspec[l]'
                print gdat.mockspec[l]
           
            if gdat.pixltype != 'unbd':
                indxpixltemp = retr_indxpixl(gdat, gdat.mockbgal[l], gdat.mocklgal[l])
                gdat.mockcnts[l] = gdat.mockspec[l][:, :, None] * gdat.expo[:, indxpixltemp, :]
                if gdat.enerbins:
                    gdat.mockcnts[l] *= gdat.diffener[:, None, None]
        # mock mean count map
        if gdat.pixltype != 'unbd':
            if gdat.pntstype == 'lght':
                mockpntsflux = retr_pntsflux(gdat, concatenate(gdat.mocklgal), concatenate(gdat.mockbgal), concatenate(gdat.mockspec, axis=1), \
                                                                                                            gdat.truepsfp, gdat.truepsfntype, gdat.mockvarioaxi, evalcirc=True)
                if gdat.backemis:
                    gdat.mockmodlflux = retr_rofi_flux(gdat, gdat.mockfixp[gdat.mockindxfixpbacp], mockpntsflux, gdat.indxcube)
                else:
                    gdat.mockmodlflux = mockpntsflux
                gdat.mockmodlcnts = gdat.mockmodlflux * gdat.expo * gdat.apix * gdat.diffener[:, None, None] # [1]
            if gdat.pntstype == 'lens':
                # create the source object
                gdat.truesourtype = 'Gaussian'
                gdat.truelenstype = 'SIE'
                #gdat.mockfluxsour = 3631. * 1e-23 * 0.624 * 10**(-0.4 * (-20.)) / 0.1 # ph / cm^2 / s
                
                gdat.mocksourobjt = franlens.Source(gdat.truesourtype, gdat.mockfixp[gdat.mockindxfixplgalsour], \
                                                                       gdat.mockfixp[gdat.mockindxfixpbgalsour], \
                                                                       gdat.mockfixp[gdat.mockindxfixpfluxsour], \
                                                                       gdat.mockfixp[gdat.mockindxfixpsizesour], \
                                                                       gdat.mockfixp[gdat.mockindxfixpratisour], \
                                                                       gdat.mockfixp[gdat.mockindxfixpanglsour])

                # background image without lensing
                lensobjttemp = franlens.LensModel(gdat.truelenstype, gdat.mockfixp[gdat.mockindxfixplgalhost], \
                                                                     gdat.mockfixp[gdat.mockindxfixpbgalhost], \
                                                                     gdat.mockfixp[gdat.mockindxfixpellphost], \
                                                                     gdat.mockfixp[gdat.mockindxfixpanglhost], \
                                                                     gdat.mockfixp[gdat.mockindxfixpsherhost], \
                                                                     gdat.mockfixp[gdat.mockindxfixpsanghost], 0.)
                
                gdat.mockmodlfluxraww = zeros((gdat.numbener, gdat.numbpixl, gdat.numbevtt))
                gdat.mockmodlfluxraww[0, :, 0], gdat.mockdeflraww = franlens.macro_only_image(gdat.lgalgrid, gdat.bgalgrid, gdat.mocksourobjt, lensobjttemp, gdat.truepsfp[0])
                gdat.mockmodlcntsraww = gdat.mockmodlfluxraww * gdat.expo * gdat.apix
                if gdat.enerbins:
                    gdat.mockmodlcntsraww *= gdat.diffener[:, None, None]
                for j in gdat.indxpixl:
                    gdat.mockmodlcntsraww[0, j, 0] = poisson(gdat.mockmodlcntsraww[0, j, 0])
                
                gdat.mockmodlflux = zeros((gdat.numbener, gdat.numbpixl, gdat.numbevtt))
                
                # construct the lens object
                gdat.mocklistlensobjt = []
                for l in gdat.mockindxpopl:
                    for k in range(gdat.mocknumbpnts[0]):
                        gdat.mocklistlensobjt.append(franlens.LensModel(gdat.truelenstype, gdat.mocklgal[l][k], gdat.mockbgal[l][k], 0., 0., 0., 0., gdat.mockspec[l][0, k]))
                            
                gdat.mocklistlensobjt.append(franlens.LensModel(gdat.truelenstype, gdat.mockfixp[gdat.mockindxfixplgalhost], \
                                                                                   gdat.mockfixp[gdat.mockindxfixpbgalhost], \
                                                                                   gdat.mockfixp[gdat.mockindxfixpellphost], \
                                                                                   gdat.mockfixp[gdat.mockindxfixpanglhost], \
                                                                                   gdat.mockfixp[gdat.mockindxfixpsherhost], \
                                                                                   gdat.mockfixp[gdat.mockindxfixpsanghost], \
                                                                                   gdat.mockfixp[gdat.mockindxfixpbeinhost]))

                # temp
                gdat.mockmodlflux[0, :, 0], gdat.mockdefl = franlens.macro_only_image(gdat.lgalgrid, gdat.bgalgrid, \
                                                                                                                   gdat.mocksourobjt, gdat.mocklistlensobjt, gdat.truepsfp[0])
            
            gdat.mockmodlcnts = gdat.mockmodlflux * gdat.expo * gdat.apix
            if gdat.enerbins:
                gdat.mockmodlcnts *= gdat.diffener[:, None, None]
        if gdat.pixltype == 'unbd':
            gdat.numbdims = 2
            gdat.mockdatacnts = zeros((gdat.numbener, gdat.numbdatasamp, gdat.numbevtt, gdat.numbdims))
            mocklgaltemp = concatenate(gdat.mocklgal)
            mockbgaltemp = concatenate(gdat.mockbgal)
            mockfluxtemp = concatenate(gdat.mockspec)[gdat.indxenerfluxdist[0], :]
            probpntsflux = mockfluxtemp / sum(mockfluxtemp)

            gdat.truepsfncdfn = roll(cumsum(gdat.truepsfn, axis=1), 1)[0, :, 0]
            gdat.truepsfncdfn[0] = 0.
            gdat.truepsfncdfn /= amax(gdat.truepsfncdfn)
            truepsfnicdfintp = interp1d(gdat.truepsfncdfn, gdat.binsangl)

            if gdat.mockindxpntstotl.size > 0:
                for k in gdat.indxdatasamp:
                    indxpntsthis = choice(gdat.mockindxpntstotl, p=probpntsflux) 
                    radi = truepsfnicdfintp(rand())
                    aang = rand() * 2. * pi
                    gdat.mockdatacnts[0, k, 0, 0] = mocklgaltemp[indxpntsthis] + radi * sin(aang)
                    gdat.mockdatacnts[0, k, 0, 1] = mockbgaltemp[indxpntsthis] + radi * cos(aang)
        else:
            gdat.mockdatacnts = zeros((gdat.numbener, gdat.numbpixl, gdat.numbevtt))
            for i in gdat.indxener:
                for j in gdat.indxpixl:
                    for m in gdat.indxevtt:
                        gdat.mockdatacnts[i, j, m] = poisson(gdat.mockmodlcnts[i, j, m])

    # final setup
    setpfinl(gdat, True) 

    if gdat.makeplot:
        if gdat.pixltype == 'cart':
            figr, axis, path = init_figr(gdat, 'datacntspeak', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
            imag = retr_imag(gdat, axis, gdat.datacnts, i, m, vmin=gdat.minmdatacnts[i], vmax=gdat.maxmdatacnts[i], scal=gdat.scalmaps)
            make_cbar(gdat, axis, imag, i, tick=gdat.tickdatacnts[i, :], labl=gdat.labldatacnts[i, :])
            #supr_fram(gdat, None, axis, i, l, True)
            
            # temp
            #axis.text(0.2, 0.95, '%0.7g %0.7g %0.7g' % (gdat.anglcatlrttr, rad2deg(gdat.lgalcntr), rad2deg(gdat.bgalcntr)), ha='center', va='center', transform=axis.transAxes)
            axis.scatter(gdat.anglfact * gdat.lgalcart[gdat.indxxaximaxm], gdat.anglfact * gdat.bgalcart[gdat.indxyaximaxm], alpha=0.3, s=20, edgecolor='none')
            
            plt.tight_layout()
            plt.savefig(path)
            plt.close(figr)
    
        for i in gdat.indxener:
            for m in gdat.indxevtt:
    
                figr, axis, path = init_figr(gdat, 'datacnts', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
                if gdat.pixltype != 'unbd':
                    imag = retr_imag(gdat, axis, gdat.datacnts, i, m, vmin=gdat.minmdatacnts[i], vmax=gdat.maxmdatacnts[i], scal=gdat.scalmaps)
                    make_cbar(gdat, axis, imag, i, tick=gdat.tickdatacnts[i, :], labl=gdat.labldatacnts[i, :])
                else:
                    imag = retr_scat(gdat, axis, gdat.datacnts, i, m)
                supr_fram(gdat, None, axis, i, l, True)
                plt.tight_layout()
                plt.savefig(path)
                plt.close(figr)
            
                if gdat.pixltype != 'unbd':
                    figr, axis, path = init_figr(gdat, 'expo', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
                    imag = retr_imag(gdat, axis, gdat.expo, i, m)
                    make_cbar(gdat, axis, imag, i)
                    plt.tight_layout()
                    plt.savefig(path)
                    plt.close(figr)
            
                    figr, axis, path = init_figr(gdat, 'backcntstotl', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
                    imag = retr_imag(gdat, axis, gdat.backcntstotl, i, m, vmin=gdat.minmdatacnts[i], vmax=gdat.maxmdatacnts[i], scal=gdat.scalmaps)
                    make_cbar(gdat, axis, imag, i, tick=gdat.tickdatacnts[i, :], labl=gdat.labldatacnts[i, :])
                    plt.tight_layout()
                    plt.savefig(path)
                    plt.close(figr)
        
                    for c in gdat.indxback:
                        figr, axis, path = init_figr(gdat, 'backcnts', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
                        imag = retr_imag(gdat, axis, gdat.backcnts[c], i, m, vmin=gdat.minmdatacnts[i], vmax=gdat.maxmdatacnts[i], scal=gdat.scalmaps)
                        make_cbar(gdat, axis, imag, i, tick=gdat.tickdatacnts[i, :], labl=gdat.labldatacnts[i, :])
                        plt.tight_layout()
                        plt.savefig(path)
                        plt.close(figr)
        
                    figr, axis, path = init_figr(gdat, 'diffcntstotl', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
                    imag = retr_imag(gdat, axis, gdat.datacnts - gdat.backcntstotl, i, m, vmin=gdat.minmdatacnts[i], vmax=gdat.maxmdatacnts[i], scal=gdat.scalmaps)
                    make_cbar(gdat, axis, imag, i, tick=gdat.tickdatacnts[i, :], labl=gdat.labldatacnts[i, :])
                    plt.tight_layout()
                    plt.savefig(path)
                    plt.close(figr)
    
                if gdat.pntstype == 'lens':
                    figr, axis, path = init_figr(gdat, 'mockmodlcntsraww', indxenerplot=i, indxevttplot=m, pathfold=gdat.pathinit)
                    imag = retr_imag(gdat, axis, gdat.mockmodlcntsraww, 0, 0, vmin=gdat.minmdatacnts[i], vmax=gdat.maxmdatacnts[i], scal=gdat.scalmaps)
                    make_cbar(gdat, axis, imag, 0, tick=gdat.tickdatacnts[i, :], labl=gdat.labldatacnts[i, :])
                    plt.tight_layout()
                    plt.savefig(path)
                    plt.close(figr)
    
                    plot_defl(gdat, gdat.mockdefl)
    
    # write the list of arguments to file
    fram = inspect.currentframe()
    listargs, temp, temp, listargsvals = inspect.getargvalues(fram)
    fileargs = open(gdat.pathoutp + 'args.txt', 'w')
    fileargs.write('PCAT call arguments')
    for args in listargs:
        fileargs.write('%s = %s\n' % (args, listargsvals[args]))
    fileargs.close()

    # start the timer
    gdat.timerealtotl = time.time()
    gdat.timeproctotl = time.clock()
   
    if gdat.verbtype > 1:
        print 'minmflux'
        print gdat.minmflux
        print 'maxmflux'
        print gdat.maxmflux
        if gdat.pixltype != 'unbd':
            print 'minmcnts'
            print gdat.minmcnts
            print 'maxmcnts'
            print gdat.maxmcnts
        print 'indxsampnumbpnts: ', gdat.indxfixpnumbpnts
        print 'indxsampmeanpnts: ', gdat.indxfixpmeanpnts
        print 'indxsampfluxdistslop: ', gdat.indxfixpfluxdistslop
        print 'indxsampfluxdistbrek: ', gdat.indxfixpfluxdistbrek
        print 'indxsampfluxdistsloplowr: ', gdat.indxfixpfluxdistsloplowr
        print 'indxsampfluxdistslopuppr: ', gdat.indxfixpfluxdistslopuppr
        print 'indxsamppsfp: ', gdat.indxfixppsfp
        print 'indxsampbacp: '
        print gdat.indxfixpbacp
        if gdat.evalcirc:
            print 'maxmangleval'
            print gdat.anglfact * gdat.maxmangleval, ' ', gdat.strganglunit
        print
        if gdat.trueinfo:
            print 'Truth information'
            print 'truelgal'
            for l in gdat.indxpopl:
                print gdat.truelgal[l]
            print 'truebgal'
            for l in gdat.indxpopl:
                print gdat.truebgal[l]
            print 'truespec'
            for l in gdat.indxpopl:
                print gdat.truespec[l]
            print 'truepsfp'
            print gdat.truepsfp
            print
            
            if False:
                if gdat.datatype == 'mock':
                    print 'Mock data'
                    for attr, valu in gdat.__dict__.iteritems():
                        if attr.startswith('mock'):
                            print attr
                            print valu
                            print

    # make initial plots
    if gdat.makeplot:
        #plot_3fgl_thrs(gdat)
        if gdat.pixltype != 'unbd':
            plot_datacntshist(gdat)
            if gdat.pntstype == 'lght':
                plot_indxprox(gdat)
        #if gdat.exprtype == 'ferm':
        #    plot_fgl3(gdat)
        # temp
        #plot_intr()
        #plot_plot()
        #plot_king(gdat)
        if gdat.evalcirc:
            plot_eval(gdat)
        #if gdat.datatype == 'mock':
        #    plot_pntsdiff()

    if gdat.verbtype > 0:
        print 'Sampling...'
    
    if gdat.verbtype > 1:
        tdpy.util.show_memo(gdat, 'gdat')

    # lock the global object againts any future modifications
    gdat.lockmodi()

    gdat.timereal = zeros(gdat.numbproc)
    gdat.timeproc = zeros(gdat.numbproc)
    if gdat.numbproc == 1:
        gridchan = [work(gdat, 0)]
    else:
        if gdat.verbtype > 0:
            print 'Forking the sampler...'

        # process lock for simultaneous plotting
        gdat.lock = mp.Manager().Lock()

        # process pool
        pool = mp.Pool(gdat.numbproc)
        
        # spawn the processes
        workpart = functools.partial(work, gdat)
        gridchan = pool.map(workpart, gdat.indxproc)

        pool.close()
        pool.join()

    if gdat.verbtype > 0:
        print 'Accumulating samples from all processes...'
        timeinit = gdat.functime()

    # unlock the global object
    gdat.unlkmodi()
    
    # parse the sample bundle
    gdat.listsamp = zeros((gdat.numbsamp, gdat.numbproc, gdat.numbpara))
    gdat.listsampvarb = zeros((gdat.numbsamp, gdat.numbproc, gdat.numbpara))
    gdat.listindxprop = zeros((gdat.numbswep, gdat.numbproc))
    gdat.listchrollik = zeros((gdat.numbswep, gdat.numbproc, gdat.numbchrollik))
    gdat.listchrototl = zeros((gdat.numbswep, gdat.numbproc, gdat.numbchrototl))
    gdat.listllik = zeros((gdat.numbsamp, gdat.numbproc))
    gdat.listlpri = zeros((gdat.numbsamp, gdat.numbproc))
    gdat.listaccp = zeros((gdat.numbswep, gdat.numbproc))
    gdat.listmodlcnts = zeros((gdat.numbsamp, gdat.numbproc, gdat.numbpixlsave))
    gdat.listpntsfluxmean = zeros((gdat.numbsamp, gdat.numbproc, gdat.numbener))
    listindxpntsfulltemp = []
    gdat.listindxparamodi = zeros((gdat.numbswep, gdat.numbproc), dtype=int) - 1
    gdat.listauxipara = [empty((gdat.numbswep, gdat.numbproc, gdat.numbcompcolr[l])) for l in gdat.indxpopl]
    gdat.listlaccfact = empty((gdat.numbswep, gdat.numbproc))
    gdat.listnumbpair = empty((gdat.numbswep, gdat.numbproc, 2))
    gdat.listjcbnfact = empty((gdat.numbswep, gdat.numbproc))
    gdat.listcombfact = empty((gdat.numbswep, gdat.numbproc))
    gdat.listboolreje = empty((gdat.numbswep, gdat.numbproc))
    gdat.listdeltllik = empty((gdat.numbswep, gdat.numbproc))
    gdat.listdeltlpri = empty((gdat.numbswep, gdat.numbproc))
    gdat.listmemoresi = empty((gdat.numbsamp, gdat.numbproc))
    gdat.listerrr = empty((gdat.numbsamp, gdat.numbproc, gdat.numbener, gdat.numbevtt))
    gdat.listerrrfrac = empty((gdat.numbsamp, gdat.numbproc, gdat.numbener, gdat.numbevtt))
    gdat.maxmllikswep = empty(gdat.numbproc)
    gdat.indxswepmaxmllik = empty(gdat.numbproc, dtype=int)
    gdat.sampvarbmaxmllik = empty((gdat.numbproc, gdat.numbpara))
    gdat.maxmlposswep = empty(gdat.numbproc)
    gdat.indxswepmaxmlpos = empty(gdat.numbproc, dtype=int)
    gdat.sampvarbmaxmlpos = empty((gdat.numbproc, gdat.numbpara))
    for k in gdat.indxproc:
        listchan = gridchan[k]
        gdat.listsamp[:, k, :] = listchan[0]
        gdat.listsampvarb[:, k, :] = listchan[1]
        gdat.listindxprop[:, k] = listchan[2]
        gdat.listchrototl[:, k, :] = listchan[3]
        gdat.listllik[:, k] = listchan[4]
        gdat.listlpri[:, k] = listchan[5]
        gdat.listaccp[:, k] = listchan[6]
        gdat.listmodlcnts[:, k, :] = listchan[7]    
        listindxpntsfulltemp.append(listchan[8])
        gdat.listindxparamodi[:, k] = listchan[9]
        for l in gdat.indxpopl:
            gdat.listauxipara[l][:, k, :] = listchan[10][l]
        gdat.listlaccfact[:, k] = listchan[11]
        gdat.listnumbpair[:, k, :] = listchan[12]
        gdat.listjcbnfact[:, k] = listchan[13]
        gdat.listcombfact[:, k] = listchan[14]
        gdat.listpntsfluxmean[:, k, :] = listchan[15]
        gdat.listchrollik[:, k, :] = listchan[16]
        gdat.listboolreje[:, k] = listchan[17]
        gdat.listdeltllik[:, k] = listchan[18]
        gdat.listdeltlpri[:, k] = listchan[19]
        gdat.listmemoresi[:, k] = listchan[20]
        gdat.maxmllikswep[k] = listchan[21]
        gdat.indxswepmaxmllik[k] = listchan[22]
        gdat.sampvarbmaxmllik[k, :] = listchan[23]
        gdat.maxmllikswep[k] = listchan[24]
        gdat.indxswepmaxmlpos[k] = listchan[25]
        gdat.sampvarbmaxmlpos[k, :] = listchan[26]
        gdat.listerrr[:, k, :, :] = listchan[27]
        gdat.listerrrfrac[:, k, :, :] = listchan[28]
        gdat.timereal[k] = gridchan[k][29]
        gdat.timeproc[k] = gridchan[k][30]

    # merge samples from processes
    gdat.listindxprop = gdat.listindxprop.reshape((gdat.numbsweptotl, -1))
    gdat.listchrototl = gdat.listchrototl.reshape((gdat.numbsweptotl, gdat.numbchrototl)) 
    gdat.listaccp = gdat.listaccp.flatten()
    gdat.listindxparamodi = gdat.listindxparamodi.flatten()
    # temp
    for l in gdat.indxpopl:
        gdat.listauxipara[l] = gdat.listauxipara[l].reshape((gdat.numbsweptotl, gdat.numbcompcolr[l]))
    #shap = listauxipara.shape
    #shap = [shap[0] * shap[1], shap[2:]]
    #listauxipara = listauxipara.reshape(shap)
    gdat.listlaccfact = gdat.listlaccfact.reshape(gdat.numbsweptotl)
    gdat.listnumbpair = gdat.listnumbpair.reshape((gdat.numbsweptotl, 2))
    gdat.listjcbnfact = gdat.listjcbnfact.reshape(gdat.numbsweptotl)
    gdat.listcombfact = gdat.listcombfact.reshape(gdat.numbsweptotl)
    gdat.listchrollik = gdat.listchrollik.reshape((gdat.numbsweptotl, gdat.numbchrollik)) 
    gdat.listboolreje = gdat.listboolreje.reshape(gdat.numbsweptotl)
    gdat.listdeltllik = gdat.listdeltllik.reshape(gdat.numbsweptotl)
    gdat.listdeltlpri = gdat.listdeltlpri.reshape(gdat.numbsweptotl)
    gdat.listerrr = gdat.listerrr.reshape((gdat.numbsamptotl, gdat.numbener, gdat.numbevtt))
    gdat.listerrrfrac = gdat.listerrrfrac.reshape((gdat.numbsamptotl, gdat.numbener, gdat.numbevtt))
    gdat.listsamp = gdat.listsamp.reshape(gdat.numbsamptotl, -1)
    gdat.listpntsfluxmean = gdat.listpntsfluxmean.reshape(gdat.numbsamptotl, gdat.numbener)
   
    gdat.listindxpntsfull = []
    for j in gdat.indxsamp:      
        for k in gdat.indxproc:
            gdat.listindxpntsfull.append(listindxpntsfulltemp[k][j])

    if gdat.pixltype != 'unbd':
        # compute the approximation error as a fraction of the counts expected from the dimmest PS for the mean exposure
        gdat.listerrrfracdimm = gdat.listerrr / (gdat.minmflux * mean(gdat.expo, 1)[None, :, :])
        if gdat.enerbins:
            gdat.listerrrfracdimm /= gdat.diffener[None, :, None] 

    # correct the likelihoods for the constant data dependent factorial
    llikoffs = sum(sp.special.gammaln(gdat.datacnts + 1))
    gdat.listllik -= llikoffs
    gdat.maxmllikswep -= llikoffs
    gdat.maxmlposswep -= llikoffs
    
    # find the maximum likelihood and posterior over the chains
    gdat.indxprocmaxmllik = argmax(gdat.maxmllikswep)
    gdat.maxmllikswep = gdat.maxmllikswep[gdat.indxprocmaxmllik]
    gdat.indxswepmaxmllik = gdat.indxprocmaxmllik * gdat.numbsamp + gdat.indxswepmaxmllik[gdat.indxprocmaxmllik]
    gdat.sampvarbmaxmllik = gdat.sampvarbmaxmllik[gdat.indxprocmaxmllik, :]
    
    gdat.indxprocmaxmlpos = argmax(gdat.maxmlposswep)
    gdat.maxmlposswep = gdat.maxmlposswep[gdat.indxprocmaxmlpos]
    gdat.indxswepmaxmlpos = gdat.indxswepmaxmlpos[gdat.indxprocmaxmlpos]
    gdat.sampvarbmaxmlpos = gdat.sampvarbmaxmlpos[gdat.indxprocmaxmlpos, :]

    # calculate log-evidence using the harmonic mean estimator
    if gdat.verbtype > 0:
        print 'Estimating the Bayesian evidence...'
        timeinit = gdat.functime()
    
    if gdat.regulevi:
        # regularize the harmonic mean estimator
        ## get an ellipse around the median posterior 
        gdat.elpscntr = percentile(listsamp, 50., axis=0)
        thissamp = rand(gdat.numbpara) * 1e-6
        stdvpara = ones(gdat.numbpara) * 1e-6
        limtpara = zeros((2, gdat.numbpara))
        limtpara[1, :] = 1.
        ## find the samples that lie inside the ellipse
        elpsaxis, minmfunc = tdpy.util.minm(thissamp, retr_elpsfrac, stdvpara=stdvpara, limtpara=limtpara, tolrfunc=1e-6, verbtype=gdat.verbtype, optiprop=True)
        lnorregu = -0.5 * gdat.numbpara * log(pi) + sp.special.gammaln(0.5 * gdat.numbpara + 1.) - sum(elpsaxis)
        indxsampregu = 0
        listlliktemp = listllik[indxsampregu]
    else:
        listlliktemp = gdat.listllik
    gdat.levi = retr_levi(listlliktemp)
    
    if gdat.verbtype > 0:
        timefinl = gdat.functime()
        print 'Done in %.3g seconds.' % (timefinl - timeinit)

    # calculate relative entropy
    gdat.info = retr_info(gdat.listllik, gdat.levi)

    # collect posterior samples from the processes
    ## PSF parameters
    gdat.listfixp = gdat.listsampvarb[:, :, gdat.indxfixp].reshape(gdat.numbsamptotl, -1)

    ## PS parameters
    gdat.listlgal = [[] for l in gdat.indxpopl]
    gdat.listbgal = [[] for l in gdat.indxpopl]
    gdat.listspec = [[] for l in gdat.indxpopl]
    if gdat.numbener > 1:
        gdat.listspep = [[] for l in gdat.indxpopl]
    for k in gdat.indxproc:
        for j in gdat.indxsamp:            
            n = k * gdat.numbsamp + j
            for l in gdat.indxpopl:
                indxsamplgal, indxsampbgal, indxsampspec, indxsampspep, indxsampcompcolr = retr_indx(gdat, gdat.listindxpntsfull[n])
                gdat.listlgal[l].append(gdat.listsampvarb[j, k, indxsamplgal[l]])
                gdat.listbgal[l].append(gdat.listsampvarb[j, k, indxsampbgal[l]])
                gdat.listspec[l].append(gdat.listsampvarb[j, k, indxsampspec[l]])
                if gdat.numbener > 1:
                    gdat.listspep[l].append(gdat.listsampvarb[j, k, indxsampspep[l]])
                
    # calculate the radial and azimuthal position 
    gdat.listgang = [[] for l in gdat.indxpopl]
    gdat.listaang = [[] for l in gdat.indxpopl]
    for l in gdat.indxpopl:
        for n in gdat.indxsamptotl:
            gdat.listgang[l].append(retr_gang(gdat.listlgal[l][n], gdat.listbgal[l][n]))
            gdat.listaang[l].append(retr_aang(gdat.listlgal[l][n], gdat.listbgal[l][n]))

    ## binned PS parameters
    if gdat.verbtype > 0:
        print 'Binning the probabilistic catalog...'
        timeinit = gdat.functime()
    
    gdat.listlgalhist = empty((gdat.numbsamptotl, gdat.numbpopl, gdat.numblgal))
    gdat.listbgalhist = empty((gdat.numbsamptotl, gdat.numbpopl, gdat.numbbgal))
    gdat.listspechist = empty((gdat.numbsamptotl, gdat.numbpopl, gdat.numbfluxplot, gdat.numbener))
    gdat.listspephist = []
    for l in gdat.indxpopl:
        gdat.listspephist.append(empty((gdat.numbsamptotl, gdat.numbspep[l], gdat.numbspepbins)))
    gdat.listganghist = empty((gdat.numbsamptotl, gdat.numbpopl, gdat.numbgang))
    gdat.listaanghist = empty((gdat.numbsamptotl, gdat.numbpopl, gdat.numbaang))
    for n in gdat.indxsamptotl: 
        for l in gdat.indxpopl:
            # find the indices of the model PSs that are in the comparison area
            indxmodlpntscomp = retr_indxpntscomp(gdat, gdat.listlgal[l][n], gdat.listbgal[l][n])
    
            gdat.listlgalhist[n, l, :] = histogram(gdat.listlgal[l][n][indxmodlpntscomp], gdat.binslgal)[0]
            gdat.listbgalhist[n, l, :] = histogram(gdat.listbgal[l][n][indxmodlpntscomp], gdat.binsbgal)[0]
            for i in gdat.indxener:
                gdat.listspechist[n, l, :, i] = histogram(gdat.listspec[l][n][i, indxmodlpntscomp], gdat.binsspecplot[i, :])[0]
            if gdat.numbener > 1:
                for p in gdat.indxspep[l]:
                    gdat.listspephist[l][n, p, :] = histogram(gdat.listspep[l][n][indxmodlpntscomp, p], gdat.binsspep[:, p])[0]
            gdat.listganghist[n, l, :] = histogram(gdat.listgang[l][n][indxmodlpntscomp], gdat.binsgang)[0]
            gdat.listaanghist[n, l, :] = histogram(gdat.listaang[l][n][indxmodlpntscomp], gdat.binsaang)[0]
    
    gdat.pntsprob = zeros((gdat.numbpopl, gdat.numbbgalpntsprob, gdat.numblgalpntsprob, gdat.numbfluxplot))
    for l in gdat.indxpopl:
        temparry = concatenate([gdat.listlgal[l][n] for n in gdat.indxsamptotl])
        temp = empty((len(temparry), 3))
        temp[:, 0] = temparry
        temp[:, 1] = concatenate([gdat.listbgal[l][n] for n in gdat.indxsamptotl])
        temp[:, 2] = concatenate([gdat.listspec[l][n][gdat.indxenerfluxdist[0], :] for n in gdat.indxsamptotl])
        gdat.pntsprob[l, :, :, :] = histogramdd(temp, bins=(gdat.binslgalpntsprob, gdat.binsbgalpntsprob, gdat.binsfluxplot))[0]

    if gdat.verbtype > 0:
        timefinl = gdat.functime()
        print 'Done in %.3g seconds.' % (timefinl - timeinit)

    # Gelman-Rubin test
    gdat.gmrbstat = zeros(gdat.numbpixlsave)
    if gdat.numbproc > 1:
        if gdat.verbtype > 0:
            print 'Computing the Gelman-Rubin TS...'
            timeinit = gdat.functime()
        for n in range(gdat.numbpixlsave):
            gdat.gmrbstat[n] = tdpy.mcmc.gmrb_test(gdat.listmodlcnts[:, :, n])
        if gdat.verbtype > 0:
            timefinl = gdat.functime()
            print 'Done in %.3g seconds.' % (timefinl - timeinit)

    # calculate the autocorrelation of the chains
    if gdat.verbtype > 0:
        print 'Computing the autocorrelation of the chains...'
        timeinit = gdat.functime()
   
    gdat.atcr, gdat.timeatcr = tdpy.mcmc.retr_timeatcr(gdat.listmodlcnts, verbtype=gdat.verbtype, maxmatcr=True)

    if gdat.timeatcr == 0.:
        print 'Autocorrelation time estimation failed.'

    if gdat.verbtype > 0:
        timefinl = gdat.functime()
        print 'Done in %.3g seconds.' % (timefinl - timeinit)

    # write the PCAT output to disc
    if gdat.verbtype > 0:
        print 'Writing the PCAT output of size to %s...' % pathpcat
    
    shel = shelve.open(pathpcat, 'n')
    for attr, valu in locals().iteritems():
        if attr == 'gdat':
            shel[attr] = valu
    shel.close()

    if gdat.makeplot:
        plot_post(pathpcat, verbtype=gdat.verbtype, makeanim=gdat.makeanim)

    gdat.timerealtotl = time.time() - gdat.timerealtotl
    gdat.timeproctotl = time.clock() - gdat.timeproctotl
     
    # output dictionary
    dictpcat = dict()
    for attr, valu in gdat.__dict__.iteritems():
        dictpcat[attr] = valu

    if gdat.verbtype > 0:
        for k in gdat.indxproc:
            print 'Process %d has been completed in %d real seconds, %d CPU seconds.' % (k, gdat.timereal[k], gdat.timeproc[k])
        print 'PCAT has run in %d real seconds, %d CPU seconds.' % (gdat.timerealtotl, gdat.timeproctotl)
        print 'The ensemble of catalogs is at ' + pathpcat
        if gdat.makeplot:
            print 'The plots are in ' + gdat.pathplot
        
    if os.environ["TERM"] == 'screen':
        sys.stdout.close()
    
    return gridchan, dictpcat
    
    
def plot_samp(gdat, gdatmodi):

    for l in gdat.indxpopl:
        gdatmodi.indxmodlpntscomp[l] = retr_indxpntscomp(gdat, gdatmodi.thissampvarb[gdatmodi.thisindxsamplgal[l]], gdatmodi.thissampvarb[gdatmodi.thisindxsampbgal[l]])

    if gdat.backemis:
        gdatmodi.thismodlflux = retr_rofi_flux(gdat, gdatmodi.thissampvarb[gdat.indxfixpbacp], gdatmodi.thispntsflux, gdat.indxcube)
    else:
        gdatmodi.thismodlflux = gdatmodi.thispntsflux

    if gdat.pixltype != 'unbd':
        gdatmodi.thismodlcnts = gdatmodi.thismodlflux * gdat.expo * gdat.apix
        if gdat.enerbins:
            gdatmodi.thismodlcnts *= gdat.diffener[:, None, None]
        gdatmodi.thisresicnts = gdat.datacnts - gdatmodi.thismodlcnts
   
    if gdat.pntstype == 'lght':
        # PSF radial profile
        if gdat.varioaxi:
            for p in gdat.indxoaxi:
                gdatmodi.thispsfn[:, :, :, p] = gdatmodi.thispsfnintp[p](gdat.binsangl)
        else:
            gdatmodi.thispsfn = gdatmodi.thispsfnintp(gdat.binsangl)

        # PSF FWHM
        gdatmodi.thisfwhm = 2. * retr_psfnwdth(gdat, gdatmodi.thispsfn, 0.5)
        
        if gdat.varioaxi:
            indxoaxitemp = retr_indxoaxipnts(gdat, gdatmodi.thissampvarb[gdatmodi.thisindxsamplgal[l]], gdatmodi.thissampvarb[gdatmodi.thisindxsampbgal[l]])
            fwhmtemp = gdatmodi.thisfwhm[:, :, indxoaxitemp]
        else:
            fwhmtemp = gdatmodi.thisfwhm
   
    if gdat.pixltype != 'unbd' and gdat.pntstype == 'lght':
        # number of background counts per PSF
        gdatmodi.thiscntsbackfwhm = retr_cntsbackfwhm(gdat, gdatmodi.thissampvarb[gdat.indxfixpbacp], gdatmodi.thisfwhm)
    
        # number of counts and standard deviation of each PS
        gdatmodi.thiscnts = []
        gdatmodi.thissigm = []
        for l in gdat.indxpopl:
            # temp -- zero exposure pixels will give zero counts
            indxpixltemp = retr_indxpixl(gdat, gdatmodi.thissampvarb[gdatmodi.thisindxsampbgal[l]], gdatmodi.thissampvarb[gdatmodi.thisindxsamplgal[l]])
            cntstemp = gdatmodi.thissampvarb[gdatmodi.thisindxsampspec[l]][:, :, None] * gdat.expofull[:, indxpixltemp, :] * gdat.diffener[:, None, None]
            gdatmodi.thiscnts.append(cntstemp)
            if gdat.varioaxi:
                sigmtemp = retr_sigm(gdat, cntstemp, gdatmodi.thiscntsbackfwhm, lgal=gdatmodi.thissampvarb[gdatmodi.thisindxsamplgal[l]], \
                                                                                bgal=gdatmodi.thissampvarb[gdatmodi.thisindxsampbgal[l]])
            else:
                sigmtemp = retr_sigm(gdat, cntstemp, gdatmodi.thiscntsbackfwhm)
            gdatmodi.thissigm.append(sigmtemp)
        
        # standard deviation axis
        gdatmodi.binssigm = retr_sigm(gdat, gdat.binscnts, gdatmodi.thiscntsbackfwhm)
    
    # plots
    ## brightest PS
    if sum(gdatmodi.thissampvarb[gdat.indxfixpnumbpnts]) != 0:
        plot_brgt(gdat, gdatmodi)

    ## PSF radial profile
    if gdat.pntstype == 'lght':
        plot_psfn(gdat, gdatmodi)

        if gdat.varioaxi or gdat.truevarioaxi:
            for i in gdat.indxener:
                for m in gdat.indxevtt:
                    plot_factoaxi(gdat, i, m, gdatmodi)
    
        ## PSF FWHM
        if False:
            plot_fwhm(gdat, gdatmodi)
    
    # number of background counts per PSF
    if False:
        for i in gdat.indxener:
            path = gdat.pathplot + 'cntsbackfwhmflux%d_%09d.pdf' % (i, gdatmodi.cntrswep)
            tdpy.util.plot_maps(path, sum(gdatmodi.thiscntsbackfwhm, 2)[i, :], pixltype=gdat.pixltype, indxpixlrofi=gdat.indxpixlrofi, numbpixl=gdat.numbpixlfull, \
                                                                                                minmlgal=gdat.anglfact*gdat.minmlgal, maxmlgal=gdat.anglfact*gdat.maxmlgal, \
                                                                                                minmbgal=gdat.anglfact*gdat.minmbgal, maxmbgal=gdat.anglfact*gdat.maxmbgal)

    # temp -- list may not be the ultimate solution to copy gdatmodi.thisindxpntsfull
    if gdat.calcerrr:
        temppntsflux, temppntscnts, tempmodlflux, tempmodlcnts = retr_maps(gdat, list(gdatmodi.thisindxpntsfull), copy(gdatmodi.thissampvarb), evalcirc=False)
        gdatmodi.thiserrrcnts = gdatmodi.thispntscnts - temppntscnts
        gdatmodi.thiserrr = zeros_like(gdatmodi.thiserrrcnts)
        indxcubegood = where(temppntscnts > 1e-10)
        gdatmodi.thiserrr[indxcubegood] = 100. * gdatmodi.thiserrrcnts[indxcubegood] / temppntscnts[indxcubegood]

    gdatmodi.trueindxpntsassc = []
    for l in gdat.indxpopl:
        if gdat.trueinfo:
            
            indxmodl, trueindxpntsassc = corr_catl(gdat, l, gdatmodi.thissampvarb[gdatmodi.thisindxsamplgal[l]], gdatmodi.thissampvarb[gdatmodi.thisindxsampbgal[l]], \
                                                                                                                              gdatmodi.thissampvarb[gdatmodi.thisindxsampspec[l]])
            gdatmodi.trueindxpntsassc.append(trueindxpntsassc)
            
            gdatmodi.thisspecmtch = zeros((gdat.numbener, gdat.truefixp[gdat.trueindxfixpnumbpnts[l]]))
            temp = where(indxmodl >= 0)[0]
            gdatmodi.thisspecmtch[:, temp] = gdatmodi.thissampvarb[gdatmodi.thisindxsampspec[l]][:, indxmodl[temp]]
            gdatmodi.thisspecmtch[:, trueindxpntsassc.miss] = 0.
           
            try:
                plot_scatspec(gdat, l, gdatmodi=gdatmodi)
                plot_scatspec(gdat, l, gdatmodi=gdatmodi, plotdiff=True)
            except:
                pass

        if gdatmodi.indxmodlpntscomp[l].size > 0:
            plot_histspec(gdat, l, gdatmodi=gdatmodi)
            if gdat.pntstype == 'lght' and gdat.numbener > 1:
                plot_histsind(gdat, l, gdatmodi=gdatmodi)
                plot_fluxsind(gdat, l, gdatmodi=gdatmodi)
        # temp -- restrict compfrac and other plots to indxmodlpntscomp
        if gdat.pntstype == 'lght':
            plot_histcnts(gdat, l, gdatmodi=gdatmodi)
            plot_compfrac(gdat, gdatmodi=gdatmodi)

        for i in gdat.indxener:
            for m in gdat.indxevttplot:
                plot_datacnts(gdat, l, gdatmodi, i, m)
                if gdat.pixltype == 'unbd':
                    plot_catlfram(gdat, gdatmodi, l, i, m)
                else:
                    plot_modlcnts(gdat, l, gdatmodi, i, m)
                    plot_resicnts(gdat, l, gdatmodi, i, m)
                if gdat.calcerrr:
                    plot_errrcnts(gdat, gdatmodi, i, m)

            # temp
            #plot_scatpixl(gdat, gdatmodi=gdatmodi)
            #for m in gdat.indxevtt:
            #    plot_datacnts(gdat, gdatmodi, i, m)
            #    plot_catl(gdat, gdatmodi, i, m, thiscnts)
            #    plot_modlcnts(gdat, gdatmodi, i, m)
            #    plot_resicnts(gdat, gdatmodi, i, m)

    #if gdat.numbener == 3:
    #    plot_datacnts(gdat, gdatmodi, None, None)
        
    # temp
    if gdat.pntstype == 'lght':
        if False and amax(fabs(gdatmodi.thiserrr)) > 0.1:
            raise Exception('Approximation error in calculating the PS flux map is above the tolerance level.')
    

def rjmc(gdat, gdatmodi, indxprocwork):

    # initialize the worker sampler
    listsamp = zeros((gdat.numbsamp, gdat.numbpara)) + -1.
    listsampvarb = zeros((gdat.numbsamp, gdat.numbpara)) + -1.
    listindxprop = zeros(gdat.numbswep)
    listchrototl = zeros((gdat.numbswep, gdat.numbchrototl))
    gdatmodi.listchrollik = zeros((gdat.numbswep, gdat.numbchrollik))
    listllik = zeros(gdat.numbsamp)
    listlpri = zeros(gdat.numbsamp)
    listlprinorm = zeros(gdat.numbsamp)
    listaccp = zeros(gdat.numbswep, dtype=bool)
    listindxparamodi = zeros(gdat.numbswep, dtype=int)
    listmodlcnts = zeros((gdat.numbsamp, gdat.numbpixlsave))
    listpntsfluxmean = zeros((gdat.numbsamp, gdat.numbener))
    gdatmodi.listindxpntsfull = []
    listerrr = empty((gdat.numbsamp, gdat.numbener, gdat.numbevtt))
    listerrrfrac = empty((gdat.numbsamp, gdat.numbener, gdat.numbevtt))
    listboolreje = empty(gdat.numbswep, dtype=bool)
    listdeltllik = zeros(gdat.numbswep)
    listdeltlpri = zeros(gdat.numbswep)
    listmemoresi = empty(gdat.numbsamp)
    listauxipara = []
    for l in gdat.indxpopl:
        listauxipara.append(zeros((gdat.numbswep, gdat.numbcompcolr[l])))
    listlaccfact = zeros(gdat.numbswep)
    listnumbpair = zeros((gdat.numbswep, 2))
    listjcbnfact = zeros(gdat.numbswep)
    listcombfact = zeros(gdat.numbswep)

    ## sample index
    gdatmodi.cntrswep = 0
    
    ## log-likelihood
    retr_llik(gdat, gdatmodi, init=True)
    gdatmodi.thislliktotl = sum(gdatmodi.thisllik)
    ## log-prior
    retr_lpri(gdat, gdatmodi, init=True)

    ## saved state of the sample index used for logging progress status
    gdatmodi.cntrswepsave = -1
   
    # store the initial sample as the best fit sample
    maxmllikswep = gdatmodi.thislliktotl
    maxmlposswep = gdatmodi.thislliktotl + gdatmodi.thislpritotl
    indxswepmaxmllik = -1 
    indxswepmaxmlpos = -1 
    sampvarbmaxmllik = copy(gdatmodi.thissampvarb)
    sampvarbmaxmlpos = copy(gdatmodi.thissampvarb)
   
    # proposal scale optimization
    if gdat.optiprop:
        pathvaripara = gdat.pathopti + '%s.fits' % gdat.rtag
        if os.path.isfile(pathvaripara) and gdat.loadvaripara:
            if gdat.verbtype > 0 and indxprocwork == 0:
                print 'Reading the previously computed proposal scale from %s...' % pathvaripara
            gdat.optidone = True
            varipara = pf.getdata(pathvaripara)
        else:
            if gdat.verbtype > 0 and indxprocwork == 0:
                print 'Optimizing proposal scale...'
            targpropeffi = 0.25
            gdat.factpropeffi = 1.2
            minmpropeffi = targpropeffi / gdat.factpropeffi
            maxmpropeffi = targpropeffi * gdat.factpropeffi
            # temp
            perdpropeffi = 100 * gdat.numbprop
            cntrprop = zeros(gdat.numbprop)
            cntrproptotl = zeros(gdat.numbprop)
            gdat.optidone = False
            cntroptimean = 0
    else:
        gdat.optidone = True
        if gdat.verbtype > 0 and indxprocwork == 0:
            print 'Skipping proposal scale optimization...'

    while gdatmodi.cntrswep < gdat.numbswep:
    
        timetotlinit = gdat.functime()
        
        if gdat.verbtype > 1:
            print
            print '-' * 10
            print 'Sweep %d' % gdatmodi.cntrswep

        thismakefram = (gdatmodi.cntrswep % gdat.numbswepplot == 0) and indxprocwork == int(float(gdatmodi.cntrswep) / gdat.numbswep * gdat.numbproc) \
                                                                                                                                        and gdat.makeplot and gdat.optidone
        gdatmodi.boolreje = False
    
        # choose a proposal type
        retr_thisindxprop(gdat, gdatmodi)
            
        if gdat.verbtype > 1:        
            print
            print '-----'
            print 'Proposing...'
            print

        # propose the next sample
        timeinit = gdat.functime()
        retr_prop(gdat, gdatmodi)
        timefinl = gdat.functime()
        listchrototl[gdatmodi.cntrswep, 1] = timefinl - timeinit

        # plot the current sample
        if thismakefram:
            if gdat.verbtype > 0:
                print 'Process %d is in queue for making a frame.' % indxprocwork
            if gdat.numbproc > 1:
                gdat.lock.acquire()
            if gdat.verbtype > 0:
                print 'Process %d started making a frame.' % indxprocwork
            plot_samp(gdat, gdatmodi)

            if gdat.verbtype > 0:
                print 'Process %d finished making a frame.' % indxprocwork
            if gdat.numbproc > 1:
                gdat.lock.release()
            
        # reject the sample if proposal is outside the prior
        if not gdatmodi.proptran:
            if where((gdatmodi.drmcsamp[gdatmodi.indxsampmodi, 1] < 0.) | (gdatmodi.drmcsamp[gdatmodi.indxsampmodi, 1] > 1.))[0].size > 0:
                gdatmodi.boolreje = True

        if gdatmodi.thisindxprop == gdat.indxproppsfp:
            if gdat.psfntype == 'doubking':
                if gdatmodi.nextsampvarb[gdat.indxfixppsfp[1]] >= gdatmodi.nextsampvarb[gdat.indxfixppsfp[3]]:
                    gdatmodi.boolreje = True
            elif gdat.psfntype == 'doubgaus':
                if gdatmodi.nextsampvarb[gdat.indxfixppsfp[1]] >= gdatmodi.nextsampvarb[gdat.indxfixppsfp[2]]:
                    gdatmodi.boolreje = True
            
        if not gdatmodi.boolreje:

            # evaluate the log-prior
            timeinit = gdat.functime()
            retr_lpri(gdat, gdatmodi)
            timefinl = gdat.functime()
            listchrototl[gdatmodi.cntrswep, 2] = timefinl - timeinit

            # evaluate the log-likelihood
            timeinit = gdat.functime()
            retr_llik(gdat, gdatmodi) 
            timefinl = gdat.functime()
            listchrototl[gdatmodi.cntrswep, 3] = timefinl - timeinit
   
            # evaluate the acceptance probability
            # temp
            try:
                accpprob = exp(gdatmodi.deltllik + gdatmodi.deltlpri + gdatmodi.laccfact)
            except:
                print 'accpprob'
                print accpprob

            if gdat.verbtype > 1:
                print 'deltlpri'
                print gdatmodi.deltlpri
                print 'deltllik'
                print gdatmodi.deltllik
                print 'laccfact'
                print gdatmodi.laccfact
                print
        else:
            accpprob = 0.
            gdatmodi.deltllik = 0.
            gdatmodi.deltlpri = 0.
    
        # accept the sample
        if accpprob >= rand():

            if gdat.verbtype > 1:
                print 'Accepted.'

            # update the current state
            updt_samp(gdat, gdatmodi)

            # check if the accepted sample has
            ## maximal likelihood
            llikswep = gdatmodi.deltllik + gdatmodi.thislliktotl
            if llikswep > maxmllikswep:
                maxmllikswep = llikswep
                indxswepmaxmllik = gdatmodi.cntrswep
                sampvarbmaxmllik = copy(gdatmodi.thissampvarb)
            ## maximal posterior
            lposswep = llikswep + gdatmodi.deltlpri + gdatmodi.thislpritotl
            if llikswep > maxmlposswep:
                maxmlposswep = lposswep
                indxswepmaxmlpos = gdatmodi.cntrswep
                sampvarbmaxmlpos = copy(gdatmodi.thissampvarb)
            
            # register the sample as accepted
            listaccp[gdatmodi.cntrswep] = True

        # reject the sample
        else:

            if gdat.verbtype > 1:
                print 'Rejected.'

            listaccp[gdatmodi.cntrswep] = False
        
        if gdatmodi.thisindxprop < gdat.indxpropbrth:
            listindxparamodi[gdatmodi.cntrswep] = gdatmodi.indxsampmodi

        if gdat.diagmode:
            # sanity checks
            indxsampbadd = where((gdatmodi.drmcsamp[gdat.numbpopl:, 0] > 1.) | (gdatmodi.drmcsamp[gdat.numbpopl:, 0] < 0.))[0] + 1
            if indxsampbadd.size > 0:
                print 'cntrswep'
                print gdatmodi.cntrswep
                print 'thisindxprop'
                print gdat.strgprop[gdatmodi.thisindxprop]
                print 'indxsampbadd'
                print indxsampbadd
                print 'drmcsamp'
                print gdatmodi.drmcsamp[indxsampbadd, :]
                raise Exception('Unit sample vector went outside [0,1].')
             
            if (gdatmodi.drmcsamp[gdat.indxsampunsd, 1] != 0.).any():
                show_samp(gdat, gdatmodi)
                print 'gdatmodi.drmcsamp[gdat.indxsampunsd, 1]'
                print gdatmodi.drmcsamp[gdat.indxsampunsd, 1]
                raise Exception('Unused vector elements are nonzero.')

            for l in gdat.indxpopl:
                
                # temp
                continue

                flux = gdatmodi.thissampvarb[gdatmodi.thisindxsampspec[l][gdat.indxenerfluxdist[0], :]]
                indxtemp = where((flux < gdat.minmflux) | (flux > gdat.maxmflux))[0]
                if indxtemp.size > 0:
                    print
                    print 'Spectrum of a PS went outside the prior range.'
                    print 'l'
                    print l
                    print 'minmflux'
                    print gdat.minmflux
                    print 'maxmflux'
                    print gdat.maxmflux
                    print 'indxtemp'
                    print indxtemp
                    print 'flux'
                    print flux
                    raise Exception('')

                # temp
                continue

                sind = gdatmodi.thissampvarb[gdatmodi.thisindxsampspep[l]]
                indxtemp = where((sind < gdat.minmsind) | (sind > gdat.maxmsind))[0]
                if indxtemp.size > 0:
                    print 'indxtemp'
                    print indxtemp
                    print 'sind'
                    print sind
                    print 'minmsind'
                    print gdat.minmsind
                    print 'maxmsind'
                    print gdat.maxmsind
                    print 'sind[indxtemp]'
                    print sind[indxtemp]
                    raise Exception('Color of a PS went outside the prior range.') 

        # save the sample
        if gdat.boolsave[gdatmodi.cntrswep]:
            timeinit = gdat.functime()
            listsamp[gdat.indxsampsave[gdatmodi.cntrswep], :] = gdatmodi.drmcsamp[:, 0]
            listsampvarb[gdat.indxsampsave[gdatmodi.cntrswep], :] = gdatmodi.thissampvarb
            gdatmodi.listindxpntsfull.append(deepcopy(gdatmodi.thisindxpntsfull))
            if gdat.correxpo:
                if gdat.backemis:
                    gdatmodi.thismodlflux = retr_rofi_flux(gdat, gdatmodi.thissampvarb[gdat.indxfixpbacp], gdatmodi.thispntsflux, gdat.indxcube)
                else:
                    gdatmodi.thismodlflux = gdatmodi.thispntsflux
                gdatmodi.thismodlcnts = gdatmodi.thismodlflux * gdat.expo * gdat.apix
                if gdat.enerbins:
                    gdatmodi.thismodlcnts *= gdat.diffener[:, None, None]

                listmodlcnts[gdat.indxsampsave[gdatmodi.cntrswep], :] = gdatmodi.thismodlcnts[0, gdat.indxpixlsave, 0]
                listpntsfluxmean[gdat.indxsampsave[gdatmodi.cntrswep], :] = mean(sum(gdatmodi.thispntsflux * gdat.expo, 2) / sum(gdat.expo, 2), 1)
                if gdat.calcerrr:
                    temppntsflux, temppntscnts, tempmodlflux, tempmodlcnts = retr_maps(gdat, list(gdatmodi.thisindxpntsfull), copy(gdatmodi.thissampvarb), evalcirc=False)
                    
                    gdatmodi.thispntscnts = gdatmodi.thispntsflux * gdat.expo * gdat.apix
                    if gdat.enerbins:
                        gdatmodi.thispntscnts *= gdat.diffener[:, None, None]
                    gdatmodi.thiserrrcnts = gdatmodi.thispntscnts - temppntscnts
                    gdatmodi.thiserrr = zeros_like(gdatmodi.thiserrrcnts)
                    indxcubegood = where(temppntscnts > 1e-10)
                    gdatmodi.thiserrr[indxcubegood] = 100. * gdatmodi.thiserrrcnts[indxcubegood] / temppntscnts[indxcubegood]
                    listerrr[gdat.indxsampsave[gdatmodi.cntrswep], :, :] = mean(gdatmodi.thiserrr, 1)
                    listerrrfrac[gdat.indxsampsave[gdatmodi.cntrswep], :, :] = mean(100. * gdatmodi.thiserrr / temppntscnts, 1) 
            
            listllik[gdat.indxsampsave[gdatmodi.cntrswep]] = gdatmodi.thislliktotl
            listlpri[gdat.indxsampsave[gdatmodi.cntrswep]] = sum(gdatmodi.thislpri)
            lprinorm = 0.
            for l in gdat.indxpopl:
                # temp
                ## brok terms are not complete
                ## lpri calculation is turned off
                break
                numbpnts = gdatmodi.thissampvarb[gdat.indxfixpnumbpnts[l]]
                meanpnts = gdatmodi.thissampvarb[gdat.indxfixpmeanpnts[l]]
                lpri += numbpnts * gdat.priofactlgalbgal + gdat.priofactfluxdistslop + gdat.priofactmeanpnts - log(meanpnts)
                flux = gdatmodi.thissampvarb[gdatmodi.thisindxsampspec[l][gdat.indxenerfluxdist[0], :]]
                if gdat.fluxdisttype[l] == 'powr':
                    fluxdistslop = gdatmodi.thissampvarb[gdat.indxfixpfluxdistslop[l]]
                    lpri -= log(1. + fluxdistslop**2)
                    lpri += sum(log(pdfn_flux_powr(gdat, flux, fluxdistslop)))
                if gdat.fluxdisttype[l] == 'brok':
                    fluxdistbrek = gdatmodi.thissampvarb[gdat.indxfixpfluxdistbrek[l]]
                    fluxdistsloplowr = gdatmodi.thissampvarb[gdat.indxfixpfluxdistsloplowr[l]]
                    fluxdistslopuppr = gdatmodi.thissampvarb[gdat.indxfixpfluxdistslopuppr[l]]
                    lpri += sum(log(pdfn_flux_brok(gdat, flux, fluxdistbrek, fluxdistsloplowr, fluxdistslopuppr)))
            listlprinorm[gdat.indxsampsave[gdatmodi.cntrswep]] = lprinorm
            
            if gdat.tracsamp:
                
                numbpnts = gdatmodi.thissampvarb[gdat.indxfixpnumbpnts[0]]
                diffllikdiffpara = empty(numbpnts)
                for k in range(numbpnts):
                    diffllikdiffpara[k]
                listdiffllikdiffpara.append(diffllikdiffpara)

                tranmatr = diffllikdiffpara[:, None] * listdiffllikdiffpara[gdatmodi.cntrswep-1][None, :]
                listtranmatr.append(tranmatr)

            listmemoresi[gdat.indxsampsave[gdatmodi.cntrswep]] = tdpy.util.retr_memoresi()[0]
            timefinl = gdat.functime()
            listchrototl[gdatmodi.cntrswep, 4] = timefinl - timeinit

        ## proposal type
        listindxprop[gdatmodi.cntrswep] = gdatmodi.thisindxprop
        ## others
        listboolreje[gdatmodi.cntrswep] = gdatmodi.boolreje
        if gdatmodi.thisindxprop >= gdat.indxproppsfp:
            listdeltllik[gdatmodi.cntrswep] = gdatmodi.deltllik
            listdeltlpri[gdatmodi.cntrswep] = gdatmodi.deltlpri
        if gdatmodi.thisindxprop == gdat.indxpropsplt or gdatmodi.thisindxprop == gdat.indxpropmerg and gdatmodi.thisnumbpair != 0:
            listauxipara[gdatmodi.indxpoplmodi][gdatmodi.cntrswep, :] = gdatmodi.auxipara
        if gdatmodi.thisindxprop == gdat.indxpropsplt or gdatmodi.thisindxprop == gdat.indxpropmerg:
            listnumbpair[gdatmodi.cntrswep, 0] = gdatmodi.thisnumbpair
            if not gdatmodi.boolreje:
                listnumbpair[gdatmodi.cntrswep, 1] = gdatmodi.nextnumbpair
        if (gdatmodi.thisindxprop == gdat.indxpropsplt or gdatmodi.thisindxprop == gdat.indxpropmerg) and not gdatmodi.boolreje:
            listcombfact[gdatmodi.cntrswep] = gdatmodi.combfact
            listjcbnfact[gdatmodi.cntrswep] = gdatmodi.jcbnfact
            listlaccfact[gdatmodi.cntrswep] = gdatmodi.laccfact
        
        # save the execution time for the sweep
        if not thismakefram:
            timetotlfinl = gdat.functime()
            listchrototl[gdatmodi.cntrswep, 0] = timetotlfinl - timetotlinit

        # log the progress
        if gdat.verbtype > 0:
            gdatmodi.cntrswepsave = tdpy.util.show_prog(gdatmodi.cntrswep, gdat.numbswep, gdatmodi.cntrswepsave, indxprocwork=indxprocwork, showmemo=True)

        if gdat.verbtype > 1:
            print
            print
            print
            print
            print
            print
            print
            print
            print
            print
            print
            print
        
        # update the sweep counter
        if gdat.optidone:
            gdatmodi.cntrswep += 1
        else:
        
            print 'gdatmodi.cntrswep'
            print gdatmodi.cntrswep
            print 'cntrproptotl'
            print cntrproptotl
            print 'perdpropeffi'
            print perdpropeffi
            print 
            cntrproptotl[gdatmodi.thisindxprop] += 1.
            if listaccp[gdatmodi.cntrswep]:
                cntrprop[gdatmodi.thisindxprop] += 1.
            
            if gdatmodi.cntrswep % perdpropeffi == 0 and (cntrproptotl > 0).all():
                
                thispropeffi = cntrprop / cntrproptotl
                if gdat.verbtype > 0:
                    print 'Proposal scale optimization step %d' % cntroptimean
                    print 'Current proposal efficiency'
                    print thispropeffi
                    print '%.3g +- %.3g' % (mean(thispropeffi), std(thispropeffi)) 
                if (thispropeffi[gdat.indxpropactv] > minmpropeffi).all() and (thispropeffi[gdat.indxpropactv] < maxmpropeffi).all():
                    if gdat.verbtype > 0:
                        print 'Optimized variance: '
                        print varipara
                        print 'Writing the optimized variance to %s...' % pathvaripara
                    gdat.optidone = True
                    pf.writeto(pathvaripara, varipara, clobber=True)
                else:
                    factcorr = 2**(thispropeffi / targpropeffi - 1.)
                    varipara *= factcorr
                    cntrprop[:] = 0.
                    cntrproptotl[:] = 0.
                    if gdat.verbtype > 0:
                        print 'Current sample'
                        print thissampvarb
                        print 'Correction factor'
                        print factcorr
                        print 'Current variance: '
                        print varipara
                        print
                cntroptimean += 1

    gdatmodi.listchrollik = array(gdatmodi.listchrollik)
    
    listchan = [listsamp, listsampvarb, listindxprop, listchrototl, listllik, listlpri, listaccp, listmodlcnts, gdatmodi.listindxpntsfull, listindxparamodi, \
        listauxipara, listlaccfact, listnumbpair, listjcbnfact, listcombfact, listpntsfluxmean, gdatmodi.listchrollik, listboolreje, listdeltlpri, \
        listdeltllik, listmemoresi, maxmllikswep, indxswepmaxmllik, sampvarbmaxmllik, maxmlposswep, indxswepmaxmlpos, sampvarbmaxmlpos, \
        listerrr, listerrrfrac]
    
    return listchan

