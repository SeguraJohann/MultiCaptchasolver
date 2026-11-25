# hCaptcha: plan

Not implemented. Accuracy figures must be measured before choosing a model.

## Flow

1. Serve a minimal page with the hCaptcha widget at the client's URL (reuse `open_widget_page`).
2. Click the checkbox. If a token appears, return it.
3. Otherwise read the prompt and classify the challenge type.
4. Dispatch to a handler, submit, and repeat for each round.
5. Read the token from `textarea[name="h-captcha-response"]`.

## Design

```
solvers/hcaptcha/   solver, widget, handlers/ (one per challenge type)
vision/             VisionModel interface + registry, like transcribers/
```

The request gets a `vision` field, mirroring `transcriber`. Unsupported challenges
return a new `unsupported_challenge` error.

| Challenge | Candidate approach |
|---|---|
| Select matching images (grid) | Zero-shot CLIP/SigLIP, image against prompt |
| Click a point or area | Open-vocabulary detector or VLM |
| Drag and drop | VLM; hardest, last |

## Steps

1. Widget and state handling, tested on the hCaptcha demo.
2. Collect and label challenge samples from the demo to see which types appear.
3. Implement the grid handler and measure accuracy on those samples.
4. Decide on a local VLM (GTX 1650, 4 GB) or an external API from the results.
