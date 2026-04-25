# Finance Plan V2

Date: 2026-04-23  
Project: Smart Glasses (Cerebro)

- Commercial-oriented path
- Open-source-oriented path

- Team size: 10
- Hardware COGS should not exceed 3,000 EGP/unit

---

## 1) Base Inputs

### Team and labor

- Team size: 10 people
- Labor rate: 5 USD/hour
- FX planning rate: 1 USD = 50 EGP
- Effective labor rate: 250 EGP/hour
- Full-time benchmark: 160 hours/person/month
- Full-time cost per person/month: 40,000 EGP

### Operating assumptions

- Hosting/compute (100 users): 10,000 EGP/month
- Rent + water + electricity: 10,000 EGP/month
- R&D baseline: 5,000 EGP/month
- One-time PC: 70,000 EGP
- One-time tools: 10,000 EGP

### Hardware constraint

- Hardware COGS cap: 3,000 EGP/unit

---

## 2) Plan A: Commercial-Oriented

## Team compensation model (recommended for launch)

- 5 full-time members
- 5 part-time/stipend members

### Monthly cost structure

- Labor = (5 x 40,000) + (5 x 8,000) = 240,000 EGP
- Hosting/compute = 10,000 EGP
- Rent + utilities = 10,000 EGP
- R&D = 5,000 EGP
- Operating reserve (10%) = 27,000 EGP

Total monthly burn (Plan A):
292,000 EGP/month

### Revenue assumptions

- Hardware selling price: 6,200 EGP/unit
- Hardware margin: 6,200 - 3,000 = 3,200 EGP/unit
- Software subscription: 300 EGP/user/month
- Donations baseline: 8,000 EGP/month

### Monthly profit formula

Profit_A = (3,200 x H) + (300 x S) + D - 292,000

Where:

- H = hardware units sold/month
- S = paying subscribers
- D = donations/month (EGP)

### Break-even snapshots

1. If S = 250 and D = 8,000:
   - Required H = (292,000 - 75,000 - 8,000) / 3,200 = 66 units/month

2. If H = 70 and D = 8,000:
   - Required S = (292,000 - 224,000 - 8,000) / 300 = 200 subscribers

3. If H = 90, S = 250, D = 8,000:
   - Profit_A = 288,000 + 75,000 + 8,000 - 292,000 = 79,000 EGP/month

### Initial capital target (Plan A)

- PC + tools = 80,000 EGP
- Initial inventory (60 units x 3,000) = 180,000 EGP
- 3-month runway (3 x 292,000) = 876,000 EGP

Total suggested startup capital (Plan A):
1,136,000 EGP

---

## 3) Plan B: Open-Source-Oriented

## Team compensation model (community-first)

- 3 full-time core members
- 7 contributor stipends

### Monthly cost structure

- Core labor = 3 x 40,000 = 120,000 EGP
- Contributor stipends = 7 x 4,000 = 28,000 EGP
- Hosting/compute (optimized) = 8,000 EGP
- Rent + utilities (lean/hybrid) = 7,000 EGP
- R&D + docs + community ops = 9,000 EGP
- Operating reserve (10%) = 17,000 EGP

Total monthly burn (Plan B):
189,000 EGP/month

### Revenue assumptions

- Community hardware selling price: 4,800 EGP/unit
- Hardware margin: 4,800 - 3,000 = 1,800 EGP/unit
- Managed subscription/support seat: 150 EGP/user/month
- Support contracts: 12,000 EGP/contract/month
- Sponsors: 10,000 EGP/sponsor/month
- Donations baseline: 35,000 to 40,000 EGP/month

### Monthly profit formula

Profit_B = (1,800 x H) + (150 x S) + (12,000 x C) + (10,000 x Sp) + D - 189,000

Where:

- H = hardware units sold/month
- S = paying managed users
- C = support contracts
- Sp = sponsors
- D = donations/month (EGP)

### Break-even snapshots

1. If S = 300, C = 2, Sp = 1, D = 35,000:
   - Required H = (189,000 - 45,000 - 24,000 - 10,000 - 35,000) / 1,800 = 42 units/month

2. If H = 35, C = 3, Sp = 1, D = 40,000:
   - Required S = (189,000 - 63,000 - 36,000 - 10,000 - 40,000) / 150 = 267 users

3. If H = 50, S = 300, C = 3, Sp = 1, D = 40,000:
   - Profit_B = 90,000 + 45,000 + 36,000 + 10,000 + 40,000 - 189,000 = 32,000 EGP/month

### Initial capital target (Plan B)

- PC + tools = 80,000 EGP
- Initial inventory (30 units x 3,000) = 90,000 EGP
- 3-month runway (3 x 189,000) = 567,000 EGP

Total suggested startup capital (Plan B):
737,000 EGP

---

## 4) Decision Guidance

Choose Plan A if:

- You can consistently sell 60 to 90 hardware units/month within 6 to 12 months.
- You can push subscription conversion early.
- You can raise a larger startup budget.

Choose Plan B if:

- You want lower burn and longer runway.
- You have realistic access to donations, sponsors, and support contracts.
- You want open-source growth first, then monetization depth.

---

## 5) Egypt-Specific Adjustments You Should Keep

- Add 10% risk reserve on hardware COGS for import/FX volatility.
- Revisit prices every quarter due to inflation pressure.
- Keep at least 3 months of cash runway at all times.
- Keep a separate maintenance reserve for device returns/warranty.

---

## 6) Stress Test (All 10 Full-Time)

If all 10 are paid full-time immediately:

- Labor alone = 400,000 EGP/month
- Total burn will likely move back above 450,000 EGP/month

Conclusion:

- Both plans become much harder to sustain at early stage.
- Use phased compensation until revenue stabilizes.

---

## 7) Editable Variables

- c_hardware = 3000
- planA_hardware_price = 6200
- planB_hardware_price = 4800
- planA_sub_price = 300
- planB_sub_price = 150
- burn_A = 292000
- burn_B = 189000

Derived:

- margin_A = planA_hardware_price - c_hardware
- margin_B = planB_hardware_price - c_hardware
- Profit_A = margin_A x H + planA_sub_price x S + D - burn_A
- Profit_B = margin_B x H + planB_sub_price x S + 12000 x C + 10000 x Sp + D - burn_B
