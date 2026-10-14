# Conditional mass envelope

The main app now includes a mass/range chart with 1, 6, 24 and 72-hour station curves. Adjust nonzero solar-day share, scheduled check-ins, Tier 2 daily minutes and recharge deadline; Advanced battery, power and wind assumptions also apply. Click Calculate mass envelope to update. Saved plots explicitly remain the last calculation until recalculated.

Each mass reserves 4.35 kg for nonbattery equipment and allocates the remaining mass to battery within 20–75% battery share. This is a conditional envelope, not optimization of every engineering assumption. Search range is 0.5–15 statute miles per leg. Battery and energy constraints, continuous thrust and electrical power, and size/weight limits are checked. Solar uses the average-weather sizing model. No full physical feasibility is implied.

The optimistic initial envelope uses one scheduled check-in/day, one Tier 2 minute/day and 100% good solar days; anomaly and sleep reporting remain budgeted. These are positive activities, not the earlier six-mile mission's fixed schedules. A 13 lb six-hour case reaches approximately 2.34 miles per leg under default engineering assumptions. Download CSV to retain the calculated curves. The expanded regression and UI suite passed 37 tests locally.
