# -*- coding: utf-8 -*-
"""
    femagtools.plot
    ~~~~~~~~~~~~~~~

    Creating plots



"""
import numpy as np
import scipy.interpolate as ip
import logging
import logging.config
try:
    import matplotlib
    import matplotlib.pyplot as pl
    import matplotlib.cm as cm
    from mpl_toolkits.mplot3d import Axes3D
    matplotlibversion = matplotlib.__version__
except ImportError:   # ModuleNotFoundError:
    matplotlibversion = 0


def _create_3d_axis():
    """creates a subplot with 3d projection if one does not already exist"""
    from matplotlib.projections import get_projection_class
    from matplotlib import _pylab_helpers

    create_axis = True
    if _pylab_helpers.Gcf.get_active() is not None:
        if isinstance(pl.gca(), get_projection_class('3d')):
            create_axis = False
    if create_axis:
        pl.figure()
        pl.subplot(111, projection='3d')

        
def _plot_surface(ax, x, y, z, labels, azim=None):
    """helper function for surface plots"""
    #ax.tick_params(axis='both', which='major', pad=-3)
    if azim is not None:
        ax.azim = azim
    X, Y = np.meshgrid(x, y)
    ax.plot_surface(X, Y, np.asarray(z),
                    rstride=1, cstride=1,
                    cmap=cm.viridis, alpha=0.85,
                    vmin=np.nanmin(z), vmax=np.nanmax(z),
                    linewidth=0, antialiased=True)
#                    edgecolor=(0, 0, 0, 0))
    #ax.set_xticks(xticks)
    #ax.set_yticks(yticks)
    #ax.set_zticks(zticks)
    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])
    ax.set_title(labels[2])

    #pl.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)


def __phasor_plot(up, idq, uxdq):
    uxd = uxdq[0]/up
    uxq = uxdq[1]/up
    u1d, u1q = (uxd, 1+uxq)
    u1 = np.sqrt(u1d**2 + u1q**2)*up
    i1 = np.linalg.norm(idq)
    i1d, i1q = (idq[0]/i1, idq[1]/i1)

    hw = 0.05
    ax = pl.gca()
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])
    
    ax.set_title(
        r'$U_1$={0} V, $I_1$={1} A, $U_p$={2} V'.format(
            round(u1, 1), round(i1, 1), round(up, 1)), fontsize=14)

    ax.arrow(0, 0, 0, 1, color='k', head_width=hw,
             length_includes_head=True)
    ax.text(0.08, 0.9, r'$U_p$', fontsize=18)
    ax.arrow(0, 0, u1d, u1q, color='r', head_width=hw,
             length_includes_head=True)
    ax.text(u1d, 0.75*u1q, r'$U_1$', fontsize=18)
    ax.arrow(0, 1, uxd, 0, color='g', head_width=hw,
             length_includes_head=True)
    if abs(uxq) > 1e-3:
        ax.arrow(uxd, 1, 0, uxq, color='g', head_width=hw,
                 length_includes_head=True)
    ax.arrow(0, 0, i1d, i1q, color='b', head_width=hw,
             length_includes_head=True)
    ax.text(1.15*i1d, 0.72*i1q, r'$I_1$', fontsize=18)

    xmin, xmax = (min(0, uxd, i1d), max(0, i1d, uxd))
    ymin, ymax = (min(0, i1q, 1-uxq), max(1, i1q, 1+uxq))

    ax.set_xlim([xmin-0.1, xmax+0.1])
    ax.set_ylim([ymin-0.1, ymax+0.1])
    ax.grid(True)


def i1beta_phasor(up, i1, beta, r1, xd, xq):
    """creates a phasor plot
    up: internal voltage
    i1: current
    beta: angle i1 vs up [deg]
    r1: resistance
    xd: reactance in direct axis
    xq: reactance in quadrature axis"""

    i1d, i1q = (i1*np.sin(beta/180*np.pi), i1*np.cos(beta/180*np.pi))
    uxdq = ((r1*i1d - xq*i1q), (r1*i1q + xd*i1d))
    __phasor_plot(up, (i1d, i1q), uxdq)


def iqd_phasor(up, iqd, uqd):
    """creates a phasor plot
    up: internal voltage
    iqd: current
    uqd: terminal voltage"""

    uxdq = (uqd[1]/np.sqrt(2), (uqd[0]/np.sqrt(2)-up))
    __phasor_plot(up, (iqd[1]/np.sqrt(2), iqd[0]/np.sqrt(2)), uxdq)


def phasor(bch):
    """create phasor plot from bch"""
    f1 = bch.machine['p']*bch.dqPar['speed']
    w1 = 2*np.pi*f1
    xd = w1*bch.dqPar['ld'][1]
    xq = w1*bch.dqPar['lq'][1]
    r1 = bch.machine['r1']
    i1beta_phasor(bch.dqPar['up0'],
                  bch.dqPar['i1'][-1], bch.dqPar['beta'][1],
                  r1, xd, xq)
    

