# Finance Plans

Date: 2026-04-23  
Project: Cerebro

## Common Inputs (Applied to Both Plans)

- Team size: 10 people
- Hardware cost cap (COGS): 3,000 EGP per unit
- Labor rate: 5 USD/hour
- FX used for planning: 1 USD = 50 EGP
- Effective labor rate: 250 EGP/hour
- Full-time workload reference: 160 hours/person/month
- Per full-time person labor cost: 40,000 EGP/month
- Hosting/compute (100 users): 10,000 EGP/month
- Rent + water + electricity: 10,000 EGP/month
- R&D baseline: 5,000 EGP/month
- One-time PC cost: 70,000 EGP
- One-time tools cost: 10,000 EGP

Note: Prices in Egypt can move quickly (FX/import/logistics), so each plan includes an operating buffer.

---

## Plan A: Commercial-Oriented (All 10 Paid Full-Time)

### Cost Structure (Monthly)

- Labor: 10 x 40,000 = 400,000 EGP
- Hosting/compute: 10,000 EGP
- Rent + utilities: 10,000 EGP
- R&D: 5,000 EGP
- Operating buffer (8% of above): 34,000 EGP

Total monthly burn:

459,000 EGP/month

### Revenue Assumptions

- Hardware selling price: 6,500 EGP/unit
- Hardware margin per unit: 6,500 - 3,000 = 3,500 EGP
- Software subscription: 300 EGP/user/month
- Donations baseline: 10,000 EGP/month

### Monthly Profit Formula

P_A = (3,500 x H) + (300 x S) + D - 459,000

Where:

- H = hardware units sold per month
- S = paying subscribers
- D = donations per month (EGP)

### Break-Even Examples

1. If S = 100 and D = 10,000:

   Required H = (459,000 - 30,000 - 10,000) / 3,500 = 120 units/month

2. If H = 80 and D = 10,000:

   Required S = (459,000 - 280,000 - 10,000) / 300 = 564 subscribers

3. If H = 120 and S = 150:

   P_A = (420,000 + 45,000 + D - 459,000) = D + 6,000

   This mix is already above break-even even before donations.

### Initial Cash Needed (Suggested)

- PC + tools: 80,000 EGP
- 3-month burn buffer: 1,377,000 EGP
- Initial inventory (50 units): 150,000 EGP

Total suggested starting capital:

1,607,000 EGP

---

## Plan B: Open-Source-Oriented (10-Person Team, Lean Compensation)

This plan keeps the team at 10, but uses a community/open-source compensation model:

- 3 core full-time paid members
- 7 contributor stipends (part-time/community)

### Cost Structure (Monthly)

- Core labor: 3 x 40,000 = 120,000 EGP
- Contributor stipends: 7 x 4,000 = 28,000 EGP
- Hosting/compute (optimized): 8,000 EGP
- Rent + utilities (hybrid/lean): 7,000 EGP
- R&D + documentation/community ops: 8,000 EGP
- Operating buffer (8%): 14,000 EGP

Total monthly burn:

185,000 EGP/month

### Revenue Assumptions

- Community hardware selling price: 4,800 EGP/unit
- Hardware margin per unit: 4,800 - 3,000 = 1,800 EGP
- Subscription (managed features/support services): 150 EGP/user/month
- Donations target baseline: 40,000 EGP/month

### Monthly Profit Formula

P_B = (1,800 x H) + (150 x S) + D - 185,000

Where:

- H = hardware units sold per month
- S = paying subscribers
- D = donations per month (EGP)

### Break-Even Examples

1. If S = 300 and D = 40,000:

   Required H = (185,000 - 45,000 - 40,000) / 1,800 = 56 units/month

2. If H = 40 and D = 40,000:

   Required S = (185,000 - 72,000 - 40,000) / 150 = 487 subscribers

3. If H = 60 and S = 300:

   Required D = 185,000 - 108,000 - 45,000 = 32,000 EGP/month

### Initial Cash Needed (Suggested)

- PC + tools: 80,000 EGP
- 3-month burn buffer: 555,000 EGP
- Initial inventory (30 units): 90,000 EGP

Total suggested starting capital:

725,000 EGP

---

## Quick Comparison

- Plan A (Commercial) gives faster scaling potential, but requires significantly higher monthly execution and capital.
- Plan B (Open-source-oriented) lowers burn substantially and is usually safer for runway in Egypt, but depends more on community growth and donations.

---

## Egypt-Specific Risk Tweaks You Should Keep

- Add 10% reserve on hardware COGS for FX/import volatility.
- Re-check subscription pricing every quarter for inflation.
- Keep at least 3 months of runway in cash.
- If all 10 members are paid full-time in either plan, monthly burn moves back near 459,000 EGP.
