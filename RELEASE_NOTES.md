# ShimStacker v0.1.0

The first public release turns a finite shim inventory and multiple target bands into a globally consistent bench plan with worst-case tolerance evidence.

Highlights:

- exact, deterministic multi-job allocation rather than one-off thickness arithmetic;
- strict decimal input and inclusive worst-case band checks;
- separate proven-infeasible and state-limit-indeterminate outcomes;
- JSON evidence, CSV pick list, printable Markdown, and script-free HTML;
- zero runtime dependencies and no network, account, or equipment access;
- verified wheel, source archive, and example-plan bundle.

Start with:

```console
python -m pip install shimstacker-0.1.0-py3-none-any.whl
shimstacker demo --output shim-report
```

ShimStacker is a calculation aid. Verify the physical assembly and follow the equipment manufacturer's procedure before operation.

