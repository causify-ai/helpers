// Color definitions
#let darkgreen = rgb("008000")
#let violet = rgb("ee82ee")
#let cyan = rgb("00ffff")
#let teal = rgb("008080")

// Vector / matrix notation
// Use in math mode: $#vv(A)$ for vector A
#let vv(x) = $bold(underline(#x))$
#let mat(x) = $bold(underline(underline(#x)))$

#let eqspace = h(10mm)
#let norm(x) = $||#x||$

// Vector shortcuts (v* for vectors)
#let vA = $bold(underline(A))$
#let vB = $bold(underline(B))$
#let vC = $bold(underline(C))$
#let vD = $bold(underline(D))$
#let vDelta = $bold(underline(Delta))$
#let vE = $bold(underline(E))$
#let vF = $bold(underline(F))$
#let vG = $bold(underline(G))$
#let vGamma = $bold(underline(Gamma))$
#let vH = $bold(underline(H))$
#let vI = $bold(underline(I))$
#let vJ = $bold(underline(J))$
#let vK = $bold(underline(K))$
#let vL = $bold(underline(L))$
#let vLambda = $bold(underline(Lambda))$
#let vM = $bold(underline(M))$
#let vN = $bold(underline(N))$
#let vO = $bold(underline(O))$
#let vOmega = $bold(underline(Omega))$
#let vP = $bold(underline(P))$
#let vPhi = $bold(underline(Phi))$
#let vPi = $bold(underline(Pi))$
#let vPsi = $bold(underline(Psi))$
#let vQ = $bold(underline(Q))$
#let vR = $bold(underline(R))$
#let vS = $bold(underline(S))$
#let vSigma = $bold(underline(Sigma))$
#let vT = $bold(underline(T))$
#let vU = $bold(underline(U))$
#let vUpsilon = $bold(underline(Upsilon))$
#let vV = $bold(underline(V))$
#let vW = $bold(underline(W))$
#let vX = $bold(underline(X))$
#let vXi = $bold(underline(Xi))$
#let vY = $bold(underline(Y))$
#let vZ = $bold(underline(Z))$
#let va = $bold(underline(a))$
#let valpha = $bold(underline(alpha))$
#let vb = $bold(underline(b))$
#let vbeta = $bold(underline(beta))$
#let vc = $bold(underline(c))$
#let vchi = $bold(underline(chi))$
#let vd = $bold(underline(d))$
#let vdelta = $bold(underline(delta))$
#let ve = $bold(underline(e))$
#let vepsilon = $bold(underline(epsilon))$
#let veta = $bold(underline(eta))$
#let vf = $bold(underline(f))$
#let vg = $bold(underline(g))$
#let vgamma = $bold(underline(gamma))$
#let vh = $bold(underline(h))$
#let vi = $bold(underline(i))$
#let viota = $bold(underline(iota))$
#let vj = $bold(underline(j))$
#let vk = $bold(underline(k))$
#let vkappa = $bold(underline(kappa))$
#let vl = $bold(underline(l))$
#let vlambda = $bold(underline(lambda))$
#let vm = $bold(underline(m))$
#let vmu = $bold(underline(mu))$
#let vn = $bold(underline(n))$
#let vnu = $bold(underline(nu))$
#let vo = $bold(underline(o))$
#let vomega = $bold(underline(omega))$
#let vp = $bold(underline(p))$
#let vphi = $bold(underline(phi))$
#let vpi = $bold(underline(pi))$
#let vpsi = $bold(underline(psi))$
#let vq = $bold(underline(q))$
#let vr = $bold(underline(r))$
#let vrho = $bold(underline(rho))$
#let vs = $bold(underline(s))$
#let vsigma = $bold(underline(sigma))$
#let vt = $bold(underline(t))$
#let vtau = $bold(underline(tau))$
#let vtheta = $bold(underline(theta))$
#let vu = $bold(underline(u))$
#let vupsilon = $bold(underline(upsilon))$
#let vvarepsilon = $bold(underline(epsilon))$
#let vvarphi = $bold(underline(phi))$
#let vvarrho = $bold(underline(rho))$
#let vvartheta = $bold(underline(theta))$
#let vvv = $bold(underline(v))$
#let vw = $bold(underline(w))$
#let vx = $bold(underline(x))$
#let vxi = $bold(underline(xi))$
#let vy = $bold(underline(y))$
#let vz = $bold(underline(z))$
#let vzeta = $bold(underline(zeta))$

// Matrix shortcuts (m* for matrices)
#let mA = $bold(underline(underline(A)))$
#let mB = $bold(underline(underline(B)))$
#let mC = $bold(underline(underline(C)))$
#let mD = $bold(underline(underline(D)))$
#let mDelta = $bold(underline(underline(Delta)))$
#let mE = $bold(underline(underline(E)))$
#let mF = $bold(underline(underline(F)))$
#let mG = $bold(underline(underline(G)))$
#let mGamma = $bold(underline(underline(Gamma)))$
#let mH = $bold(underline(underline(H)))$
#let mI = $bold(underline(underline(I)))$
#let mJ = $bold(underline(underline(J)))$
#let mK = $bold(underline(underline(K)))$
#let mL = $bold(underline(underline(L)))$
#let mLambda = $bold(underline(underline(Lambda)))$
#let mM = $bold(underline(underline(M)))$
#let mN = $bold(underline(underline(N)))$
#let mO = $bold(underline(underline(O)))$
#let mOmega = $bold(underline(underline(Omega)))$
#let mP = $bold(underline(underline(P)))$
#let mPi = $bold(underline(underline(Pi)))$
#let mPsi = $bold(underline(underline(Psi)))$
#let mQ = $bold(underline(underline(Q)))$
#let mR = $bold(underline(underline(R)))$
#let mS = $bold(underline(underline(S)))$
#let mSigma = $bold(underline(underline(Sigma)))$
#let mT = $bold(underline(underline(T)))$
#let mU = $bold(underline(underline(U)))$
#let mUpsilon = $bold(underline(underline(Upsilon)))$
#let mV = $bold(underline(underline(V)))$
#let mW = $bold(underline(underline(W)))$
#let mX = $bold(underline(underline(X)))$
#let mXi = $bold(underline(underline(Xi)))$
#let mY = $bold(underline(underline(Y)))$
#let mZ = $bold(underline(underline(Z)))$

