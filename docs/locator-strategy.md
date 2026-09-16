# Locator strategy

## The constraint

The system under test is a React + Vite SPA (MUI, goober, TanStack Query,
better-auth) with zero `data-testid` attributes, and the brief is to test it
without touching its code. So every locator is inferred from what the app
happens to render.

That is a real fragility, and pretending otherwise is how suites rot. The
mitigation is containment, not cleverness.

## Rules

1. **One file.** Every locator lives in `ui/src/selectors.ts`. A test file that
   contains a selector string is a bug in the test file.
2. **Role first.** `getByRole('button', { name: /talk to me/i })` survives
   restyling, DOM restructuring and class-name churn. It only breaks when the
   accessible name changes - which is a change worth noticing anyway.
3. **Text second.** Scoped to a container, case-insensitive regex, never exact
   unless the string is genuinely fixed.
4. **Structural CSS last.** MUI emits hashed class names (`css-1q2w3e`) - these
   change on every build and must never be used. If you need a structural
   selector, anchor it to a semantic parent and leave a comment saying why.
5. **Mark confidence.** Each entry is tagged `VERIFIED` (confirmed against the
   live dev deployment, with the date) or `UNVERIFIED` (written from expected
   markup). Promote to `VERIFIED` the first time a test exercises it.

## If you ever get one PR merged

Adding `data-testid` to the agent widget shell - the panel, the status text, the
end-call control, the chat input and message list - is the single highest-value
change to the app for testability. Roughly five attributes would remove most of
the fragility in this suite. Worth asking for, but the suite does not depend on it.

## Known-brittle spots

| Locator | Risk | Mitigation |
|---|---|---|
| `talkToMe` | copy change ("Talk to me" to "Ask the agent") | regex, and it fails loudly in smoke |
| `galleryThumbs` | matches on filename pattern in the aria-label | count assertion only, never index-based |
| `voiceWidget.*` | UNVERIFIED - guessed roles | confirm on first live run, fix in one place |
