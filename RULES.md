# IPL 2027 Auction Prediction Game: Rule Book

## 1. The game in one paragraph

Before the IPL 2027 auction, you predict two things for each player in the auction pool: **which team buys him** and **for how much**. Once the auction starts, predictions lock. As each player is sold, you earn points for getting the team right and for getting close to the price. The highest total at the end wins.

---

## 2. Getting started

- The admin creates your account and gives you a temporary password. There is no public sign-up.
- After your first login, click your name (⚙) at the top right and **change your password**. Changing it signs you out on every other device.
- Players place predictions. Admins run the auction and do not appear on the leaderboard.

---

## 3. The two phases

| Phase | When | What you can do |
|---|---|---|
| **A. Betting open** | Before the auction | Place, edit and clear predictions. Other players' predictions are hidden. |
| **B. Auction locked** | When the admin starts the auction | No changes allowed. Everyone's predictions are revealed in the **Bet Matrix**, and the **Leaderboard** goes live. |

The admin switches between phases. Once betting locks, the server rejects every change, so finish your predictions before the auction starts.

---

## 4. Making predictions (Phase A)

### 4.1 What a prediction is

For each player you pick **one** of:

- **A team and a price in ₹ Crores** (for example, `MI · ₹6.50 Cr`). The price must be more than 0, up to 2 decimals, max ₹100 Cr.
- **UNSOLD**, if you think nobody will buy him. The price is automatically ₹0.

You don't have to predict every player, but a player you skip scores 0. The progress bar (`Completed: 14 / 20 players`) shows how many you have done.

### 4.2 Saving and editing

- Fill in the tile and click **Save**. A saved tile turns light so you can see it is done.
- To change it, click **Re-edit**, adjust it, and **Save** again. Or click **Clear** to remove the prediction.
- You can edit as often as you like until betting locks.

### 4.3 Your personal team budgets

Each team enters the auction with a fixed purse and a limited number of slots. **Your predictions must respect those limits, just like a real auction.**

| Team | Full name | Purse (₹ Cr) | Total slots | Overseas slots |
|---|---|---:|---:|---:|
| LSG | Lucknow Super Giants | 47.45 | 7 | 3 |
| KKR | Kolkata Knight Riders | 41.65 | 8 | 3 |
| SRH | Sunrisers Hyderabad | 40.15 | 7 | 3 |
| DC | Delhi Capitals | 39.50 | 9 | 4 |
| MI | Mumbai Indians | 32.60 | 9 | 2 |
| CSK | Chennai Super Kings | 28.05 | 6 | 2 |
| RR | Rajasthan Royals | 27.05 | 6 | 3 |
| PBKS | Punjab Kings | 18.60 | 6 | 2 |
| RCB | Royal Challengers Bengaluru | 14.15 | 5 | 1 |
| GT | Gujarat Titans | 8.75 | 3 | 2 |

The bar at the top of the page shows **your own** remaining budget for every team, based only on your predictions:

- **Purse left** = team purse − total of your predicted prices for that team
- **Slots left** = total slots − number of players you assigned to that team
- **Overseas left** = overseas slots − number of overseas players you assigned to that team

Overseas players count toward **both** the overseas limit and the total slot limit. For example, with LSG (7 slots, 3 overseas) you can assign at most 3 overseas players and at most 7 players in total.

### 4.4 When a prediction is rejected

A save is rejected if it would push any team below zero. The team's card turns red and you see the reason, for example:

- `Exceeds GT remaining purse of ₹3.25 Cr`
- `Cannot assign to RCB: Overseas limit (1/1) already reached`
- `Cannot assign to DC: Total slots limit (9/9) already reached`

To fix it, lower the price, choose another team, or re-edit an earlier prediction to free up purse or a slot. When you edit a player, his old prediction doesn't count against the limits.

**UNSOLD** predictions never use a team's purse or slots.

The limits are based on each team's pre-auction numbers above. They do not change during the auction.

---

## 5. During the auction (Phase B)

- The admin enters each player's official result as he is sold: **team + price**, or **UNSOLD**.
- **Bet Matrix**: every player, his official result (or `Pending`), and every participant's prediction side by side, with the points each one earned.
- **Leaderboard**: live ranking. Both pages refresh automatically every 10 seconds.
- If the admin corrects a result, all scores are recalculated automatically.

---

## 6. Scoring

A player is scored only once his official result is in. Players still `Pending` score nothing yet.

For each of your predictions, you earn **Team Points + Price Points**, for a maximum of **27** per player.

### 6.1 Team points

| Your team pick | Points |
|---|---:|
| Matches the buying team (or you said UNSOLD and he went unsold) | **12** |
| Anything else | 0 |

### 6.2 Price points

Price accuracy is measured by how far your price is from the actual price, as a share of the actual price:

```
error    = |your price − actual price| ÷ actual price
accuracy = 100% − error        (never below 0%)
```

| Accuracy | Meaning | Points |
|---|---|---:|
| 100% | Exact price | **15** |
| 90% to under 100% | Within 10% | **9** |
| 80% to under 90% | Within 20% | **4** |
| 70% to under 80% | Within 30% | **1** |
| Below 70% | More than 30% off | 0 |

Things to know:

- **Price points are scored separately from the team.** You can get the price right with the wrong team and still earn price points.
- **Guessing too high and too low are treated the same.** On a ₹10 Cr player, ₹12 Cr and ₹8 Cr are both 20% off.
- **Unsold players (actual price ₹0):** a price of ₹0 is exact (15 points). Any price above ₹0 scores 0 price points.
- Prices are compared to 2 decimal places (₹0.01 Cr).

### 6.3 Worked examples

Official result: **sold to CSK for ₹10.00 Cr**.

| Your prediction | Team | Accuracy | Price | Total |
|---|---:|---|---:|---:|
| CSK · ₹10.00 | 12 | 100% | 15 | **27** |
| CSK · ₹10.80 | 12 | 92% | 9 | **21** |
| CSK · ₹8.50 | 12 | 85% | 4 | **16** |
| CSK · ₹12.50 | 12 | 75% | 1 | **13** |
| CSK · ₹15.00 | 12 | 50% | 0 | **12** |
| MI · ₹10.00 | 0 | 100% | 15 | **15** |
| MI · ₹9.20 | 0 | 92% | 9 | **9** |
| UNSOLD | 0 | 0% | 0 | **0** |
| *(no prediction)* | | | | **0** |

Official result: **UNSOLD**.

| Your prediction | Team | Price | Total |
|---|---:|---:|---:|
| UNSOLD | 12 | 15 | **27** |
| RR · ₹2.00 | 0 | 0 | **0** |

---

## 7. Leaderboard and tie-breaks

The leaderboard shows, for each participant:

- **Total Points**
- **Exact Team Hits**: players where your team pick was right
- **Exact Price Hits**: players where your price was exact
- **Players Scored**: how many of your predictions have an official result so far

Ranking order:

1. Most **Total Points**
2. Then most **Exact Team Hits**
3. Then most **Exact Price Hits**

Participants still level on all three share the same rank.

---

## 8. Fair play

- Keep your password to yourself, and change the temporary one.
- Predictions stay hidden from everyone until betting locks, so nobody can copy you.
- The official results the admin enters are final for scoring. If you spot a mistake, tell the admin. A correction updates everyone's score instantly.

Good luck, and may your auction instincts be sharp. 🏏
