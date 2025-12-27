# SkillCorner Physical Metrics & Column Reference

Use this reference to map user questions about physical stats to the correct SQL columns. 

**Naming Convention:**
Most metrics have three variations based on possession state:
1. `_full_all`: Total match stats (Use this by default).
2. `_full_tip`: Team In Possession (When the player's team has the ball).
3. `_full_otip`: Opponent Team In Possession (Defensive phase/Pressing).

---

## 1. Distance & Intensity Metrics

| Concept | Definition | SQL Columns (All / TIP / OTIP) |
| :--- | :--- | :--- |
| **Total Distance** | Total distance covered (meters). | `total_distance_full_all`<br>`total_distance_full_tip`<br>`total_distance_full_otip` |
| **M/min** | Meters per minute. Relative work rate intensity. | `total_metersperminute_full_all`<br>`total_metersperminute_full_tip`<br>`total_metersperminute_full_otip` |
| **Running** | Distance covered between 15 km/h and 20 km/h. | `running_distance_full_all`<br>`running_distance_full_tip`<br>`running_distance_full_otip` |
| **HSR (High Speed Running)** | Distance covered between 20 and 25 km/h. | `hsr_distance_full_all`<br>`hsr_distance_full_tip`<br>`hsr_distance_full_otip` |
| **Sprinting** | Distance covered above 25 km/h. | `sprint_distance_full_all`<br>`sprint_distance_full_tip`<br>`sprint_distance_full_otip` |
| **HI (High Intensity)** | Distance covered above 20 km/h (Sum of HSR + Sprint). | `hi_distance_full_all`<br>`hi_distance_full_tip`<br>`hi_distance_full_otip` |

## 2. Count Metrics (Discrete Efforts)

| Concept | Definition | SQL Columns (All / TIP / OTIP) |
| :--- | :--- | :--- |
| **Count HSR** | Number of efforts between 20-25 km/h. | `hsr_count_full_all`<br>`hsr_count_full_tip`<br>`hsr_count_full_otip` |
| **Count Sprint** | Number of efforts > 25 km/h. | `sprint_count_full_all`<br>`sprint_count_full_tip`<br>`sprint_count_full_otip` |
| **Count HI** | Total high intensity efforts (HSR + Sprint). | `hi_count_full_all`<br>`hi_count_full_tip`<br>`hi_count_full_otip` |
| **Med Acceleration** | Accels between 1.5 - 3 m/s². | `medaccel_count_full_all`<br>`medaccel_count_full_tip`<br>`medaccel_count_full_otip` |
| **High Acceleration** | Accels > 3 m/s². | `highaccel_count_full_all`<br>`highaccel_count_full_tip`<br>`highaccel_count_full_otip` |
| **Med Deceleration** | Decels between -1.5 and -3 m/s². | `meddecel_count_full_all`<br>`meddecel_count_full_tip`<br>`meddecel_count_full_otip` |
| **High Deceleration** | Decels < -3 m/s². | `highdecel_count_full_all`<br>`highdecel_count_full_tip`<br>`highdecel_count_full_otip` |

## 3. Peak Speed (PSV)

| Concept | Definition | SQL Columns |
| :--- | :--- | :--- |
| **PSV-99** | Peak Sprint Velocity (99th percentile). The player's top speed. | `psv99` |
| **Top 5 PSV-99** | Average of the player's top 5 matches for PSV-99. | `psv99_top5` |

## 4. Advanced Agility & Explosiveness

| Concept | Definition | SQL Columns (All / TIP / OTIP) |
| :--- | :--- | :--- |
| **Explosive Accel to HSR** | High Accel starting <9km/h reaching >20km/h. | `explacceltohsr_count_full_all`<br>`explacceltohsr_count_full_tip`<br>`explacceltohsr_count_full_otip` |
| **Explosive Accel to Sprint** | High Accel starting <9km/h reaching >25km/h. | `explacceltosprint_count_full_all`<br>`explacceltosprint_count_full_tip`<br>`explacceltosprint_count_full_otip` |
| **Time to HSR** | Time to reach HSR zone (Top 3 Avg). | `timetohsr_top3` |
| **Time to Sprint** | Time to reach Sprint zone (Top 3 Avg). | `timetosprint_top3` |

## 5. Context Columns

| Concept | SQL Columns |
| :--- | :--- |
| **Player Info** | `player_name`, `player_short_name`, `player_id`, `player_birthdate` |
| **Team Info** | `team_name`, `team_id` |
| **Match Info** | `minutes_full_all` (Minutes Played), `count_match` (Matches Played) |