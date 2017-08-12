from scipy import misc
from collections import deque

'''
    Level 1 with patterns defined by the sign of vertex gradient: modified core algorithm of levels 1 + 2.

    Pixel comparison in 2D forms lateral and vertical derivatives: 2 matches and 2 differences per pixel. 
    They are formed on the same level because average lateral match ~ average vertical match. 
    Minimal and unique unit of 2D gradient is a vertex of rightward and downward derivatives per pixel.

    Vertex gradient is computed as an average of these two equally representative sample derivatives. 
    2D patterns are blobs of same-sign vertex gradient, of value for vP or difference for dP.
    Level 1 has 4 steps of encoding, incremental per line defined by coordinate y:

    y:   comp()    p_ array of pixels, lateral comp -> p,m,d,
    y-1: ycomp()   t_ array of tuples, vertical comp, der.comb -> 1D P,
    y-2: comp_P()  P_ array of 1D patterns, vertical comp, eval, comb -> PP ) CP
    y-3: cons_P2() P2_ array of 2D patterns, root overlap, eval, PP or CP consolidation:
'''

def comp(p_):  # comparison of consecutive pixels in a scan line forms tuples: pixel, match, difference

    t_ = []
    pri_p = p_[0]  # no d, m at x=0, lagging t_.append(t)

    for p in p_:  # compares laterally consecutive pixels, vs. for x in range(1, X)

        d = p - pri_p  # difference between consecutive pixels
        m = min(p, pri_p)  # match between consecutive pixels
        t = pri_p, d, m
        t_.append(t)
        pri_p = p

    t = pri_p, 0, 0; t_.append(t)  # last pixel is not compared
    return t_


def ycomp(t_, _t_, fd, fv, y, Y, r, a, _vP_, _dP_):

    # vertical comparison between pixels, forms vertex tuples t2: p, d, dy, m, my, separate fd, fv
    # last "_" denotes array vs. element, first "_" denotes higher-line array, pattern, or variable

    x, valt_, dalt_, vP_, dP_, term_vP_, term_dP_ = 0,[],[],[],[],[],[]  # term_P_ accumulated in ycomp
    pri_s, I, D, Dy, M, My, G, olp, e_ = 0,0,0,0,0,0,0,0,[]  # also _G: interference | redundancy?

    vP = pri_s, I, D, Dy, M, My, G, olp, e_  # _fork_, _fork_vPP_, _fork_dPP_ for comp_P: += in ycomp?
    dP = pri_s, I, D, Dy, M, My, G, olp, e_  # alt_ included at term, rdn from alt_ eval in comp_P?

    A = a * r

    for t, _t in zip(t_, _t_):  # compares vertically consecutive pixels, forms gradients

        x += 1
        p, d, m = t
        _p, _d, _m = _t

        dy = p - _p   # vertical difference between pixels, summed -> Dy
        dg = _d + dy  # gradient of difference, formed at prior-line pixel _p, -> dG: variation eval?
        fd += dg      # all shorter + current- range dg s within extended quadrant

        my = min(p, _p)   # vertical match between pixels, summed -> My
        vg = _m + my - A  # gradient of predictive value (relative match) at prior-line _p, -> vG
        fv += vg          # all shorter + current- range vg s within extended quadrant

        t2 = p, d, dy, m, my  # fd, fv -> type-specific g, _g; all are accumulated within P:

        # forms 1D slice of value pattern vP: horizontal span of same-sign vg s with associated vars:

        sv, valt_, dalt_, vP, vP_, _vP_, term_vP_ = \
        form_P(0, t2, fv, fd, valt_, dalt_, vP, vP_, _vP_, term_vP_, x, y, Y, r, A)

        # forms 1D slice of difference pattern dP: horizontal span of same-sign dg s with associated vars:

        sd, dalt_, valt_, dP, dP_, _dP_, term_dP_ = \
        form_P(1, t2, fd, fv, dalt_, valt_, dP, dP_, _dP_, term_dP_, x, y, Y, r, A)

    # line's end, last ycomp t: lateral d = 0, m = 0, inclusion per incomplete gradient?
    # vP, dP term, no initialization:

    dolp = dP[7]; dalt = len(vP_), dolp; dalt_.append(dalt)
    volp = vP[7]; valt = len(dP_), volp; valt_.append(valt)

    vP_, _vP_, term_vP_ = comp_P(valt_, vP, vP_, _vP_, term_vP_, x, y, Y, r, A)  # empty _vP_
    dP_, _dP_, term_dP_ = comp_P(dalt_, dP, dP_, _dP_, term_dP_, x, y, Y, r, A)  # empty _dP_

    return vP_, dP_, term_vP_, term_dP_  # with refs to vPPs, dPPs, vCPs, dCPs from comp_P, adjusted by cons_P2


