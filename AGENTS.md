<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Keep market adapters fetch-based and validate incoming candles before analysis; invalid or missing real data must degrade to UNAVAILABLE, never to mock data.
- Symbol-mode AI analysis consumes the same real OHLCV adapters as charts and includes source and last-bar time, so generated summaries cannot silently analyze demo data.
