⍝ Poiseuille flow relaxation with primal overlay operators.
⍝ Call as: Poiseuille (mode t x θ overlay)
⍝ x – 1-element vector (flow Q).
⍝ θ – 4-element vector (pressure drop ΔP, viscosity μ, length L, radius r).

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

Poiseuille←{
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

    Q←x[1]
    dP←θ[1]
    mu←θ[2]
    L←θ[3]
    r←θ[4]

    isParam←mode≡'parammod'
    r←r×(isParam×(Q Mfn t) + (1-isParam))

    π←3.141592653589793
    Qss←π×(r*4)×dP÷(8×mu×L)
    k←5
    dQ←k×(Qss - Q)

    isResidual←mode≡'residual'
    dQ←dQ + isResidual×(Q Rfn t)

    isControl←mode≡'control'
    dQ←dQ + isControl×(Ufn t)

    dQ
}