def form_P(type, t2, g, _g, alt_, _alt_, P, P_, _P_, term_P_, x, y, Y, r, A):  # forms 1D slices of 2D patterns

    p, d, dy, m, my = t2
    pri_s, I, D, Dy, M, My, G, olp, e_ = P  # unpacked to increment or initialize vars, +_G to eval alt_P rdn?

    s = 1 if g > 0 else 0
    if s != pri_s and x > r + 2:  # P (span of same-sign gs) is terminated and compared to overlapping _Ps:

        P_, _P_, term_P_ = comp_P(alt_, P, P_, _P_, term_P_, x, y, Y, r, A)  # P_ becomes _P_ at line end
        _alt = len(P_), olp # index len(P_) and overlap of P are buffered in _P' _alt_:
        _alt_.append(_alt)
        I, D, Dy, M, My, G, olp, e_, alt_ = 0,0,0,0,0,0,0,[],[]  # initialized P and alt_

    # continued or initialized P vars are accumulated:

    olp += 1  # P overlap to concurrent alternative-type P, accumulated till either P or _P is terminated
    I += p    # p s summed within P
    D += d; Dy += dy  # lat D for vertical vP comp, + vert Dy for P2 orient adjust eval and gradient
    M += m; My += my  # lateral and vertical M for P2 orient, vs V gradient eval, V = M - 2a * W?
    G += g  # fd | fv summed to define P value, with directional resolution loss

    if type == 0:
        pri = p, g, _g  # also d, dy, m, my, for fuzzy accumulation within P-specific r?
        e_.append(pri)  # prior same-line vertex, buffered for selective inc_rng comp
    else:
        e_.append(g)  # prior same-line difference gradient, buffered for inc_der comp

    P = s, I, D, Dy, M, My, G, olp, e_

    return s, alt_, _alt_, P, P_, _P_, term_P_

    # draft below:


def comp_P(alt_, P, P_, _P_, term_P_, x, y, Y, r, A):  # same type and sign 1D slice comp, select inclusion in PP:

    # blob P2 ( vPP ( dPP: redundant composition and feedback levels, var_P form within each PP type?

    fork_, buff_ = deque(),[]  # for fork rdn eval and re-input at x < _ix
    n = 0  # index of _P for addressing selected forks Ps in discontinuous fork_
    rdn_oG, rdn_PM, rdn_PD = 0,0,0  # number of higher-value Ps in fork_ + alt Ps in alt_

    ddx = 0  # no nvar: comp till min number of levels per P, then par nvar + for dPP || vPP per PM * 2 + PD
    _ix = 0  # initial coordinate of _P displaced from _P_ by last comp_P  # 2D ee_ per P in Py_?

    s, I, D, Dy, M, My, G, e_ = P  # also alt_, fork_: doesn't need to be returned?
    ix = x - len(e_)  # len(e_) is w: P width, ix: initial coordinate of P

    while x >= _ix:  # comp while P and _P horizontal overlap

        _P = _P_.popleft(); n += 1  # _n | len(P_) - len(_P_): _P counter to sync Fork_ with _P_
        _s, _ix, _x, _I, _D, _Dy, _M, _My, _G, _r, _e_, _rdn, _alt_, _fork_, _fork_vPP_, _fork_dPP_ = _P

        if s == _s:  # 1D vars comp -> PM + PD value and vertical direction, for dim reduction to axis and contour:

            dx = x - len(e_)/2 - _x - len(_e_)/2  # -> Dx? comp(dx), ddx = Ddx / h? dS *= cos(ddx), mS /= cos(ddx)?
            mx = x - _ix; if ix > _ix: mx -= ix - _ix  # mx - a_mx -> form_P(vxP), vs. mx = -(a_dx - dx): discont?

            dw = len(e_) - len(_e_)  # -> dwP, Ddx + Dw (higher-Dim Ds) triggers adjustment of derivatives or _vars
            mw = min(len(e_), len(_e_))  # comp(S | aS(norm to assign redun)) if higher-Dim (mx+mw) vP, or default:

            # w: P width = len(e_), relative overlap: mx / w, similarity: mw?
            # ddx and dw signs correlate, dx (direction) and dw (dimension) don't

            dI = I - _I; mI = min(I, _I)  # eval of MI vs. Mh rdn at term PP | var_P, not per slice?
            dD = D - _D; mD = min(D, _D)
            dM = M - _M; mM = min(M, _M)  # no G comp: y-derivatives are incomplete. also len(alt_) comp?

            PD = ddx + dw + dI + dD + dM  # defines dPP; var_P form if PP form, term if var_P or PP term;
            PM = mx + mw + mI + mD + mM   # defines vPP; comb rep value = PM * 2 + PD?
            oG = G * mw / len(e_)  # overlap of summed gradient, or while (i > mw) _e_ -> g; oG += g?

            fork = oG, PM, PD, mx, dx, mw, dw, mI, dI, mD, dD, mM, dM, P, _P
            fork_.append(fork)

    while len(fork_) > 0:  # redundancy is assigned to weaker fork: of P2 per oG ( vPP per PM, dPP per PD

        fork = fork_.pop(); oG = fork[0]; PM = fork[2]; PD = fork[4]  # buffered till len(fork_) = 0

        for i in range(len(fork_)):  # remaining forks are reused vs. popped:

            _oG = fork_[i][0]  # criterion comp, redundancy assignment, max if rdn=0:
            if oG > _oG: fork_[i][1] += 1
            else: rdn_oG += 1

            if oG > A:  # continuity bias: blob-first, possible re-scan at cons_PP?

                _PM = fork_[i][2]
                if PM > _PM: fork_[i][3] += 1
                else: rdn_PM += 1

                _PD = fork_[i][4]
                if PD > _PD: fork_[i][5] += 1
                else: rdn_PD += 1

        # separate fork_ and alt_ rdn, total redundancy = len(stronger_fork_) + len(stronger_alt_):

        for i in range(len(alt_)):  # refs to alt_P_ per fork_P, comp of oG, PM, PD?:

            _PM = alt_[i][2]
            if PM > _PM: alt_[i][3] += 1  # alt_P' rdn_PM increment, or *= rdn coef: neg_v_Olp / w?
            else: rdn_PM += 1

        buff_.append(fork)

    fork_ = buff_

    while len(fork_) > 0:  # fork eval by form_PP, PP eval within selected P2, at least 1 else 1D bias?

        fork = fork_.pop()  # same-fork P2 ( vPP, dPP form:

        sv, valt_, dalt_, vP, vP_, _vP_, term_vP_ = \
        form_PP(0, oG, fork, fork_, _fork_, term_P_, x, y, Y, r, A)

    '''
    oG? form sP2: gs blob, rdn alt_: fb vPPs and dPPs
    
    PM? form vPP: 2D value pattern, rdn alt_: fb dPPs and adjusted P2s
    
    PD? form dPP: 2D difference pattern, rdn alt_: feedback adjusted alt_ P2s and vPPs?
    
    fork_PP.append(fork) if P2 *= rdn > A, full syntax?   term per root_: 
    
    cons_PP(P2 | vPP | dPP): eval orientation (dim reduction -> axis | contour) and consolidation?  P2 rdn fb?
    '''

    return P_, _P_ , term_P_  # interlaced term_vP_ and term_dP_? + refs to vPPs, dPPs, vCPs, dCPs?


