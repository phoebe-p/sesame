from numpy import exp
import numpy as np


def get_n(sys, efn, v, sites):
    """
    Compute the electron density on the given sites.
    
    Parameters
    ----------
    sys: Builder
        The discretized system.
    efn: numpy array of floats
        Values of the electron quasi-Fermi level.
    v: numpy array of floats
        Values of the electrostatic potential.
    sites: list of integers
        The sites where the electron density should be computed.
    
    Returns
    -------
    n: numpy array
    """

    n = sys.Nc[sites] * exp(-sys.bl[sites]+efn[sites]+v[sites])
    return n

def get_p(sys, efp, v, sites):
    """
    Compute the hole density on the given sites.
    
    Parameters
    ----------
    sys: Builder
        The discretized system.
    efp: numpy array of floats
        Values of the hole quasi-Fermi level.
    v: numpy array of floats
        Values of the electrostatic potential.
    sites: list of integers
        The sites where the hole density should be computed.
    
    Returns
    -------
    p: numpy array
    """
    bl = sys.bl[sites]
    Eg = sys.Eg[sites]
    Nv = sys.Nv[sites]
    p = Nv * exp(-Eg+bl+efp[sites]-v[sites])
    return p


def get_bulk_rr(sys, n, p):
    # Compute the bulk recombination of the entire system for SRH, radiative and
    # Auger mechanisms
    ni2 = sys.ni**2
    _np = n*p
    r = (_np - ni2)/(sys.tau_h * (n+sys.n1) + sys.tau_e*(p+sys.p1))\
      + (sys.Cn * n + sys.Cp * p) * (_np - ni2)\
      + sys.B * (_np - ni2)
    return r

def get_bulk_rr_derivs(sys, n, p):
    ni2 = sys.ni**2
    _np = n*p

    defn = (_np*(sys.tau_h*(n+sys.n1) + sys.tau_e*(p+sys.p1)) - (_np-ni2)*n*sys.tau_h)\
         / (sys.tau_h*(n+sys.n1) + sys.tau_e*(p+sys.p1))**2\
         + sys.Cn * n * (2*_np - ni2) + sys.Cp * _np * p\
         + sys.B * _np

    defp = (_np*(sys.tau_h*(n+sys.n1) + sys.tau_e*(p+sys.p1)) - (_np-ni2)*p*sys.tau_e)\
         / (sys.tau_h*(n+sys.n1) + sys.tau_e*(p+sys.p1))**2\
         + sys.Cn * n * _np + sys.Cp * p * (2*_np - ni2)\
         + sys.B * _np

    dv = (_np-ni2) * (sys.tau_e*p - sys.tau_h*n) \
       / (sys.tau_h*(n+sys.n1) + sys.tau_e*(p+sys.p1))**2\
       + sys.Cn * n * (_np - ni2) - sys.Cp * p * (_np - ni2)

    return defn, defp, dv

def get_jn(sys, efn, v, sites_i, sites_ip1, dl):
    """
    Compute the electron current between sites ``site_i`` and ``sites_ip1``.
    
    Parameters
    ----------
    sys: Builder
        The discretized system.
    efn: numpy array of floats
        Values of the electron quasi-Fermi level for the entire system (as given
        by the drift diffusion Poisson solver).
    v: numpy array of floats
        Values of the electrostatic potential for the entire system (as given
        by the drift diffusion Poisson solver).
    sites_i: list of integers
        Indices of the sites the current is coming from.
    sites_ip1: list of integers
        Indices of the sites the current is going to.
    dl: numpy arrays of floats
        Lattice distances between sites ``sites_i`` and sites ``sites_ip1``.
    
    Returns
    -------
    jn: numpy array of floats
    """

    bl = sys.bl[sites_i]

    vp0 = v[sites_i]
    dv = vp0 - v[sites_ip1]
    efnp0= efn[sites_i]
    efnp1 = efn[sites_ip1]

    Nc = sys.Nc[sites_i]
    mu = sys.mu_e[sites_i]

    dv = dv + (np.abs(dv) < 1e-5)*1e-5

    jn = Nc * mu * exp(-bl) * (exp(efnp1) - exp(efnp0)) / dl * \
         dv / (-exp(-vp0)*(1 - exp(dv)))
    return jn

