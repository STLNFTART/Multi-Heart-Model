⍝ FitzHugh–Nagumo excitable dynamics with primal overlay operators.
⍝ Call as: FHN (mode t x θ overlay)
⍝ x – 2-element vector (membrane voltage v, recovery variable w).
⍝ θ – 3-element vector (a, b, c).

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

FHN←{
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

    v←x[1]
    w←x[2]
    a←θ[1]
    b←θ[2]
    c←θ[3]

    isParam←mode≡'parammod'
    a←a×(isParam×(v Mfn t) + (1-isParam))
    b←b×(isParam×(w Mfn t) + (1-isParam))

    dv←v - v×v×v÷3 - w
    dw←(v + a - b×w)÷c

    isResidual←mode≡'residual'
    dv←dv + isResidual×(v Rfn t)
    dw←dw + isResidual×(w Rfn t)

    isControl←mode≡'control'
    dv←dv + isControl×(Ufn t)

    dv,dw
}