def airgap(airgap):
    """creates plot of flux density in airgap"""
    pl.title('Airgap Flux Density [T]')
    pl.plot(airgap['pos'], airgap['B'])
    pl.plot(airgap['pos'], airgap['B_fft'])
    pl.xlabel('Position/°')
    pl.grid()

    
def torque(pos, torque):
    """creates plot from torque vs position"""
    k = 20
    alpha = np.linspace(0, pos[-1],
                        k*len(torque))
    f = ip.interp1d(pos, torque, kind='cubic')
    unit = 'Nm'
    scale = 1
    if np.min(torque) < -9.9e3 or np.max(torque) > 9.9e3:
        scale = 1e-3
        unit = 'kNm'
    ax = pl.gca()
    ax.set_title('Torque / {}'.format(unit))
    ax.grid(True)
    ax.plot(pos, [scale*t for t in torque], 'go')
    ax.plot(alpha, scale*f(alpha))
    if np.min(torque) > 0 and np.max(torque) > 0:
        ax.set_ylim(bottom=0)
    elif np.min(torque) < 0 and np.max(torque) < 0:
        ax.set_ylim(top=0)


def torque_fft(order, torque):
    """plot torque harmonics"""
    unit = 'Nm'
    scale = 1
    if np.min(torque) < -9.9e3 or np.max(torque) > 9.9e3:
        scale = 1e-3
        unit = 'kNm'
    ax = pl.gca()
    ax.set_title('Torque Harmonics / {}'.format(unit))
    ax.grid(True)
    try:
        bw = 2.5E-2*max(order)
        ax.bar(order, [scale*t for t in torque], width=bw, align='center')
        ax.set_xlim(left=-bw/2)
    except ValueError:  # empty sequence
        pass


def force(title, pos, force, xlabel=''):
    """plot force vs position"""
    unit = 'N'
    scale = 1
    if min(force) < -9.9e3 or max(force) > 9.9e3:
        scale = 1e-3
        unit = 'kN'
    ax = pl.gca()
    ax.set_title('{} / {}'.format(title, unit))
    ax.grid(True)
    ax.plot(pos, [scale*f for f in force])
    if xlabel:
        ax.set_xlabel(xlabel)
    if min(force) > 0:
        ax.set_ylim(bottom=0)


def force_fft(order, force):
    """plot force harmonics"""
    unit = 'N'
    scale = 1
    if min(force) < -9.9e3 or max(force) > 9.9e3:
        scale = 1e-3
        unit = 'kN'
    ax = pl.gca()
    ax.set_title('Force Harmonics / {}'.format(unit))
    ax.grid(True)
    try:
        bw = 2.5E-2*max(order)
        ax.bar(order, [scale*t for t in force], width=bw, align='center')
        ax.set_xlim(left=-bw/2)
    except ValueError:  # empty sequence
        pass


def forcedens(title, pos, fdens):
    """plot force densities"""
    ax = pl.gca()
    ax.set_title(title)
    ax.grid(True)
        
    ax.plot(pos, [1e-3*ft for ft in fdens[0]], label='F tang')
    ax.plot(pos, [1e-3*fn for fn in fdens[1]], label='F norm')
    ax.legend()
    ax.set_xlabel('Pos / deg')
    ax.set_ylabel('Force Density / kN/m²')


def forcedens_surface(fdens):
    _create_3d_axis()
    ax = pl.gca()
    xpos = [p for p in fdens.positions[0]['X']]
    ypos = [p['position'] for p in fdens.positions]
    z = 1e-3*np.array([p['FN']
                       for p in fdens.positions])
    _plot_surface(ax, xpos, ypos, z,             
                  (u'Rotor pos/°', u'Pos/°', u'F N / kN/m²'))


def forcedens_fft(title, fdens):
    """plot force densities FFT
    Args:
      title: plot title
      fdens: force density object
    """
    ax = pl.axes(projection="3d")

    F = 1e-3*fdens.fft()
    fmin = 0.2
    num_bars = F.shape[0] + 1
    _xx, _yy = np.meshgrid(np.arange(1, num_bars),
                           np.arange(1, num_bars))
    z_size = F[F > fmin]
    x_pos, y_pos = _xx[F > fmin], _yy[F > fmin]
    z_pos = np.zeros_like(z_size)
    x_size = 2
    y_size = 2
  
    ax.bar3d(x_pos, y_pos, z_pos, x_size, y_size, z_size)
    ax.view_init(azim=120)
    ax.set_xlim(0, num_bars+1)
    ax.set_ylim(0, num_bars+1)
    ax.set_title(title)
    ax.set_xlabel('M')
    ax.set_ylabel('N')
    ax.set_zlabel('kN/m²')


def winding_flux(pos, flux):
    """plot flux vs position"""
    ax = pl.gca()
    ax.set_title('Winding Flux / Vs')
    ax.grid(True)
    for p, f in zip(pos, flux):
        ax.plot(p, f)


def winding_current(pos, current):
    """plot winding currents"""
    ax = pl.gca()
    ax.set_title('Winding Currents / A')
    ax.grid(True)
    for p, i in zip(pos, current):
        ax.plot(p, i)