def get_jp(sys, efp, v, sites_i, sites_ip1, dl):
    """
    Compute the hole current between sites ``site_i`` and ``sites_ip1``.
    
    Parameters
    ----------
    sys: Builder
        The discretized system.
    efp: numpy array of floats
        Values of the hole quasi-Fermi level for the entire system (as given
        by the drift diffusion Poisson solver).
    v: numpy array of floats
        Values of the electrostatic potential for the entire system (as given
        by the drift diffusion Poisson solver).
    sites_i: list of integers
        Indices of the sites the current is coming from.
    sites_ip1: list of integers
        Indices of the sites the current is going to.
    dl: numpy arrays of floats
        Lattice distances between sites ``sites_i`` and sites ``sites_ip1``.
    
    Returns
    -------
    jp: numpy array of floats
    """

    bl = sys.bl[sites_i]

    vp0 = v[sites_i]
    dv = vp0 - v[sites_ip1]
    efpp0= efp[sites_i]
    efpp1 = efp[sites_ip1]

    Nv = sys.Nv[sites_i]
    Eg = sys.Eg[sites_i]
    mu = sys.mu_h[sites_i]

    dv = dv + (np.abs(dv) < 1e-5)*1e-5

    jp = Nv * mu * exp(-Eg + bl) * (exp(efpp1) - exp(efpp0)) / dl *\
         dv / (-exp(vp0)*(1 - exp(-dv)))

    return jp

def get_jn_derivs(sys, efn, v, sites_i, sites_ip1, dl):
    bl = sys.bl[sites_i]

    vp0 = v[sites_i]
    vp1 = v[sites_ip1]
    dv = vp0 - vp1
    efnp0= efn[sites_i]
    efnp1 = efn[sites_ip1]

    Nc = sys.Nc[sites_i]
    mu = sys.mu_e[sites_i]

    dv = dv + (np.abs(dv) < 1e-5)*1e-5

    ev0 = exp(-vp0)
    ep1 = exp(-bl+efnp1)
    ep0 = exp(-bl+efnp0)

    defn_i = 1./dl * ep0 * (-dv) / (-ev0*(1 - exp(dv)))

    defn_ip1 = -1./dl * ep1 * (-dv) / (-ev0 * (1 - exp(dv)))

    dv_i = -1./dl * (ep1 - ep0) * ev0*(1 + dv - exp(dv))\
           / (ev0**2 * (exp(dv)-1)**2)

    dv_ip1 = -1./dl * (ep1 - ep0) * exp(-vp1) * (1 - dv - exp(-dv))\
            / (exp(-2*vp1) * (1-exp(-dv))**2)

    return mu*Nc*defn_i, mu*Nc*defn_ip1, mu*Nc*dv_i, mu*Nc*dv_ip1   

def get_jp_derivs(sys, efp, v, sites_i, sites_ip1, dl):
    bl = sys.bl[sites_i]

    vp0 = v[sites_i]
    vp1 = v[sites_ip1]
    dv = vp0 - vp1
    efpp0= efp[sites_i]
    efpp1 = efp[sites_ip1]

    Nv = sys.Nv[sites_i]
    Eg = sys.Eg[sites_i]
    mu = sys.mu_h[sites_i]

    dv = dv + (np.abs(dv) < 1e-5)*1e-5

    ev0 = exp(vp0)
    ep1 = exp(bl+efpp1-Eg)
    ep0 = exp(bl+efpp0-Eg)

    defp_i = 1/dl * ep0 * (-dv) / (-ev0 * (1 - exp(-dv)))

    defp_ip1 = 1/dl * ep1 * (-dv) / (ev0 * (1 - exp(-dv)))

    dv_i = -1/dl * (ep1 - ep0) * ev0 * (1-dv - exp(-dv))\
           / (ev0**2*((exp(-dv)-1)**2))

    dv_ip1 = -1/dl * (ep1 - ep0) * exp(vp1) * (1+dv - exp(dv))\
            / (exp(2*vp1)*((1-exp(dv))**2))

    return mu*Nv*defp_i, mu*Nv*defp_ip1, mu*Nv*dv_i, mu*Nv*dv_ip1

def get_srh_rr_derivs(sys, n, p, n1, p1, tau_e, tau_h):
    ni2 = n1 * p1
    _np = n*p

    defn = (_np*(tau_h*(n+n1) + tau_e*(p+p1)) - (_np-ni2)*n*tau_h)\
         / (tau_h*(n+n1) + tau_e*(p+p1))**2
    defp = (_np*(tau_h*(n+n1) + tau_e*(p+p1)) - (_np-ni2)*p*tau_e)\
         / (tau_h*(n+n1) + tau_e*(p+p1))**2
    dv = (_np-ni2) * (tau_e*p - tau_h*n) / (tau_h*(n+n1) + tau_e*(p+p1))**2

    return defn, defp, dv
