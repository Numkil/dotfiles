# Scryfall Search Syntax Quick Reference

Use with `card-search.sh` or directly via the Scryfall API.

## Card Properties

| Syntax | Description | Example |
|--------|-------------|---------|
| `name:X` or just `X` | Card name contains X | `name:"Sol Ring"` |
| `t:X` | Type line contains X | `t:creature`, `t:legendary`, `t:artifact` |
| `o:X` | Oracle text contains X | `o:"draw a card"`, `o:destroy` |
| `c:X` | Card color (exact or operators) | `c:r` (red), `c>=ub` (at least U and B) |
| `ci:X` | Color identity | `ci:wubrg`, `ci<=rg` (within R/G) |
| `cmc=N` | Converted mana cost | `cmc=3`, `cmc<=2`, `cmc>=7` |
| `pow=N` | Power | `pow>=5`, `pow=0` |
| `tou=N` | Toughness | `tou>=4` |
| `loy=N` | Loyalty | `loy>=5` |
| `r:X` | Rarity | `r:mythic`, `r:rare`, `r:uncommon`, `r:common` |
| `set:X` | Set code | `set:cmr`, `set:mh2` |
| `keyword:X` | Has keyword | `keyword:flying`, `keyword:partner` |
| `f:X` | Legal in format | `f:commander`, `f:modern` |
| `banned:X` | Banned in format | `banned:commander` |
| `is:X` | Card categories | `is:commander`, `is:modal`, `is:spell` |

## Commander-Specific Searches

```
# Find possible commanders in specific colors
is:commander ci=bg

# Find partner commanders
keyword:partner t:legendary t:creature

# Find all cards legal in commander with specific ability
f:commander o:"whenever a creature dies"

# Find commanders by color identity (within colors)
is:commander ci<=esper    # Within Esper (WUB)

# Banned cards in commander
banned:commander

# Find cards that care about commanders
o:"commander" f:commander
```

## Boolean Operators

| Operator | Description | Example |
|----------|-------------|---------|
| (space) | AND | `t:creature t:legendary` |
| `or` | OR | `t:angel or t:demon` |
| `-` | NOT | `t:creature -t:legendary` |
| `()` | Grouping | `(t:angel or t:demon) c:w` |

## Sorting

The API supports `order=` parameter:
- `name`, `set`, `released`, `rarity`, `color`, `usd`, `eur`
- `cmc`, `power`, `toughness`, `edhrec`, `penny`, `artist`

The `card-search.sh` script defaults to `edhrec` (EDHREC popularity) sorting.
