# Luminara — marketing site

Two static pages, no build step, no dependencies. Open `index.html` in a browser
and it works; there is nothing to compile and nothing to install.

```
index.html     the page
privacy.html   the privacy policy, which App Store Connect asks for by URL
assets/        icons, copied from the app's own icon source
.nojekyll      stops GitHub running Jekyll over files it does not need to touch
robots.txt
```

## Deploying

1. Create a repository on GitHub and push this folder to `main`.
2. Settings → Pages → Source: **Deploy from a branch**, branch `main`, folder `/ (root)`.
3. The site appears at `https://<user>.github.io/<repo>/` within a minute or two.

No workflow file is needed. Pages serves a static root directly, and adding an
Actions build for two HTML files would be a pipeline that can break where there
is currently nothing that can.

### A custom domain

Add a file called `CNAME` containing the bare hostname, one line, no protocol:

```
luminara.app
```

Then point the domain's DNS at GitHub and turn on **Enforce HTTPS** in Settings
→ Pages once the certificate is issued.

## Two things to fill in before this is finished

**The sample photograph.** The hero pad grades a drawn colour field, which is
obviously a rendering rather than a photograph. Drop a real one at
`assets/sample.jpg` and it is picked up automatically: the page probes for the
file and only swaps it in if it loads, so a missing file costs nothing. Landscape,
3:2, and something with skin or sky in it so the saturation axis has something to
do. Around 1600px wide is plenty.

**The App Store link.** `index.html` has one placeholder button reading
"Coming to the Mac App Store". Swap its `href` for the product page URL once the
app is live, and change the label beside it.

## About the design

The palette is copied by value from the app's `Achromatic.swift`, names and all,
so a grey that changes there can be found here with a grep. Every colour on the
page satisfies `r == g == b`.

That is not a restriction imposed on the page, it is the app's own rule: apart
from one destructive red, Luminara's interface has no colour in it. So the only
colour a visitor sees is the photograph in the grading pad, changing as they move
across it. The page is making the product's argument by being built the same way.

Type is the system stack rather than a web font. The audience for a Mac app is on
Apple hardware, so the page renders in SF Pro and SF Mono, which is what the app
itself uses for body text and for every label and number. A downloaded font would
be an approximation of something the reader already has.

The pad's arithmetic is CSS `brightness()` and `saturate()`, not the app's grading
maths. It demonstrates the gesture. Reimplementing `Grade.apply` in JavaScript
would create a second answer to what a grade is, and the two would disagree the
first time either changed.

## Privacy policy

`privacy.html` is written from what the app and relay actually do, and it is a
draft rather than legal advice. Read it against your own understanding of the
service before you hand the URL to App Store Connect, particularly the retention
paragraph and the account deletion route, since Apple checks that one works.
