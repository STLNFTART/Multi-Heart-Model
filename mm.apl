⍝ Michaelis–Menten kinetics with primal overlay operators.
⍝ Call as: MM (mode t x θ overlay)
⍝ mode    – character vector (Residual|ParamMod|Control|TimeWarp), case-insensitive.
⍝ t       – scalar time point.
⍝ x       – 2-element vector (substrate, product).
⍝ θ       – 2-element vector (Vmax, Km).
⍝ overlay – optional vector of functions [R M U];
⍝           R and M are called dyadically (state R t, state M t),
⍝           U is called monadically (U t). Missing entries default to 0/1.

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

MM←{
    args←⍵
    mode←Lower ⊃args
    t←⊃1↓args
    x←⊃2↓args
    θ←⊃3↓args
    overlay←GetOverlay args
    Rfn←⊃((≢overlay)≥1)/overlay,(⊂R0)
    Mfn←⊃((≢overlay)≥2)/1↓overlay,(⊂M0)
    Ufn←⊃((≢overlay)≥3)/2↓overlay,(⊂U0)

    S←x[1]
    Vmax←θ[1]
    Km←θ[2]

    scale←S Mfn t
    isParam←mode≡'parammod'
    Veff←Vmax×(isParam×scale + (1-isParam))
    v←Veff×S÷Km+S

    isResidual←mode≡'residual'
    isControl←mode≡'control'
    v←v + isResidual×(S Rfn t) + isControl×(Ufn t)

    (-v),v
}