def voltage(title, pos, voltage):
    """plot voltage vs. position"""
    ax = pl.gca()
    ax.set_title('{} / V'.format(title))
    ax.grid(True)
    ax.plot(pos, voltage)
    

def voltage_fft(title, order, voltage):
    """plot FFT harmonics of voltage"""
    ax = pl.gca()
    ax.set_title('{} / V'.format(title))
    ax.grid(True)
    try:
        bw = 2.5E-2*max(order)
        ax.bar(order, voltage, width=bw, align='center')
    except ValueError:  # empty sequence
        pass


def mcv_hbj(mcv, log=True):
    """plot H, B, J of mcv dict"""
    import femagtools.mcv
    MUE0 = 4e-7*np.pi
    ji = []

    csiz = len(mcv['curve'])
    ax = pl.gca()
    ax.set_title(mcv['name'])
    for k, c in enumerate(mcv['curve']):
        bh = [(bi, hi*1e-3)
              for bi, hi in zip(c['bi'],
                                c['hi'])]
        try:
            if csiz == 1 and mcv['ctype'] in (femagtools.mcv.MAGCRV,
                                              femagtools.mcv.ORIENT_CRV):
                ji = [b-MUE0*h*1e3 for b, h in bh]
        except Exception:
            pass
        bi, hi = zip(*bh)

        label = 'Flux Density'
        if csiz > 1:
            label = 'Flux Density ({0}°)'.format(mcv.mc1_angle[k])
        if log:
            ax.semilogx(hi, bi, label=label)
            if ji:
                ax.semilogx(hi, ji, label='Polarisation')
        else:
            ax.plot(hi, bi, label=label)
            if ji:
                ax.plot(hi, ji, label='Polarisation')
    ax.set_xlabel('H / kA/m')
    ax.set_ylabel('T')
    if ji or csiz > 1:
        ax.legend(loc='lower right')
    ax.grid()


def mcv_muer(mcv):
    """plot rel. permeability vs. B of mcv dict"""
    MUE0 = 4e-7*np.pi
    bi, ur = zip(*[(bx, bx/hx/MUE0)
                   for bx, hx in zip(mcv['curve'][0]['bi'],
                                     mcv['curve'][0]['hi']) if not hx == 0])
    ax = pl.gca()
    ax.plot(bi, ur)
    ax.set_xlabel('B / T')
    ax.set_title('rel. Permeability')
    ax.grid()


def mtpa(pmrel, i1max, title='', projection=''):
    """create a line or surface plot with torque and mtpa curve"""
    nsamples = 10
    i1 = np.linspace(0, i1max, nsamples)
    iopt = np.array([pmrel.mtpa(x) for x in i1]).T

    iqmax, idmax = pmrel.iqdmax(i1max)
    iqmin, idmin = pmrel.iqdmin(i1max)

    if projection == '3d':
        nsamples = 50
    else:
        if iqmin == 0:
            iqmin = 0.1*iqmax
    id = np.linspace(idmin, idmax, nsamples)
    iq = np.linspace(iqmin, iqmax, nsamples)

    torque_iqd = np.array(
        [[pmrel.torque_iqd(x, y)
          for y in id] for x in iq])
    if projection == '3d':
        idq_torque(id, iq, torque_iqd)
        ax = pl.gca()
        ax.plot(iopt[1], iopt[0], iopt[2],
                color='red', linewidth=2, label='MTPA: {0:5.0f} Nm'.format(
                    np.max(iopt[2][-1])))
    else:
        ax = pl.gca()
        ax.set_aspect('equal')
        x, y = np.meshgrid(id, iq)
        CS = ax.contour(x, y, torque_iqd, 6, colors='k')
        ax.clabel(CS, fmt='%d', inline=1)
            
        ax.set_xlabel('Id/A')
        ax.set_ylabel('Iq/A')
        ax.plot(iopt[1], iopt[0],
                color='red', linewidth=2, label='MTPA: {0:5.0f} Nm'.format(
                    np.max(iopt[2][-1])))
        ax.grid()
        
    if title:
        ax.set_title(title)
    ax.legend()


def mtpv(pmrel, u1max, i1max, title='', projection=''):
    """create a line or surface plot with voltage and mtpv curve"""
    w1 = pmrel.w2_imax_umax(i1max, u1max)
    nsamples = 20
    if projection == '3d':
        nsamples = 50
        
    iqmax, idmax = pmrel.iqdmax(i1max)
    iqmin, idmin = pmrel.iqdmin(i1max)
    id = np.linspace(idmin, idmax, nsamples)
    iq = np.linspace(iqmin, iqmax, nsamples)
    u1_iqd = np.array(
        [[np.linalg.norm(pmrel.uqd(w1, iqx, idx))/np.sqrt(2)
          for idx in id] for iqx in iq])
    u1 = np.mean(u1_iqd)
    imtpv = np.array([pmrel.mtpv(wx, u1, i1max)
                      for wx in np.linspace(w1, 20*w1, nsamples)]).T
    
    if projection == '3d':
        torque_iqd = np.array(
            [[pmrel.torque_iqd(x, y)
              for y in id] for x in iq])
        idq_torque(id, iq, torque_iqd)
        ax = pl.gca()
        ax.plot(imtpv[1], imtpv[0], imtpv[2],
                color='red', linewidth=2)
    else:
        ax = pl.gca()
        ax.set_aspect('equal')
        x, y = np.meshgrid(id, iq)
        CS = ax.contour(x, y, u1_iqd, 4, colors='b')  # linestyles='dashed')
        ax.clabel(CS, fmt='%d', inline=1)

        ax.plot(imtpv[1], imtpv[0],
                color='red', linewidth=2,
                label='MTPV: {0:5.0f} Nm'.format(np.max(imtpv[2])))
        #beta = np.arctan2(imtpv[1][0], imtpv[0][0])
        #b = np.linspace(beta, 0)
        #ax.plot(np.sqrt(2)*i1max*np.sin(b), np.sqrt(2)*i1max*np.cos(b), 'r-')
        
        ax.grid()
        ax.legend()
    ax.set_xlabel('Id/A')
    ax.set_ylabel('Iq/A')
    if title:
        ax.set_title(title)


