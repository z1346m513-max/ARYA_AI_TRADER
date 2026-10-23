# ClientTypeAll Provider

**Driver:** `client_type_all`
**URL:** `https://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx`
**Format:** CSV, row sep `;`, cols: ins_code, n_buy_count, l_buy_count, n_buy_volume, l_buy_volume, n_sell_count, l_sell_count, n_sell_volume, l_sell_volume

## Map to ShareholderFlowMetrics

- `legal_buy_share` = legal buy vol / total buy vol
- `legal_net_buy_value` = legal buy vol - legal sell vol (**volume**, not Rial)
- `individual_avg_*` = natural volume / count
- shareholder count fields empty
- `data_quality` = `partial` when found

## Config

```yaml
shareholders:
  driver: client_type_all
```

## Live test (Iran IP)

```python
from arya.providers.shareholders.client_type_all_provider import ClientTypeAllProvider
print(ClientTypeAllProvider().fetch_shareholder_flow("فولاد"))
```

## Ownership note

Built on owner request; coordinates with Z.ai shareholder track — prefer one live driver name in YAML.
