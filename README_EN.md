# NBA Objective Data Standard Selection Skill

## Introduction

This Skill provides a unified, objective data-driven system for evaluating NBA awards, completely excluding media narratives, reputation, and popularity. It is designed for platforms that support custom Markdown Skills (e.g., Claude, Cursor, custom GPT).

## Core Principles

- **Data-driven**: All results are based on real statistics (Basketball-Reference, NBA API, etc.)
- **Winning matters**: Team record accounts for 60% of the score for regular-season individual awards
- **Standardized**: Every player in the same season uses the same scoring model
- **Reproducible**: All formulas are public; anyone can reproduce the results from the same data

## Covered Awards

### Regular Season
- Statistical leaders: Scoring, Rebounds, Assists, Steals, Blocks (pure ranking)
- MVP (Most Valuable Player)
- DPOY (Defensive Player of the Year)
- All-NBA Teams (1st, 2nd, 3rd)
- All-Defensive Teams (1st, 2nd)
- Rookie of the Year, Most Improved Player, Sixth Man of the Year

### Postseason
- Champion
- Finals MVP
- **Postseason MVP** (entire playoffs performance – new award)
- **Championship Quality Index (CQI)** (optional, evaluates the strength of a title)

## Scoring Rules Summary

| Award | Record Weight | Data Weight | Key Metrics |
|-------|---------------|-------------|--------------|
| MVP | 60% | 40% | PER, WS/48, VORP |
| DPOY | Ignored | 100% | DBPM, DWS, Steals+Blocks |
| Finals MVP | 60% (Finals W/L) | 40% | Finals PER, WS/48 |
| Postseason MVP | 50% (Final round) | 50% | Playoffs PER, WS/48, VORP |
| CQI | Composite formula | — | Team dominance + Opponent strength + Injuries + Legacy |

## Quick Start

**Trigger phrases** (enter any of the following in the conversation):

/客观数据标准
/statStandard


Then specify your request, for example:

- `评选 2001 年全部奖项` (Evaluate all awards for 2001)
- `Postseason MVP 2023`
- `Calculate 2016 championship quality index`

The AI will automatically produce a report containing data source declarations, scoring processes, and final results.

## Data Sources

The Skill automatically attempts the following sources and cross-validates (priority high → low):

1. **Basketball-Reference** – Most complete advanced stats
2. **nba_api** – Official API, structured data
3. **balldontlie API** – Free fallback
4. Hupu / Sina – Chinese basic stats (auxiliary)

If a source is unavailable, the Skill degrades to the next one and notes confidence. Missing advanced data (e.g., early-seasons VORP) is estimated using PER + WS/48 weighting.

## Output Example

A full report includes:
- Data source declaration and consistency level
- Regular-season statistical leaders (points, rebounds, etc.)
- MVP top 5 score table
- All-NBA Teams (1st, 2nd, 3rd)
- DPOY and All-Defensive Teams
- Playoff champion, Finals MVP, Postseason MVP
- Championship Quality Index (if requested)

## FAQ

**Q: Why separate Postseason MVP from Finals MVP?**  
A: Finals MVP only considers the Finals (max 7 games), which is high variance. Postseason MVP covers the entire playoffs and better reflects total contribution.

**Q: How is the record score calculated?**  
A: For the regular season, it is linearly mapped from overall league ranking (1st → 60 points, 20th → 1 point). For the playoffs, it is based on the final round (Champion → 100, Runner‑up → 80, Conf Finals → 60, Semis → 40, First round → 20).

**Q: What if advanced stats are missing for older seasons?**  
A: The Skill automatically falls back to weighted PER + WS/48 and marks the estimate with `*`.

**Q: Can I evaluate the current ongoing season?**  
A: Yes, but data stabilizes only about one month after the season ends. Results for an unfinished season should be considered preliminary.

## File Structure
