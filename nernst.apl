⍝ Nernst membrane potential relaxation with primal overlay operators.
⍝ Call as: Nernst (mode t x θ overlay)
⍝ x – 1-element vector (membrane potential E).
⍝ θ – 4-element vector (temperature T, valence z, extracellular concentration Co, intracellular concentration Ci).

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

Nernst←{
    args←⍵
    mode←Lower ⊃args
    t←⊃1↓args
    x←⊃2↓args
    θ←⊃3↓args
    overlay←GetOverlay args
    Rfn←⊃((≢overlay)≥1)/overlay,(⊂R0)
    Mfn←⊃((≢overlay)≥2)/1↓overlay,(⊂M0)
    Ufn←⊃((≢overlay)≥3)/2↓overlay,(⊂U0)

    E←x[1]
    T←θ[1]
    z←θ[2]
    Co←θ[3]
    Ci←θ[4]

    Rgas←8.314462618
    F←96485.33212

    isParam←mode≡'parammod'
    T←T×(isParam×(E Mfn t) + (1-isParam))

    EN←(Rgas×T÷(z×F))×(⍟Co-⍟Ci)
    k←10
    dE←k×(EN - E)

    isResidual←mode≡'residual'
    dE←dE + isResidual×(E Rfn t)

    isControl←mode≡'control'
    dE←dE + isControl×(Ufn t)

    dE
}