def form_PP(crit, fork, fork_, _P_, _fork_, term_P_, n, _x, y, Y, r, A):

    # forms 2D patterns per criterion: oG | PM | PD, crit is an index?

    buff_, CP_, = deque(), deque()
    root_, Root_ = deque(), deque()  # olp fork_: same-sign higher _Ps, root_: same-sign lower Ps

    a_mx = 2; a_mw = 2; a_mI = 256; a_mD = 128; a_mM = 128  # feedback to define var_vPs (variable value patterns)
    # a_PM = a_mx + a_mw + a_mI + a_mD + a_mM  or A * n_vars, rdn accum per var_P, alt eval per vertical overlap?

    W, I2, D2, Dy2, M2, My2, G2, rdn2, alt2_, Py_ = 0, 0, 0, 0, 0, 0, 0, 0, [], []  # PP vars (pattern of patterns) per root
    WC, IC, DC, DyC, MC, MyC, GC, rdnC, altC_, PP_ = 0, 0, 0, 0, 0, 0, 0, 0, [], []  # CP vars (connected PPs) at first Fork

    oG, PM, PD, mx, dx, mw, dw, mI, dI, mD, dD, mM, dM, P, _P = fork
    s, ix, x, I, D, Dy, M, My, G, r, e_, rdn, alt_, fork_, fork_vPP_, fork_dPP_ = P

    # criterion eval, P inclusion in PP, then all connected PPs in CP, unique tracing of max_crit PPs:

    if crit > A * 5 * rdn:  # PP vars increment, else empty fork ref?

        W += len(alt_); I2 += I; D2 += D; Dy2 += Dy; M2 += M; My2 += My; G2 += G; alt2_ += alt_, Py_.append(P)
        PP = W, I2, D2, Dy2, M2, My2, G2, alt2_, Py_  # alt2_: fork_ alt_ concat, to re-compute redundancy per PP

        fork = len(_P_), PP; fork_.append(fork)  # _P index and PP per fork, possibly multiple forks per P
        root_.appendleft(n)  # index of connected P in future term_P_, to be buffered in Fork_ of CP

    if _x <= ix:  # _P and attached PP output if no horizontal overlap between _P and next P:

        PP = W, I2, D2, Dy2, M2, My2, G2, alt2_, Py_  # PP per _fork P in _fork_
        Root_ += root_  # all continuing _Ps of CP, referenced from its first root _P: CP flag per _P?

        if (len(root_) == 0 and y > r + 3) or y == Y - 1:  # no continuation per _P, term of PP

            cons_PP(PP)  # _fork PP eval for rotation, re-scan, re-comp, recursion, rdn, eval? CP vars increment:
            # separate for vPP: summed var_vs, and dPP: summed var_ds?

            WC += W; IC += I2; DC += D2; DyC += Dy2; MC += M2; MyC += My2; GC += G2; altC_ += alt2_; PP_.append(PP)

        else:
            _P = _s, _ix, _x, _w, _I, _D, _Dy, _M, _My, _G, _r, _e_, _alt_, _root_, _fork_  # PP index per fork
            # old _fork_, new _root_ (old _root_ is displaced with old _P_?)
            buff_.appendleft(_P)  # _P is re-inputted for next-P comp

        CP = WC, IC, DC, DyC, MC, MyC, GC, altC_, PP_, Root_

        if (len(Root_) == 0 and y > r + 3) or y == Y - 1:  # no continuation per CP:

            cons_PP(CP)  # eval for rotation, re-scan, cross-comp of P2_? also sum per frame?

        elif len(_P_) == last_Root_nP:  # CP_ to _P_ sync for PP inclusion and cons(CP) trigger by Fork_' last _P?

            CP_.append(CP)  # PP may include len(CP_): CP index

        Py_.append(P)  # vertical inclusion, per P per fork?

    P = s, w, I, D, Dy, M, My, G, r, e_, alt_, fork_  # each fork is new, includes P2 if unique cont:
    P_.append(P)  # _P_ = P_ for next-line comp, if no horizontal overlap between P and next _P

    _P_ += buff_  # first to pop() in _P_ for next-P comb_P()

    return P_, _P_, term_P_  # _P_ and term_P_ include _P and ref PP, fork_ is accumulated within comp_P
    

