⍝ SIR epidemiological model with primal overlay operators.
⍝ Call as: SIR (mode t x θ overlay)
⍝ x – 3-element vector (susceptible, infectious, recovered).
⍝ θ – 3-element vector (β, γ, population N).

Lower←{
    text←⍵
    mask←text∊⎕A
    text[mask]←⎕a[⎕A⍳mask/text]
    text
}

GetOverlay←{
    args←⍵
    (4≥≢args):⍬
    ⊃4↓args
}

R0←{0×⍺+0×⍵}
M0←{1+0×⍺+0×⍵}
U0←{0×⍵}

SIR←{
    args←⍵
    mode←Lower ⊃args
    t←⊃1↓args
    x←⊃2↓args
    θ←⊃3↓args
    overlay←GetOverlay args
    GetFn←{
        idx←⍺                             ⍝ zero-based position in overlay vector
        (idx<≢overlay):(1+idx)⊃overlay    ⍝ pick caller-supplied function when provided
        ⍵                                 ⍝ otherwise fall back to default
    }
    Rfn←0 GetFn R0
    Mfn←1 GetFn M0
    Ufn←2 GetFn U0

    S←x[1]
    I←x[2]
    Rc←x[3]

    beta←θ[1]
    gamma←θ[2]
    N←θ[3]

    isParam←mode≡'parammod'
    beta←beta×(isParam×(I Mfn t) + (1-isParam))

    inf←beta×S×I÷N
    rec←gamma×I

    dS←-inf
    dI←inf-rec
    dRc←rec

    isResidual←mode≡'residual'
    dS←dS + isResidual×(S Rfn t)
    dI←dI + isResidual×(I Rfn t)
    dRc←dRc + isResidual×(Rc Rfn t)

    isControl←mode≡'control'
    dI←dI + isControl×(Ufn t)

    dS,dI,dRc
}