def pmrelsim(bch, title=''):
    """creates a plot of a PM/Rel motor simulation"""
    cols = 2
    rows = 4
    if len(bch.flux['1']) > 1:
        rows += 1
    htitle = 1.5 if title else 0
    fig, ax = pl.subplots(nrows=rows, ncols=cols,
                          figsize=(10, 3*rows + htitle))
    if title:
        fig.suptitle(title, fontsize=16)

    row = 1
    pl.subplot(rows, cols, row)
    if bch.torque:
        torque(bch.torque[-1]['angle'], bch.torque[-1]['torque'])
        pl.subplot(rows, cols, row+1)
        tq = list(bch.torque_fft[-1]['torque'])
        order = list(bch.torque_fft[-1]['order'])
        if order and max(order) < 5:
            order += [15]
            tq += [0]
        torque_fft(order, tq)
        pl.subplot(rows, cols, row+2)
        force('Force Fx',
              bch.torque[-1]['angle'], bch.torque[-1]['force_x'])
        pl.subplot(rows, cols, row+3)
        force('Force Fy',
              bch.torque[-1]['angle'], bch.torque[-1]['force_y'])
        row += 3
    elif bch.linearForce:
        force('Force x', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_x'], 'Displ. / mm')
        pl.subplot(rows, cols, row+1)
        force_fft(bch.linearForce_fft[-2]['order'],
                  bch.linearForce_fft[-2]['force'])
        pl.subplot(rows, cols, row+2)
        force('Force y', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_y'], 'Displ. / mm')
        pl.subplot(rows, cols, row+3)
        force_fft(bch.linearForce_fft[-1]['order'],
                  bch.linearForce_fft[-1]['force'])
        row += 3
        
    pl.subplot(rows, cols, row+1)
    flux = [bch.flux[k][-1] for k in bch.flux]
    pos = [f['displ'] for f in flux]
    winding_flux(pos,
                 [f['flux_k'] for f in flux])
    pl.subplot(rows, cols, row+2)
    winding_current(pos,
                    [f['current_k'] for f in flux])
    pl.subplot(rows, cols, row+3)
    voltage('Internal Voltage',
            bch.flux['1'][-1]['displ'],
            bch.flux['1'][-1]['voltage_dpsi'])
    pl.subplot(rows, cols, row+4)
    voltage_fft('Internal Voltage Harmonics',
                bch.flux_fft['1'][-1]['order'],
                bch.flux_fft['1'][-1]['voltage'])
   
    if len(bch.flux['1']) > 1:
        pl.subplot(rows, cols, row+5)
        voltage('No Load Voltage',
                bch.flux['1'][0]['displ'],
                bch.flux['1'][0]['voltage_dpsi'])
        pl.subplot(rows, cols, row+6)
        voltage_fft('No Load Voltage Harmonics',
                    bch.flux_fft['1'][0]['order'],
                    bch.flux_fft['1'][0]['voltage'])

    fig.tight_layout(h_pad=3.5)
    if title:
        fig.subplots_adjust(top=0.92)


def multcal(bch, title=''):
    """creates a plot of a MULT CAL simulation"""
    cols = 2
    rows = 4
    htitle = 1.5 if title else 0
    fig, ax = pl.subplots(nrows=rows, ncols=cols,
                          figsize=(10, 3*rows + htitle))
    if title:
        fig.suptitle(title, fontsize=16)

    row = 1
    pl.subplot(rows, cols, row)
    if bch.torque:
        torque(bch.torque[-1]['angle'], bch.torque[-1]['torque'])
        pl.subplot(rows, cols, row+1)
        tq = list(bch.torque_fft[-1]['torque'])
        order = list(bch.torque_fft[-1]['order'])
        if order and max(order) < 5:
            order += [15]
            tq += [0]
        torque_fft(order, tq)
        pl.subplot(rows, cols, row+2)
        force('Force Fx',
              bch.torque[-1]['angle'], bch.torque[-1]['force_x'])
        pl.subplot(rows, cols, row+3)
        force('Force Fy',
              bch.torque[-1]['angle'], bch.torque[-1]['force_y'])
        row += 3
    elif bch.linearForce:
        force('Force x', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_x'], 'Displ. / mm')
        pl.subplot(rows, cols, row+1)
        force_fft(bch.linearForce_fft[-2]['order'],
                  bch.linearForce_fft[-2]['force'])
        pl.subplot(rows, cols, row+2)
        force('Force y', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_y'], 'Displ. / mm')
        pl.subplot(rows, cols, row+3)
        force_fft(bch.linearForce_fft[-1]['order'],
                  bch.linearForce_fft[-1]['force'])
        row += 3
        
    pl.subplot(rows, cols, row+1)
    flux = [bch.flux[k][-1] for k in bch.flux]
    pos = [f['displ'] for f in flux]
    winding_flux(pos,
                 [f['flux_k'] for f in flux])
    pl.subplot(rows, cols, row+2)
    winding_current(pos,
                    [f['current_k'] for f in flux])
    pl.subplot(rows, cols, row+3)
    voltage('Internal Voltage',
            bch.flux['1'][-1]['displ'],
            bch.flux['1'][-1]['voltage_dpsi'])
    pl.subplot(rows, cols, row+4)
    voltage_fft('Internal Voltage Harmonics',
                bch.flux_fft['1'][-1]['order'],
                bch.flux_fft['1'][-1]['voltage'])
   
    if len(bch.flux['1']) > 1:
        pl.subplot(rows, cols, row+5)
        voltage('No Load Voltage',
                bch.flux['1'][0]['displ'],
                bch.flux['1'][0]['voltage_dpsi'])
        pl.subplot(rows, cols, row+6)
        voltage_fft('No Load Voltage Harmonics',
                    bch.flux_fft['1'][0]['order'],
                    bch.flux_fft['1'][0]['voltage'])

    fig.tight_layout(h_pad=3.5)
    if title:
        fig.subplots_adjust(top=0.92)


def fasttorque(bch, title=''):
    """creates a plot of a Fast Torque simulation"""
    cols = 2
    rows = 4
    if len(bch.flux['1']) > 1:
        rows += 1
    htitle = 1.5 if title else 0
    fig, ax = pl.subplots(nrows=rows, ncols=cols,
                          figsize=(10, 3*rows + htitle))
    if title:
        fig.suptitle(title, fontsize=16)

    row = 1
    pl.subplot(rows, cols, row)
    if bch.torque:
        torque(bch.torque[-1]['angle'], bch.torque[-1]['torque'])
        pl.subplot(rows, cols, row+1)
        torque_fft(bch.torque_fft[-1]['order'], bch.torque_fft[-1]['torque'])
        pl.subplot(rows, cols, row+2)
        force('Force Fx',
              bch.torque[-1]['angle'], bch.torque[-1]['force_x'])
        pl.subplot(rows, cols, row+3)
        force('Force Fy',
              bch.torque[-1]['angle'], bch.torque[-1]['force_y'])
        row += 3
    elif bch.linearForce:
        force('Force x', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_x'], 'Displ. / mm')
        pl.subplot(rows, cols, row+1)
        force_fft(bch.linearForce_fft[-2]['order'],
                  bch.linearForce_fft[-2]['force'])
        pl.subplot(rows, cols, row+2)
        force('Force y', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_y'], 'Displ. / mm')
        pl.subplot(rows, cols, row+3)
        force_fft(bch.linearForce_fft[-1]['order'],
                  bch.linearForce_fft[-1]['force'])
        row += 3
        
    pl.subplot(rows, cols, row+1)
    flux = [bch.flux[k][-1] for k in bch.flux]
    pos = [f['displ'] for f in flux]
    winding_flux(pos,[f['flux_k'] for f in flux])
    pl.subplot(rows, cols, row+2)
    winding_current(pos, [f['current_k'] for f in flux])
    pl.subplot(rows, cols, row+3)
    voltage('Internal Voltage',
            bch.flux['1'][-1]['displ'],
            bch.flux['1'][-1]['voltage_dpsi'])
    pl.subplot(rows, cols, row+4)
    voltage_fft('Internal Voltage Harmonics',
                bch.flux_fft['1'][-1]['order'],
                bch.flux_fft['1'][-1]['voltage'])
   
    if len(bch.flux['1']) > 1:
        pl.subplot(rows, cols, row+5)
        voltage('No Load Voltage',
                bch.flux['1'][0]['displ'],
                bch.flux['1'][0]['voltage_dpsi'])
        pl.subplot(rows, cols, row+6)
        voltage_fft('No Load Voltage Harmonics',
                    bch.flux_fft['1'][0]['order'],
                    bch.flux_fft['1'][0]['voltage'])

    fig.tight_layout(h_pad=3.5)
    if title:
        fig.subplots_adjust(top=0.92)


def cogging(bch, title=''):
    """creates a cogging plot"""
    cols = 2
    rows = 3

    htitle = 1.5 if title else 0
    fig, ax = pl.subplots(nrows=rows, ncols=cols,
                          figsize=(10, 3*rows + htitle))
    if title:
        fig.suptitle(title, fontsize=16)
        
    row = 1
    pl.subplot(rows, cols, row)
    if bch.torque:
        torque(bch.torque[0]['angle'], bch.torque[0]['torque'])
        pl.subplot(rows, cols, row+1)
        if bch.torque_fft:
            torque_fft(bch.torque_fft[0]['order'], bch.torque_fft[0]['torque'])
        pl.subplot(rows, cols, row+2)
        force('Force Fx',
              bch.torque[0]['angle'], bch.torque[0]['force_x'])
        pl.subplot(rows, cols, row+3)
        force('Force Fy',
              bch.torque[0]['angle'], bch.torque[0]['force_y'])
        row += 3
    elif bch.linearForce:
        force('Force x', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_x'], 'Displ. / mm')
        pl.subplot(rows, cols, row+1)
        force_fft(bch.linearForce_fft[-2]['order'],
                  bch.linearForce_fft[-2]['force'])
        pl.subplot(rows, cols, row+2)
        force('Force y', bch.linearForce[-1]['displ'],
              bch.linearForce[-1]['force_y'], 'Displ. / mm')
        pl.subplot(rows, cols, row+3)
        force_fft(bch.linearForce_fft[-1]['order'],
                  bch.linearForce_fft[-1]['force'])
        row += 3
        
    pl.subplot(rows, cols, row+1)
    voltage('Voltage',
            bch.flux['1'][0]['displ'],
            bch.flux['1'][0]['voltage_dpsi'])
    pl.subplot(rows, cols, row+2)
    voltage_fft('Voltage Harmonics',
                bch.flux_fft['1'][0]['order'],
                bch.flux_fft['1'][0]['voltage'])

    fig.tight_layout(h_pad=2)
    if title:
        fig.subplots_adjust(top=0.92)


def transientsc(bch, title=''):
    """creates a transient short circuit plot"""
    cols = 1
    rows = 2
    htitle = 1.5 if title else 0
    fig, ax = pl.subplots(nrows=rows, ncols=cols,
                          figsize=(10, 3*rows + htitle))
    if title:
        fig.suptitle(title, fontsize=16)

    row = 1
    pl.subplot(rows, cols, row)
    ax = pl.gca()
    ax.set_title('Currents / A')
    ax.grid(True)
    for i in ('ia', 'ib', 'ic'):
        ax.plot(bch.scData['time'], bch.scData[i], label=i)
    ax.set_xlabel('Time / s')
    ax.legend()

    row = 2
    pl.subplot(rows, cols, row)
    ax = pl.gca()
    ax.set_title('Torque / Nm')
    ax.grid(True)
    ax.plot(bch.scData['time'], bch.scData['torque'])
    ax.set_xlabel('Time / s')

    fig.tight_layout(h_pad=2)
    if title:
        fig.subplots_adjust(top=0.92)


def i1beta_torque(i1, beta, torque):
    """creates a surface plot of torque vs i1, beta"""
    _create_3d_axis()
    ax = pl.gca()
    azim = 210
    if 0 < np.mean(beta) or -90 > np.mean(beta):
        azim = -60
    unit = 'Nm'
    scale = 1
    if np.min(torque) < -9.9e3 or np.max(torque) > 9.9e3:
        scale = 1e-3
        unit = 'kNm'
    _plot_surface(ax, i1, beta, scale*np.asarray(torque),
                  (u'I1/A', u'Beta/°', u'Torque/{}'.format(unit)),
                  azim=azim)


def i1beta_ld(i1, beta, ld):
    """creates a surface plot of ld vs i1, beta"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, i1, beta, np.asarray(ld)*1e3,
                  (u'I1/A', u'Beta/°', u'Ld/mH'),
                  azim=60)
    

def i1beta_lq(i1, beta, lq):
    """creates a surface plot of ld vs i1, beta"""
    _create_3d_axis()
    ax = pl.gca()
    azim = 60
    if 0 < np.mean(beta) or -90 > np.mean(beta):
        azim = -120
    _plot_surface(ax, i1, beta, np.asarray(lq)*1e3,
                  (u'I1/A', u'Beta/°', u'Lq/mH'),
                  azim=azim)


def i1beta_psim(i1, beta, psim):
    """creates a surface plot of psim vs i1, beta"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, i1, beta, psim,
                  (u'I1/A', u'Beta/°', u'Psi m/Vs'),
                  azim=60)


def i1beta_psid(i1, beta, psid):
    """creates a surface plot of psid vs i1, beta"""
    _create_3d_axis()
    ax = pl.gca()
    azim = -60
    if 0 < np.mean(beta) or -90 > np.mean(beta):
        azim = 60
    _plot_surface(ax, i1, beta, psid,
                  (u'I1/A', u'Beta/°', u'Psi d/Vs'),
                  azim=azim)


def i1beta_psiq(i1, beta, psiq):
    """creates a surface plot of psiq vs i1, beta"""
    _create_3d_axis()
    ax = pl.gca()
    azim = 210
    if 0 < np.mean(beta) or -90 > np.mean(beta):
        azim = -60
    _plot_surface(ax, i1, beta, psiq,
                  (u'I1/A', u'Beta/°', u'Psi q/Vs'),
                  azim=azim)


def idq_torque(id, iq, torque):
    """creates a surface plot of torque vs id, iq"""
    _create_3d_axis()
    ax = pl.gca()
    unit = 'Nm'
    scale = 1
    if np.min(torque) < -9.9e3 or np.max(torque) > 9.9e3:
        scale = 1e-3
        unit = 'kNm'
    _plot_surface(ax, id, iq, scale*np.asarray(torque),
                  (u'Id/A', u'Iq/A', u'Torque/{}'.format(unit)),
                  azim=-60)


def idq_psid(id, iq, psid):
    """creates a surface plot of psid vs id, iq"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, id, iq, psid,
                  (u'Id/A', u'Iq/A', u'Psi d/Vs'),
                  azim=210)


def idq_psiq(id, iq, psiq):
    """creates a surface plot of psiq vs id, iq"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, id, iq, psiq,
                  (u'Id/A', u'Iq/A', u'Psi q/Vs'),
                  azim=210)


def idq_psim(id, iq, psim):
    """creates a surface plot of psim vs. id, iq"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, id, iq, psim,
                  (u'Id/A', u'Iq/A', u'Psi m [Vs]'),
                  azim=120)
    

def idq_ld(id, iq, ld):
    """creates a surface plot of ld vs. id, iq"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, id, iq, np.asarray(ld)*1e3,
                  (u'Id/A', u'Iq/A', u'L d/mH'),
                  azim=120)
    

def idq_lq(id, iq, lq):
    """creates a surface plot of lq vs. id, iq"""
    _create_3d_axis()
    ax = pl.gca()
    _plot_surface(ax, id, iq, np.asarray(lq)*1e3,
                  (u'Id/A', u'Iq/A', u'L q/mH'),
                  azim=120)
    

def ldlq(bch):
    """creates the surface plots of a BCH reader object
    with a ld-lq identification"""
    beta = bch.ldq['beta']
    i1 = bch.ldq['i1']
    torque = bch.ldq['torque']
    ld = np.array(bch.ldq['ld'])
    lq = np.array(bch.ldq['lq'])
    psid = bch.ldq['psid']
    psiq = bch.ldq['psiq']
    psim = bch.ldq['psim']

    rows = 3
    fig = pl.figure(figsize=(10, 4*rows))
    fig.suptitle('Ld-Lq Identification {}'.format(bch.filename), fontsize=16)
    fig.add_subplot(rows, 2, 1, projection='3d')
    i1beta_torque(i1, beta, torque)

    fig.add_subplot(rows, 2, 2, projection='3d')
    i1beta_psid(i1, beta, psid)
    
    fig.add_subplot(rows, 2, 3, projection='3d')
    i1beta_psiq(i1, beta, psiq)

    fig.add_subplot(rows, 2, 4, projection='3d')
    i1beta_psim(i1, beta, psim)

    fig.add_subplot(rows, 2, 5, projection='3d')
    i1beta_ld(i1, beta, ld)

    fig.add_subplot(rows, 2, 6, projection='3d')
    i1beta_lq(i1, beta, lq)


def psidq(bch):
    """creates the surface plots of a BCH reader object
    with a psid-psiq identification"""
    id = bch.psidq['id']
    iq = bch.psidq['iq']
    torque = bch.psidq['torque']
    ld = np.array(bch.psidq_ldq['ld'])
    lq = np.array(bch.psidq_ldq['lq'])
    psim = bch.psidq_ldq['psim']
    psid = bch.psidq['psid']
    psiq = bch.psidq['psiq']

    rows = 3
    fig = pl.figure(figsize=(10, 4*rows))
    fig.suptitle('Psid-Psiq Identification {}'.format(
        bch.filename), fontsize=16)

    fig.add_subplot(rows, 2, 1, projection='3d')
    idq_torque(id, iq, torque)
    
    fig.add_subplot(rows, 2, 2, projection='3d')
    idq_psid(id, iq, psid)
    
    fig.add_subplot(rows, 2, 3, projection='3d')
    idq_psiq(id, iq, psiq)

    fig.add_subplot(rows, 2, 4, projection='3d')
    idq_psim(id, iq, psim)
    
    fig.add_subplot(rows, 2, 5, projection='3d')
    idq_ld(id, iq, ld)
    
    fig.add_subplot(rows, 2, 6, projection='3d')
    idq_lq(id, iq, lq)


def felosses(losses, coeffs, title='', log=True):
    """plot iron losses with steinmetz or jordan approximation
    Args:
      losses: dict with f, B, pfe values
      coeffs: list with steinmetz (cw, alpha, beta) or
              jordan (cw, alpha, ch, beta, gamma) coeffs
      title: title string
      log: log scale for x and y axes if True

    """
    import femagtools.losscoeffs as lc
    ax = pl.gca()

    fo = losses['fo']
    Bo = losses['Bo']
    B = pl.np.linspace(0.9*np.min(losses['B']),
                       1.1*0.9*np.max(losses['B']))
                                  
    for i, f in enumerate(losses['f']):
        pfe = [p for p in np.array(losses['pfe'])[i] if p]
        if f > 0:
            if len(coeffs) == 5:
                ax.plot(B, lc.pfe_jordan(f, B, *coeffs, fo=fo, Bo=Bo))
            elif len(coeffs) == 3:
                ax.plot(B, lc.pfe_steinmetz(f, B, *coeffs, fo=fo, Bo=Bo))
        pl.plot(losses['B'][:len(pfe)], pfe,
                marker='o', label="{} Hz".format(f))

    ax.set_title("Fe Losses/(W/kg) " + title)
    if log:
        ax.set_yscale('log')
        ax.set_xscale('log')
    ax.set_xlabel("Flux Density [T]")
    #pl.ylabel("Pfe [W/kg]")
    ax.legend()
    ax.grid(True) 


def spel(isa, with_axis=False):
    """plot super elements of I7/ISA7 model
    Args:
      isa: Isa7 object
    """
    from matplotlib.patches import Polygon
    ax = pl.gca()
    ax.set_aspect('equal')
    for se in isa.superelements:
        ax.add_patch(Polygon([n.xy
                              for nc in se.nodechains
                              for n in nc.nodes],
                             color=isa.color[se.color], lw=0))

    ax.autoscale(enable=True)
    if not with_axis:
        ax.axis('off')


def mesh(isa, with_axis=False):
    """plot mesh of I7/ISA7 model
    Args:
      isa: Isa7 object
    """
    from matplotlib.lines import Line2D
    ax = pl.gca()
    ax.set_aspect('equal')
    for el in isa.elements:
        pts = [list(i) for i in zip(*[v.xy for v in el.vertices])]
        ax.add_line(Line2D(pts[0], pts[1], color='b', ls='-', lw=0.25))

    #for nc in isa.nodechains:
    #    pts = [list(i) for i in zip(*[(n.x, n.y) for n in nc.nodes])]
    #    ax.add_line(Line2D(pts[0], pts[1], color="b", ls="-", lw=0.25, 
    #                       marker=".", ms="2", mec="None"))
    
    #for nc in isa.nodechains:
    #    if nc.nodemid is not None:
    #        plt.plot(*nc.nodemid.xy, "rx")
    
    ax.autoscale(enable=True)
    if not with_axis:
        ax.axis('off')


def main():
    import io
    import sys
    import argparse    
    from .__init__ import __version__
    from femagtools.bch import Reader
    
    argparser = argparse.ArgumentParser(
        description='Read BCH/BATCH/PLT file and create a plot')
    argparser.add_argument('filename',
                           help='name of BCH/BATCH/PLT file')
    argparser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s {}, Python {}".format(__version__, sys.version),
        help="display version information",
    )
    args = argparser.parse_args()
    if not matplotlibversion:
        sys.exit(0)
    if not args.filename:
        sys.exit(0)
    if args.filename.split('.')[-1].startswith('PLT'):
        import femagtools.forcedens
        fdens = femagtools.forcedens.read(args.filename)
        cols = 1
        rows = 2
        fig, ax = pl.subplots(nrows=rows, ncols=cols,
                              figsize=(10, 10*rows))
        title = '{}, Rotor position {}'.format(
            fdens.title, fdens.positions[0]['position'])
        pos = fdens.positions[0]['X']
        FT_FN = (fdens.positions[0]['FT'],
                 fdens.positions[0]['FN'])
        pl.subplot(rows, cols, 1)
        forcedens(title, pos, FT_FN)

        title = 'Force Density Harmonics'
        pl.subplot(rows, cols, 2)
        forcedens_fft(title, fdens)
        
        #fig.tight_layout(h_pad=3.5)
        #if title:
        #    fig.subplots_adjust(top=0.92)
        pl.show()
        return
    
    bchresults = Reader()
    with io.open(args.filename, encoding='latin1', errors='ignore') as f:
        bchresults.read(f.readlines())

    if (bchresults.type.lower().find(
            'pm-synchronous-motor simulation') >= 0 or
        bchresults.type.lower().find(
            'permanet-magnet-synchronous-motor') >= 0):
        pmrelsim(bchresults, bchresults.filename)
    elif bchresults.type.lower().find(
            'multiple calculation of forces and flux') >= 0:
        multcal(bchresults, bchresults.filename)
    elif bchresults.type.lower().find('cogging calculation') >= 0:
        cogging(bchresults, bchresults.filename)
    elif bchresults.type.lower().find('ld-lq-identification') >= 0:
        ldlq(bchresults)
    elif bchresults.type.lower().find('psid-psiq-identification') >= 0:
        psidq(bchresults)
    elif bchresults.type.lower().find('fast_torque calculation') >= 0:
        fasttorque(bchresults)
    elif bchresults.type.lower().find('transient sc') >= 0:
        transientsc(bchresults, bchresults.filename)
    else:
        raise ValueError("BCH type {} not yet supported".format(
            bchresults.type))
    pl.show()


if __name__ == "__main__":
    logger = logging.getLogger("femagtools.plot")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')
    main()