def cons_PP(P2):  # sub-level 4: eval for rotation, re-scan, re-comp, recursion, accumulation, at PP or CP term

    ''' 
    :param P2: 
    :return: 
    ''''''
    cons_P2(PP): eval of d,m adjust | _var adjust | x,y adjust if projected dS-, mS+ for min.1D Ps over max.2D

        if dw sign == ddx sign and min(dw, ddx) > a: _S /= cos (ddx)  # to angle-normalize S vars for comp

    if dw > a: div_comp (w): rw = w / _w, to width-normalize S vars for comp: 

        if rw > a: pn = I/w; dn = D/w; vn = V/w; 

            comp (_n) # or default norm for redun assign, but comp (S) if low rw?

            if d_n > a: div_comp (_n) -> r_n # or if d_n * rw > a: combined div_comp eval: ext, int co-variance?

        comp Dy and My, /=cos at PP term?  default div and overlap eval per PP? not per CP: sparse coverage?
        
    rrdn = 1 + rdn_w / len(e_)  # redundancy rate / w, -> P Sum value, orthogonal but predictive
    S = 1 if abs(D) + V + a * len(e_) > rrdn * aS else 0  # rep M = a*w, bi v!V, rdn I?
    '''

    mean_dx = 1  # fractional?
    dx = Dx / H
    if dx > a: comp(abs(dx))  # or if dxP Dx: fixed ddx cost?  comp of same-sign dx only

    vx = mean_dx - dx  # normalized compression of distance: min. cost decrease, not min. benefit?


def Le1(f):  # last "_" denotes array vs. element, first "_" denotes higher-line array, pattern, variable

    r = 1; a = 127  # feedback filters
    Y, X = f.shape  # Y: frame height, X: frame width
    fd, fv, y, _vP_, _dP_, term_vP_, term_dP_, F_ = 0,0,0,[],[],[],[],[]

    p_ = f[0, :]   # first line / row of pixels
    _t_= comp(p_)  # _t_ includes ycomp() results, with Dy, My, dG, vG initialized at 0

    for y in range(1, Y):  # y is index of new line p_

        p_ = f[y, :]
        t_ = comp(p_)  # lateral pixel comp, then vertical pixel comp:
        _vP_, _dP_, term_vP_, term_dP_ = ycomp(t_, _t_, fd, fv, y, Y, r, a, _vP_, _dP_)
        _t_ = t_

        PP_ = term_vP_, term_dP_  # PP term by comp_P, adjust by cons_P2, after P ) PP ) CP termination
        F_.append(PP_)  # line of patterns is added to frame of patterns, y = len(F_)

    return F_  # output to level 2

f = misc.face(gray=True)  # input frame of pixels
f = f.astype(int)
Le1(f)