// Number fields (blackboard bold)
#let bbB = $bb(B)$
#let bbC = $bb(C)$
#let bbF = $bb(F)$
#let bbL = $bb(L)$
#let bbN = $bb(N)$
#let bbQ = $bb(Q)$
#let bbR = $bb(R)$
#let bbS = $bb(S)$
#let bbZ = $bb(Z)$

// Script variables (calligraphic/mathcal)
#let cala = $cal(a)$
#let calb = $cal(b)$
#let calc = $cal(c)$
#let cald = $cal(d)$
#let cale = $cal(e)$
#let calf = $cal(f)$
#let calg = $cal(g)$
#let calh = $cal(h)$
#let cali = $cal(i)$
#let calj = $cal(j)$
#let calk = $cal(k)$
#let call = $cal(l)$
#let calm = $cal(m)$
#let caln = $cal(n)$
#let calo = $cal(o)$
#let calp = $cal(p)$
#let calq = $cal(q)$
#let calr = $cal(r)$
#let cals = $cal(s)$
#let calt = $cal(t)$
#let calu = $cal(u)$
#let calv = $cal(v)$
#let calw = $cal(w)$
#let calx = $cal(x)$
#let caly = $cal(y)$
#let calz = $cal(z)$
#let calA = $cal(A)$
#let calB = $cal(B)$
#let calC = $cal(C)$
#let calD = $cal(D)$
#let calE = $cal(E)$
#let calF = $cal(F)$
#let calG = $cal(G)$
#let calH = $cal(H)$
#let calI = $cal(I)$
#let calJ = $cal(J)$
#let calK = $cal(K)$
#let calL = $cal(L)$
#let calM = $cal(M)$
#let calN = $cal(N)$
#let calO = $cal(O)$
#let calP = $cal(P)$
#let calQ = $cal(Q)$
#let calR = $cal(R)$
#let calS = $cal(S)$
#let calT = $cal(T)$
#let calU = $cal(U)$
#let calV = $cal(V)$
#let calW = $cal(W)$
#let calX = $cal(X)$
#let calY = $cal(Y)$
#let calZ = $cal(Z)$

// Tilde accents
#let ttau = $tilde(tau)$
#let ttt = $tilde(t)$
#let ty = $tilde(y)$

// Hat (circumflex) accents
#let hF = $hat(F)$
#let hvF = $bold(underline(hat(F)))$
#let hG = $hat(G)$
#let hvG = $bold(underline(hat(G)))$
#let hX = $hat(X)$
#let hvX = $bold(underline(hat(X)))$

// Unit vectors
#let vvvhat = $bold(underline(hat(v)))$
#let uuhat = $bold(underline(hat(u)))$
#let xxhat = $bold(underline(hat(x)))$
#let tildeAAA = $bold(underline(underline(tilde(A))))$

// Basic operators and functions
#let defeq = $triangle eq$
#let lcm = $"lcm"$

// Mean and variance
#let EE = $bb(E)$
#let VV = $bb(V)$
#let Cov = $"Cov"$
#let Corr = $"Corr"$

// Color shortcuts for slides
#let blue(content) = text(blue, content)
#let red(content) = text(red, content)

// Distributions (using sans-serif for distribution names)
#let Bernoulli = $sans("Bernoulli")$
#let Beta = $sans("Beta")$
#let Binomial = $sans("Binomial")$
#let Exponential = $sans("Exponential")$
#let LogNormal = $sans("LogNormal")$
#let N = $sans("N")$
#let Poisson = $sans("Poisson")$
#let Uniform = $sans("Uniform")$
#let WN = $sans("WN")$
#let GWN = $sans("GWN")$

// Linear algebra operations
#let Col = $sans("Col")$
#let Dim = $sans("Dim")$
#let Re = $sans("Re")$
#let Im = $sans("Im")$
#let Ker = $sans("Ker")$
#let Null = $sans("Null")$
#let Rank = $sans("Rank")$
#let Row = $sans("Row")$
#let Span = $sans("Span")$
#let Det = $sans("Det")$
#let Tr = $sans("Tr")$
#let Diag = $sans("Diag")$
#let sign = $sans("sign")$
#let argmin = $sans("argmin")$
#let argmax = $sans("argmax")$
#let mod = $sans(" mod ")$
#let min = $sans("min")$
#let max = $sans("max")$
#let avg = $sans("avg")$

// Derivative at a point: at(deriv, x) gives deriv|_x
#let at(f, x) = $#f |_(#x)$

// Logic operators (small caps)
#let NOT = $sans("NOT")$
#let OR = $sans("OR")$
#let AND = $sans("AND")$
#let XOR = $sans("XOR")$
#let IFF = $sans("IFF")$
