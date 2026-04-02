## The Core Frame: Livewire as an Organizing Intelligence Platform

The product is an **intelligence briefing system for people who fight for their communities** — the same situational awareness that lobbyists buy for $50k/year, rebuilt for organizers at a fundamentally different price point and with a fundamentally different set of questions.

Livewire today answers: **"What legislation is moving, and what does it mean?"**

The expanded platform answers a broader set of intelligence questions:

---

### The Six Intelligence Layers

**1. Legislative Intelligence** (Livewire today)
What bills are moving, where, and what do they do?

Already built. This is the foundation.

**2. Power Intelligence** (the Power Map idea, deepened)
Who are the decision-makers, what do they care about, and who influences them?

But I'd push this beyond a static relationship graph. The real value is **dynamic power analysis tied to specific fights**. For any given bill, the system should be able to assemble a briefing:

- **Who votes on this?** (Pull from Legistar's body/committee data — you already have this)
- **How have they voted on similar issues?** (Voting record pattern matching — Legistar has vote data)
- **Who's funding them?** (Campaign finance APIs are public — FEC for federal, most states have open data portals)
- **Who's lobbying on this?** (Lobbying disclosure records, again largely public)
- **Who's testified on this or related bills?** (Public comment records from Legistar)

The AI layer synthesizes this into something like: *"This bill goes before the 5-member Public Safety Committee on April 15. Martinez and Liu voted for similar measures in 2024. Thompson is the swing vote — she's received $12k from the police union this cycle but also co-sponsored the accountability resolution last year. Her chief of staff previously worked at [allied nonprofit]."*

That's the kind of briefing a professional lobbyist gets from their firm. There's no reason it can't be assembled from public data.

**3. Narrative Intelligence** (Pulse, deepened)
What are people saying, what frames are winning, and how is the discourse shifting?

I'd scope this more tightly than "monitor all social media." The highest-value version focuses on **three specific narrative arenas**:

- **Official testimony and public comment** — What are people saying *on the record* at hearings? Legistar sometimes has this. City council meeting minutes and transcripts are increasingly available. This is the most underused public dataset in organizing.
- **Local news framing** — How are local reporters covering this issue? What frame is the headline using? ("Council considers tenant protections" vs. "Controversial rent control proposal divides council" — same bill, very different signals about where the narrative is)
- **Opposition messaging** — What language are industry groups and opposition coalitions using in their official statements, op-eds, and press releases? Tracking this over time reveals their playbook.

The AI layer does frame detection and shift tracking: *"Opposition to the tenant protection bill has shifted from 'property rights' framing to 'small landlord hardship' framing over the past 3 weeks — this suggests they're targeting sympathetic moderate council members."*

**4. Pattern Intelligence** (Ripple, deepened)
What's the national landscape for this fight, and what can we learn from how it played out elsewhere?

Livewire's radar already detects bill similarity. The intelligence extension asks: **what happened next?** For any cluster of similar bills:

- **Outcome tracking** — Did similar bills pass or fail in other cities? By what margin?
- **Timeline analysis** — How long did the fight take? What was the sequence of events?
- **Amendment patterns** — How did bills get modified during the process? What compromises were made? (Legistar tracks bill versions)
- **Velocity detection** — Is this type of legislation accelerating? Are model bills being pushed by a coordinated campaign?

That last one is particularly valuable. When ALEC or other model-bill organizations push legislation, it shows up as a sudden spike of similar bills across jurisdictions. Organizers need to know: *"This 'public safety' bill that just appeared in your city was introduced in 9 other cities in the past 60 days with nearly identical language. Here's the model bill it appears to derive from, and here's what happened in the cities that voted first."*

**5. Financial Intelligence** (new layer)
Where's the money flowing, and what does it tell us?

This is the layer organizers consistently wish they had and currently assemble by hand from campaign finance websites. Public data sources:

- **Campaign contributions** — FEC, state-level APIs (e.g., California's CAL-ACCESS, Illinois Sunshine)
- **Lobbying disclosures** — Most major cities require them
- **City contracts and procurement** — Often on open data portals
- **Corporate entity registrations** — Secretary of state databases

The intelligence question isn't just "who gave money to whom" — it's **"why is this bill moving now?"** When a zoning bill appears and you can surface that the developer who benefits contributed $50k to three committee members last quarter, that's not conspiracy — it's public record, just hard to connect manually.

**6. Coalition Intelligence** (new layer)
Who else is working on this, and are there potential allies we don't know about?

This is the relational version of pattern intelligence. Instead of connecting *bills*, connect *organizations and campaigns*:

- **Testimony overlap** — Which organizations are testifying on the same bills? If three groups you've never heard of are showing up to the same housing committee hearings, they might be natural coalition partners.
- **Cross-city network mapping** — If an organization is active on similar bills in multiple cities, they're likely running a coordinated campaign. Are they an ally or opponent?
- **Shared interest detection** — "Your environmental justice coalition and this transit advocacy group have both commented on 4 of the same bills this year but aren't in contact. Introduction might be valuable."

---

### What Makes This Defensible

The moat isn't any single data source — it's the **synthesis layer**. All of this data is theoretically public. The value is:

1. **Aggregation** — pulling 15 different public data sources into one place
2. **Connection** — linking a campaign contribution to a vote to a lobbying disclosure to a bill
3. **Translation** — turning all of that into a briefing an organizer can read in 2 minutes before a meeting
4. **Timeliness** — surfacing it *when it matters*, not after the vote already happened

The existing political intelligence platforms (Quorum, FiscalNote, Plural) do this for lobbyists and government affairs teams. They charge enterprise prices and optimize for corporate use cases. Nobody is doing it for organizers.

---

### Where I'd Sequence This

If I'm thinking about what to build next on top of Livewire:

1. **Power intelligence on the bill detail page** — Start narrow. For each bill, auto-assemble a "power brief": who votes on it, their voting history on similar bills, and campaign finance connections. This extends the existing briefing feature and proves the value.

2. **Pattern intelligence with outcomes** — Extend radar to track what happened to similar bills in other cities. This is mostly a data enrichment problem on data you're already ingesting.

3. **Narrative intelligence from official records** — Start with public testimony and meeting minutes, not social media. More structured, more reliable, more actionable.

4. **Financial intelligence** — Campaign finance data integration. High value but messier data (every jurisdiction formats it differently).

5. **Coalition intelligence** — This emerges naturally once you have testimony data and cross-city patterns. It's less a feature you build than a layer that appears.

---

The pitch: **"The intelligence briefing your opponents already have — now you have it too."**
